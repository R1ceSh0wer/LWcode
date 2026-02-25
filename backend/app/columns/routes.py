from flask import jsonify, request, current_app
from datetime import datetime
from models import db, ExamColumn, Comment
from utils import allowed_file, ocr_process, batch_ocr_process, save_uploaded_file, init_ocr_engine, extract_knowledge_from_ocr_text, get_knowledge_model
import os
import json
from app.columns import bp


@bp.route('/columns', methods=['GET'])
def get_columns():
    try:
        columns = ExamColumn.query.all()
        
        result = []
        for column in columns:
            result.append({
                'id': str(column.id),
                'name': column.title,
                'description': column.question_text or '',
                'created': column.created_at.strftime('%Y-%m-%d'),
                'teacherId': str(column.teacher_id)
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取专栏列表失败：{str(e)}'}), 500


@bp.route('/columns/<string:id>', methods=['GET'])
def get_column(id):
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        
        if column:
            return jsonify({
                'id': str(column.id),
                'name': column.title,
                'description': column.question_text or '',
                'created': column.created_at.strftime('%Y-%m-%d'),
                'questionImagePath': column.question_image_path or '',
                'teacherId': str(column.teacher_id)
            })
        return jsonify({'message': '专栏不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取专栏信息失败：{str(e)}'}), 500


@bp.route('/columns', methods=['POST'])
def create_column():
    try:
        title = request.form.get('name')
        teacher_id = request.form.get('teacherId', 1)
        
        new_column = ExamColumn(
            teacher_id=teacher_id,
            title=title,
            question_text=""
        )
        db.session.add(new_column)
        db.session.commit()
        
        question_image_paths = [None] * 6
        file_paths = []
        
        for i in range(1, 7):
            file_key = f'image{i}'
            if file_key in request.files:
                file = request.files[file_key]
                if file and allowed_file(file.filename):
                    file_path, filename = save_uploaded_file(file)
                    if file_path:
                        relative_path = f'uploads/{filename}'
                        setattr(new_column, f'question_image_path{i}', relative_path)
                        question_image_paths[i-1] = file_path
                        file_paths.append(file_path)
        
        question_texts_dict = {}
        question_knowledge_dict = {}
        
        if file_paths:
            print(f'[OCR] 开始并行处理 {len(file_paths)} 张图片')
            ocr_results = batch_ocr_process(file_paths, quality_mode='light', max_workers=2)
            
            for i, (image_path, ocr_result) in enumerate(zip(question_image_paths, ocr_results)):
                if image_path and ocr_result:
                    question_texts_dict[f"img_{i+1}"] = ocr_result
            
            try:
                print(f'[Knowledge] 开始从OCR文本提取题目和预测知识点')
                
                # 获取知识点模型
                print(f'[DEBUG] 获取知识点模型...')
                knowledge_model = get_knowledge_model()
                print(f'[DEBUG] 知识点模型获取结果: {knowledge_model is not None}')
                
                if knowledge_model:
                    all_questions = {}
                    all_knowledge = {}
                    
                    # 从OCR结果中提取题目和知识点
                    for i, ocr_result in enumerate(ocr_results):
                        if ocr_result:
                            questions, knowledge = extract_knowledge_from_ocr_text(ocr_result, knowledge_model)
                            all_questions.update(questions)
                            all_knowledge.update(knowledge)
                    
                    question_texts_dict = {str(k): v for k, v in all_questions.items()}
                    question_knowledge_dict = {str(k): v for k, v in all_knowledge.items()}
                    print(f'[Knowledge] 识别到 {len(question_texts_dict)} 道题目，{len(question_knowledge_dict)} 道题目的知识点')
                else:
                    print(f'[ERROR] 知识点模型初始化失败')
            except Exception as e:
                print(f'[WARN] 知识点预测失败: {str(e)}')
                import traceback
                traceback.print_exc()
        
        new_column.question_text = json.dumps(question_texts_dict, ensure_ascii=False) if question_texts_dict else "{}"
        new_column.question_knowledge = json.dumps(question_knowledge_dict, ensure_ascii=False) if question_knowledge_dict else "{}"
        
        db.session.commit()
        
        return jsonify({
            'id': str(new_column.id),
            'name': new_column.title,
            'description': new_column.question_text,
            'questionKnowledge': new_column.question_knowledge,
            'created': new_column.created_at.strftime('%Y-%m-%d'),
            'teacherId': str(new_column.teacher_id)
        }), 201
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'创建专栏失败：{str(e)}'}), 500


@bp.route('/columns/<string:id>', methods=['PUT'])
def update_column(id):
    data = request.get_json()
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        if not column:
            return jsonify({'success': False, 'message': '专栏不存在'}), 404
        
        column.title = data.get('name', column.title)
        column.question_text = data.get('description', column.question_text)
        db.session.commit()
        
        return jsonify({
            'id': str(column.id),
            'name': column.title,
            'description': column.question_text,
            'created': column.created_at.strftime('%Y-%m-%d'),
            'teacherId': str(column.teacher_id)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新专栏失败：{str(e)}'}), 500


@bp.route('/columns/<string:id>', methods=['DELETE'])
def delete_column(id):
    try:
        column = ExamColumn.query.filter_by(id=id).first()
        if not column:
            return jsonify({'success': False, 'message': '专栏不存在'}), 404
        
        image_paths = [
            column.question_image_path1,
            column.question_image_path2,
            column.question_image_path3,
            column.question_image_path4,
            column.question_image_path5,
            column.question_image_path6
        ]
        
        for image_path in image_paths:
            if image_path:
                full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(image_path))
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f'[DELETE] 删除图片文件: {full_path}')
                except Exception as e:
                    print(f'[DELETE] 删除图片文件失败 {full_path}: {str(e)}')
        
        comments = Comment.query.filter_by(column_id=id).all()
        for comment in comments:
            comment_image_paths = [
                comment.answer_image_path1,
                comment.answer_image_path2,
                comment.answer_image_path3,
                comment.answer_image_path4,
                comment.answer_image_path5,
                comment.answer_image_path6
            ]
            
            for image_path in comment_image_paths:
                if image_path:
                    full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(image_path))
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            print(f'[DELETE] 删除评语图片文件: {full_path}')
                    except Exception as e:
                        print(f'[DELETE] 删除评语图片文件失败 {full_path}: {str(e)}')
        
        Comment.query.filter_by(column_id=id).delete()
        
        db.session.delete(column)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '专栏已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除专栏失败：{str(e)}'}), 500
