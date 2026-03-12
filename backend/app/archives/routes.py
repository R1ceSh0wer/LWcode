import os
import json
import shutil
import subprocess
import threading
import random
from flask import request, jsonify, current_app
from . import bp
from .models import ModelArchive
from ..users.models import db
from functools import wraps
from datetime import datetime


def train_archive_model(archive_id, data_dir, knowledge_mapping_file):
    """在后台训练模型"""
    from flask import current_app
    
    with current_app.app_context():
        archive = ModelArchive.query.get(archive_id)
        if not archive:
            return
        
        try:
            # 更新状态为训练中
            archive.status = 'training'
            db.session.commit()
            
            # 准备训练数据
            neuralcdm_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'NeuralCDM_plus-main')
            
            # 复制知识图谱映射文件到 data 目录
            shutil.copy(knowledge_mapping_file, os.path.join(neuralcdm_dir, 'data', 'knowledge_mapping.txt'))
            
            # 准备训练和验证数据集
            train_data = {
                'train_set': [],
                'val_set': [],
                'test_set': []
            }
            
            # 从 data_dir 中读取所有上传的文件
            for filename in os.listdir(data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(data_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'train' in filename.lower():
                                train_data['train_set'].extend(data if isinstance(data, list) else [])
                            elif 'val' in filename.lower() or 'valid' in filename.lower():
                                train_data['val_set'].extend(data if isinstance(data, list) else [])
                            elif 'test' in filename.lower():
                                train_data['test_set'].extend(data if isinstance(data, list) else [])
                    except Exception as e:
                        print(f'[Archive] 读取文件失败 {filename}: {e}')
            
            # 保存训练数据到 NeuralCDM+ 目录
            for dataset_name, dataset in train_data.items():
                if dataset:
                    file_path = os.path.join(neuralcdm_dir, 'data', f'{dataset_name}.json')
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(dataset, f, ensure_ascii=False, indent=2)
                    print(f'[Archive] 保存 {dataset_name} 共 {len(dataset)} 条数据')
            
            # 运行训练脚本
            print(f'[Archive] 开始训练模型...')
            train_script = os.path.join(neuralcdm_dir, 'full_train.py')
            
            process = subprocess.Popen(
                ['python', train_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=neuralcdm_dir
            )
            
            log_lines = []
            for line in process.stdout:
                print(f'[Train] {line.strip()}')
                log_lines.append(line)
            
            process.wait()
            
            # 训练完成后，查找最佳模型
            if process.returncode == 0:
                # 读取训练结果查找最佳 epoch
                result_file = os.path.join(neuralcdm_dir, 'result', 'model_test.txt')
                best_epoch = 1
                best_accuracy = 0
                
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if 'accuracy' in line.lower():
                                try:
                                    parts = line.strip().split(',')
                                    for part in parts:
                                        if 'epoch' in part.lower():
                                            epoch = int(part.split('=')[1].strip())
                                        if 'accuracy' in part.lower():
                                            acc = float(part.split('=')[1].strip())
                                            if acc > best_accuracy:
                                                best_accuracy = acc
                                                best_epoch = epoch
                                except:
                                    pass
                
                # 复制最佳模型到存档目录
                # 获取 backend 根目录（ archives 目录所在位置）
                # __file__ 是 app/archives/routes.py
                # dirname(__file__) 是 app/archives
                # dirname(app/archives) 是 app
                # dirname(app) 是 backend
                backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                archive_dir = os.path.join(backend_dir, 'archives', archive.name)
                os.makedirs(archive_dir, exist_ok=True)
                print(f'[DEBUG] 存档目录: {archive_dir}')
                
                # 复制词嵌入文件
                word_emb_src = os.path.join(neuralcdm_dir, 'result', 'word2vec.model')
                word_emb_dst = os.path.join(archive_dir, f'{archive.name}W')
                if os.path.exists(word_emb_src):
                    shutil.copy(word_emb_src, word_emb_dst)
                    archive.word_emb_path = os.path.join('archives', archive.name, f'{archive.name}W')
                
                # 复制诊断模型文件
                model_src = os.path.join(neuralcdm_dir, 'model', f'model_epoch{best_epoch}')
                model_dst = os.path.join(archive_dir, f'{archive.name}N')
                if os.path.exists(model_src):
                    shutil.copy(model_src, model_dst)
                    archive.diagnosis_model_path = os.path.join('archives', archive.name, f'{archive.name}N')
                
                # 复制知识点映射文件
                mapping_dst = os.path.join(archive_dir, f'{archive.name}map.txt')
                shutil.copy(knowledge_mapping_file, mapping_dst)
                archive.knowledge_mapping_path = os.path.join('archives', archive.name, f'{archive.name}map.txt')
                
                archive.status = 'completed'
                archive.training_log = ''.join(log_lines)
                print(f'[Archive] 训练完成！最佳 epoch: {best_epoch}, 准确率：{best_accuracy:.4f}')
            else:
                archive.status = 'failed'
                archive.training_log = ''.join(log_lines)
                print(f'[Archive] 训练失败，返回码：{process.returncode}')
            
            db.session.commit()
            
        except Exception as e:
            print(f'[Archive] 训练异常：{e}')
            import traceback
            traceback.print_exc()
            with current_app.app_context():
                archive.status = 'failed'
                archive.training_log = str(e)
                db.session.commit()


@bp.route('/', methods=['GET'])
def get_archives():
    """获取所有存档"""
    teacher_id = request.args.get('teacher_id', type=int)
    
    query = ModelArchive.query
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    
    archives = query.order_by(ModelArchive.created_at.desc()).all()
    
    result = []
    for archive in archives:
        result.append({
            'id': archive.id,
            'name': archive.name,
            'status': archive.status,
            'created_at': archive.created_at.strftime('%Y-%m-%d %H:%M:%S') if archive.created_at else None,
            'has_word_emb': bool(archive.word_emb_path),
            'has_diagnosis_model': bool(archive.diagnosis_model_path),
            'has_knowledge_mapping': bool(archive.knowledge_mapping_path)
        })
    
    return jsonify({'success': True, 'archives': result})


@bp.route('/', methods=['POST'])
def create_archive():
    """创建新存档"""
    data = request.form
    
    name = data.get('name')
    teacher_id = data.get('teacher_id', type=int)
    
    if not name or not teacher_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400
    
    # 检查名称是否已存在
    existing = ModelArchive.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'error': '存档名称已存在'}), 400
    
    archive = ModelArchive(
        name=name,
        teacher_id=teacher_id,
        status='pending'
    )
    
    db.session.add(archive)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'archive': {
            'id': archive.id,
            'name': archive.name,
            'status': archive.status
        }
    })


@bp.route('/create-with-files', methods=['POST'])
def create_archive_with_files():
    """创建存档并上传文件（支持两种模式：选择已有模型或上传训练文件）"""
    data = request.form
    
    name = data.get('name')
    teacher_id = data.get('user_id', type=int)
    create_mode = data.get('create_mode', 'existing')  # 'existing' 或 'train'
    
    if not name or not teacher_id:
        return jsonify({'success': False, 'error': '缺少必要参数'}), 400
    
    # 检查名称是否已存在
    existing = ModelArchive.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'error': '存档名称已存在'}), 400
    
    # 创建存档记录
    archive = ModelArchive(
        name=name,
        teacher_id=teacher_id,
        status='pending'
    )
    db.session.add(archive)
    db.session.commit()
    
    try:
        # 创建存档目录 - 使用 backend/archives 目录
        # __file__ 是 app/archives/routes.py
        # dirname(__file__) 是 app/archives
        # dirname(app/archives) 是 app
        # dirname(app) 是 backend
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        archive_dir = os.path.join(backend_dir, 'archives', name)
        os.makedirs(archive_dir, exist_ok=True)
        print(f'[DEBUG] 创建存档目录: {archive_dir}')
        
        if create_mode == 'existing':
            # 选择已有模型模式
            # 保存 word2vec 模型
            if 'word2vec_model' in request.files:
                word2vec_file = request.files['word2vec_model']
                word2vec_path = os.path.join(archive_dir, f'{name}W')
                word2vec_file.save(word2vec_path)
                archive.word_emb_path = os.path.join('archives', name, f'{name}W')
            
            # 保存诊断模型文件 - 直接保存在存档根目录下，不使用 model 子目录
            diagnosis_files = request.files.getlist('diagnosis_model_files')
            if diagnosis_files:
                # 直接保存在存档根目录下
                for file in diagnosis_files:
                    if file.filename:
                        file_path = os.path.join(archive_dir, f'{name}N')
                        file.save(file_path)
                # 设置主模型路径为 {name}N 格式（直接存放在存档根目录）
                archive.diagnosis_model_path = os.path.join('archives', name, f'{name}N')
            
            # 保存知识点映射文件
            if 'knowledge_mapping' in request.files:
                mapping_file = request.files['knowledge_mapping']
                mapping_path = os.path.join(archive_dir, f'{name}map.txt')
                mapping_file.save(mapping_path)
                archive.knowledge_mapping_path = os.path.join('archives', name, f'{name}map.txt')
            
            archive.status = 'completed'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'archive': {
                    'id': archive.id,
                    'name': archive.name,
                    'status': archive.status
                }
            })
            
        else:
            # 上传训练文件模式
            # 保存知识点映射文件
            if 'knowledge_mapping' not in request.files:
                return jsonify({'success': False, 'error': '缺少知识点映射文件'}), 400
            
            knowledge_mapping_file = request.files['knowledge_mapping']
            mapping_path = os.path.join(archive_dir, 'knowledge_mapping.txt')
            knowledge_mapping_file.save(mapping_path)
            archive.knowledge_mapping_path = os.path.join('archives', name, 'knowledge_mapping.txt')
            
            # 保存训练数据文件
            train_data_files = request.files.getlist('train_data_files')
            if not train_data_files:
                return jsonify({'success': False, 'error': '缺少训练数据文件'}), 400
            
            train_data_dir = os.path.join(archive_dir, 'train_data')
            os.makedirs(train_data_dir, exist_ok=True)
            for file in train_data_files:
                if file.filename:
                    file_path = os.path.join(train_data_dir, file.filename)
                    file.save(file_path)
            
            db.session.commit()
            
            # 启动后台训练线程
            thread = threading.Thread(
                target=train_archive_model_with_raw_data,
                args=(archive.id, train_data_dir, mapping_path, name)
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'success': True,
                'message': '文件上传成功，训练已启动',
                'archive_id': archive.id
            })
            
    except Exception as e:
        print(f'[Archive] 创建存档失败：{e}')
        import traceback
        traceback.print_exc()
        archive.status = 'failed'
        db.session.commit()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<int:archive_id>/upload', methods=['POST'])
def upload_archive_files(archive_id):
    """上传存档文件并开始训练"""
    archive = ModelArchive.query.get(archive_id)
    if not archive:
        return jsonify({'success': False, 'error': '存档不存在'}), 404
    
    if 'knowledge_mapping' not in request.files:
        return jsonify({'success': False, 'error': '缺少知识点映射文件'}), 400
    
    knowledge_mapping_file = request.files['knowledge_mapping']
    
    # 保存上传的文件
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'archive_uploads', str(archive_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存知识点映射文件
    mapping_path = os.path.join(upload_dir, 'knowledge_mapping.txt')
    knowledge_mapping_file.save(mapping_path)
    
    # 保存其他数据文件
    data_files = []
    for key in request.files:
        if key != 'knowledge_mapping':
            file = request.files[key]
            if file.filename:
                file_path = os.path.join(upload_dir, file.filename)
                file.save(file_path)
                data_files.append(file_path)
    
    # 启动后台训练线程
    thread = threading.Thread(
        target=train_archive_model,
        args=(archive_id, upload_dir, mapping_path)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': '文件上传成功，训练已启动',
        'archive_id': archive_id
    })


@bp.route('/<int:archive_id>', methods=['GET'])
def get_archive_detail(archive_id):
    """获取存档详情"""
    archive = ModelArchive.query.get(archive_id)
    if not archive:
        return jsonify({'success': False, 'error': '存档不存在'}), 404
    
    return jsonify({
        'success': True,
        'archive': {
            'id': archive.id,
            'name': archive.name,
            'status': archive.status,
            'training_log': archive.training_log,
            'created_at': archive.created_at.strftime('%Y-%m-%d %H:%M:%S') if archive.created_at else None,
            'word_emb_path': archive.word_emb_path,
            'diagnosis_model_path': archive.diagnosis_model_path,
            'knowledge_mapping_path': archive.knowledge_mapping_path
        }
    })


@bp.route('/<int:archive_id>', methods=['DELETE'])
def delete_archive(archive_id):
    """删除存档"""
    archive = ModelArchive.query.get(archive_id)
    if not archive:
        return jsonify({'success': False, 'error': '存档不存在'}), 404
    
    # 检查是否有专栏使用该存档
    if archive.columns.count() > 0:
        return jsonify({'success': False, 'error': '有专栏正在使用该存档，无法删除'}), 400
    
    # 删除存档文件
    if archive.word_emb_path:
        try:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], archive.word_emb_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f'[Archive] 删除词嵌入文件失败：{e}')
    
    if archive.diagnosis_model_path:
        try:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], archive.diagnosis_model_path)
            if os.path.exists(file_path):
                shutil.rmtree(os.path.dirname(file_path))
        except Exception as e:
            print(f'[Archive] 删除模型文件失败：{e}')
    
    # 删除数据库记录
    db.session.delete(archive)
    db.session.commit()
    
    return jsonify({'success': True})


def train_archive_model_with_raw_data(archive_id, train_data_dir, knowledge_mapping_file, archive_name):
    """使用原始数据训练模型（类似玄高数据汇总处理流程）"""
    from flask import current_app
    
    with current_app.app_context():
        archive = ModelArchive.query.get(archive_id)
        if not archive:
            return
        
        try:
            # 更新状态为训练中
            archive.status = 'training'
            db.session.commit()
            
            # 准备训练数据
            neuralcdm_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'NeuralCDM_plus-main')
            
            # 复制知识点映射文件到 data 目录
            shutil.copy(knowledge_mapping_file, os.path.join(neuralcdm_dir, 'data', 'knowledge_mapping.txt'))
            
            # 处理原始数据（类似玄高数据汇总中的处理方式）
            # 读取所有上传的训练数据文件
            raw_data = []
            for filename in os.listdir(train_data_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(train_data_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                raw_data.extend(data)
                    except Exception as e:
                        print(f'[Archive] 读取文件失败 {filename}: {e}')
            
            # 使用知识点映射作为 question 映射，生成训练所需格式
            # 这里需要将 raw_data 转换为 NeuralCDM+ 所需的格式
            # 格式参考：user_id, exer_id, score, knowledge_code
            
            train_set = []
            val_set = []
            test_set = []
            
            # 简单的数据分割：70% 训练，15% 验证，15% 测试
            random.shuffle(raw_data)
            n = len(raw_data)
            train_end = int(n * 0.7)
            val_end = int(n * 0.85)
            
            for i, record in enumerate(raw_data):
                # 转换数据格式
                formatted_record = {
                    'user_id': record.get('user_id', record.get('student_id', i)),
                    'exer_id': record.get('exer_id', record.get('question_id', i)),
                    'score': float(record.get('score', record.get('answer', 0))),
                    'knowledge_code': record.get('knowledge_code', record.get('knowledge_points', [1]))
                }
                
                if i < train_end:
                    train_set.append(formatted_record)
                elif i < val_end:
                    val_set.append(formatted_record)
                else:
                    test_set.append(formatted_record)
            
            # 保存转换后的训练数据
            datasets = {
                'train_set': train_set,
                'val_set': val_set,
                'test_set': test_set
            }
            
            for dataset_name, dataset in datasets.items():
                file_path = os.path.join(neuralcdm_dir, 'data', f'{dataset_name}.json')
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(dataset, f, ensure_ascii=False, indent=2)
                print(f'[Archive] 保存 {dataset_name} 共 {len(dataset)} 条数据')
            
            # 运行训练脚本
            print(f'[Archive] 开始训练模型...')
            train_script = os.path.join(neuralcdm_dir, 'full_train.py')
            
            process = subprocess.Popen(
                ['python', train_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=neuralcdm_dir
            )
            
            log_lines = []
            for line in process.stdout:
                print(f'[Train] {line.strip()}')
                log_lines.append(line)
            
            process.wait()
            
            # 训练完成后，查找最佳模型
            if process.returncode == 0:
                # 读取训练结果查找最佳 epoch
                result_file = os.path.join(neuralcdm_dir, 'result', 'model_test.txt')
                best_epoch = 1
                best_accuracy = 0
                
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if 'accuracy' in line.lower():
                                try:
                                    parts = line.strip().split(',')
                                    for part in parts:
                                        if 'epoch' in part.lower():
                                            epoch = int(part.split('=')[1].strip())
                                        if 'accuracy' in part.lower():
                                            acc = float(part.split('=')[1].strip())
                                            if acc > best_accuracy:
                                                best_accuracy = acc
                                                best_epoch = epoch
                                except:
                                    pass
                
                # 复制最佳模型到存档目录
                # 获取 backend 根目录（ archives 目录所在位置）
                # __file__ 是 app/archives/routes.py
                # dirname(__file__) 是 app/archives
                # dirname(app/archives) 是 app
                # dirname(app) 是 backend
                backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                archive_dir = os.path.join(backend_dir, 'archives', archive_name)
                os.makedirs(archive_dir, exist_ok=True)
                print(f'[DEBUG] 存档目录: {archive_dir}')
                
                # 复制词嵌入文件
                word_emb_src = os.path.join(neuralcdm_dir, 'result', 'word2vec.model')
                word_emb_dst = os.path.join(archive_dir, f'{archive_name}W')
                if os.path.exists(word_emb_src):
                    shutil.copy(word_emb_src, word_emb_dst)
                    archive.word_emb_path = os.path.join('archives', archive_name, f'{archive_name}W')
                
                # 复制诊断模型文件
                model_src = os.path.join(neuralcdm_dir, 'model', f'model_epoch{best_epoch}')
                model_dst = os.path.join(archive_dir, f'{archive_name}N')
                if os.path.exists(model_src):
                    shutil.copy(model_src, model_dst)
                    archive.diagnosis_model_path = os.path.join('archives', archive_name, f'{archive_name}N')
                
                # 复制知识点映射文件
                mapping_dst = os.path.join(archive_dir, f'{archive_name}map.txt')
                shutil.copy(knowledge_mapping_file, mapping_dst)
                archive.knowledge_mapping_path = os.path.join('archives', archive_name, f'{archive_name}map.txt')
                
                archive.status = 'completed'
                archive.training_log = ''.join(log_lines)
                print(f'[Archive] 训练完成！最佳 epoch: {best_epoch}, 准确率：{best_accuracy:.4f}')
            else:
                archive.status = 'failed'
                archive.training_log = ''.join(log_lines)
                print(f'[Archive] 训练失败，返回码：{process.returncode}')
            
            db.session.commit()
            
        except Exception as e:
            print(f'[Archive] 训练异常：{e}')
            import traceback
            traceback.print_exc()
            with current_app.app_context():
                archive.status = 'failed'
                archive.training_log = str(e)
                db.session.commit()
