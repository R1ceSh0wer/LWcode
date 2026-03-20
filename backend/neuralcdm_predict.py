import os
import sys
import json
import subprocess

from flask import current_app

exer_n = 3790
knowledge_n = 196
student_n = 190

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
NEURALCDM_DIR = os.path.join(PROJECT_ROOT, 'NeuralCDM_plus-main')
NEURALCDM_PYTHON = os.path.join(NEURALCDM_DIR, '.venv', 'Scripts', 'python.exe')
DIAGNOSIS_SCRIPT = os.path.join(NEURALCDM_DIR, 'diagnosis_service.py')

# 获取上传文件夹路径
# __file__ 是 neuralcdm_predict.py，位于 backend 目录下
# BASE_DIR 已经在上面定义为 backend 目录
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ARCHIVES_FOLDER = os.path.join(BASE_DIR, 'archives')
print(f'[NeuralCDM] BASE_DIR: {BASE_DIR}')
print(f'[NeuralCDM] UPLOAD_FOLDER: {UPLOAD_FOLDER}')
print(f'[NeuralCDM] ARCHIVES_FOLDER: {ARCHIVES_FOLDER}')

def _call_diagnosis_service(student_id, exercise_ids, knowledge_codes, model_path, knowledge_num):
    # 处理模型路径，确保使用正确的绝对路径
    if not os.path.isabs(model_path):
        # 优先尝试 archives 目录（因为模型文件存储在 backend/archives 下）
        archives_path = os.path.join(ARCHIVES_FOLDER, model_path)
        if os.path.exists(archives_path):
            model_path = archives_path
        else:
            # 然后尝试 uploads/archives 目录
            uploads_archives_path = os.path.join(UPLOAD_FOLDER, 'archives', model_path)
            if os.path.exists(uploads_archives_path):
                model_path = uploads_archives_path
            else:
                # 最后尝试 uploads 目录
                model_path = os.path.join(UPLOAD_FOLDER, model_path)
    
    input_data = {
        'student_id': student_id,
        'exercise_ids': exercise_ids,
        'knowledge_codes': knowledge_codes,
        'model_path': model_path,
        'knowledge_num': knowledge_num
    }
    
    try:
        print(f'[NeuralCDM] 调用诊断服务...')
        print(f'[NeuralCDM] 模型路径: {model_path}')
        print(f'[NeuralCDM] 学生ID: {student_id}')
        print(f'[NeuralCDM] 题目ID: {exercise_ids}')
        print(f'[NeuralCDM] 知识点编码: {knowledge_codes}')
        
        # 检查模型文件是否存在
        if not os.path.exists(model_path):
            print(f'[DEBUG] 模型路径是否存在: {os.path.exists(model_path)}')
            print(f'[NeuralCDM] 模型文件不存在: {model_path}')
            # 尝试其他可能的路径
            alternative_paths = [
                # 尝试 uploads 目录
                os.path.join(UPLOAD_FOLDER, os.path.basename(model_path)),
                # 尝试当前目录
                os.path.join(os.getcwd(), os.path.basename(model_path)),
                # 尝试父目录
                os.path.join(os.path.dirname(os.getcwd()), os.path.basename(model_path)),
                # 尝试 archives 目录直接路径
                os.path.join(UPLOAD_FOLDER, 'archives', os.path.basename(model_path))
            ]
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    print(f'[NeuralCDM] 找到模型文件在替代路径: {alt_path}')
                    model_path = alt_path
                    input_data['model_path'] = alt_path
                    break
            else:
                # 所有路径都不存在
                return None, None
        
        # 检查诊断服务脚本是否存在
        if not os.path.exists(DIAGNOSIS_SCRIPT):
            print(f'[NeuralCDM] 诊断服务脚本不存在: {DIAGNOSIS_SCRIPT}')
            return None, None
        
        # 检查Python解释器是否存在
        if not os.path.exists(NEURALCDM_PYTHON):
            print(f'[NeuralCDM] Python解释器不存在: {NEURALCDM_PYTHON}')
            return None, None
        
        result = subprocess.run(
            [NEURALCDM_PYTHON, DIAGNOSIS_SCRIPT],
            cwd=NEURALCDM_DIR,
            input=json.dumps(input_data),
            capture_output=True,
            encoding='utf-8',
            timeout=60  # 增加超时时间到60秒
        )
        
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                if output.get('success'):
                    predictions = output.get('predictions', [])
                    mastery = output.get('mastery', [])
                    print(f'[NeuralCDM] 诊断服务返回成功')
                    print(f'[NeuralCDM] 预测结果: {predictions}')
                    print(f'[NeuralCDM] 知识点掌握度: {mastery[:5] if len(mastery) > 5 else mastery}')
                    return predictions, mastery
                else:
                    print(f'[NeuralCDM] 诊断服务失败: {output.get("error")}')
                    return None, None
            except json.JSONDecodeError as e:
                print(f'[NeuralCDM] 解析诊断服务输出失败: {str(e)}')
                print(f'[NeuralCDM] 原始输出: {result.stdout}')
                return None, None
        else:
            print(f'[NeuralCDM] 诊断服务错误: {result.stderr}')
            print(f'[NeuralCDM] 返回码: {result.returncode}')
            return None, None
    except subprocess.TimeoutExpired:
        print(f'[NeuralCDM] 诊断服务超时')
        return None, None
    except Exception as e:
        print(f'[NeuralCDM] 调用诊断服务失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return None, None


def load_neuralcdm_model(model_path):
    # 处理模型路径，确保使用正确的绝对路径
    if not os.path.isabs(model_path):
        # 如果是相对路径，转换为绝对路径（基于 UPLOAD_FOLDER）
        model_path = os.path.join(UPLOAD_FOLDER, model_path)
    
    if not os.path.exists(model_path):
        print(f'[NeuralCDM] 模型文件不存在: {model_path}')
        # 尝试其他可能的路径
        alternative_paths = [
            # 尝试 uploads 目录
            os.path.join(UPLOAD_FOLDER, os.path.basename(model_path)),
            # 尝试当前目录
            os.path.join(os.getcwd(), os.path.basename(model_path)),
            # 尝试父目录
            os.path.join(os.path.dirname(os.getcwd()), os.path.basename(model_path)),
            # 尝试 archives 目录直接路径
            os.path.join(UPLOAD_FOLDER, 'archives', os.path.basename(model_path))
        ]
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                print(f'[NeuralCDM] 找到模型文件在替代路径: {alt_path}')
                model_path = alt_path
                break
        else:
            # 所有路径都不存在
            return None
    
    print(f'[NeuralCDM] 模型路径: {model_path}')
    return {'path': model_path}


def predict_student_performance(model, student_id, column_id, exercise_ids, actual_scores, question_knowledge, knowledge_num):
    if model is None:
        print(f'[NeuralCDM] 模型未加载，返回默认预测值')
        return [0.5] * len(exercise_ids), None
    
    model_path = model.get('path') if isinstance(model, dict) else model
    
    predictions, mastery = _call_diagnosis_service(
        student_id, exercise_ids, question_knowledge, model_path, knowledge_num
    )
    
    if predictions is not None and mastery is not None:
        print(f'[NeuralCDM] 诊断服务返回预测成功')
        return predictions, mastery
    else:
        print(f'[NeuralCDM] 诊断服务失败，返回默认预测值')
        return [0.5] * len(exercise_ids), None


def get_student_knowledge_status(model, student_id):
    import numpy as np
    
    if model is None:
        return np.array([0.5] * knowledge_n)
    
    model_path = model.get('path') if isinstance(model, dict) else model
    
    predictions, mastery = _call_diagnosis_service(
        student_id,
        [0],
        {'img_0': [0]},
        model_path,
        knowledge_n
    )
    
    if mastery is not None:
        import numpy as np
        return np.array(mastery)
    else:
        return np.array([0.5] * knowledge_n)


def analyze_student_weaknesses(model, student_id, top_n=10):
    import numpy as np
    knowledge_status = get_student_knowledge_status(model, student_id)
    
    knowledge_indices = [(i + 1, knowledge_status[i]) for i in range(len(knowledge_status))]
    knowledge_indices.sort(key=lambda x: x[1])
    
    weaknesses = []
    for k_id, proficiency in knowledge_indices[:top_n]:
        weaknesses.append({
            'knowledge_id': k_id,
            'proficiency': float(proficiency),
            'level': '薄弱' if proficiency < 0.3 else '一般' if proficiency < 0.6 else '良好'
        })
    
    return weaknesses


def format_cdm_predictions(exercise_ids, predictions, threshold=0.5):
    results = []
    for exer_id, pred in zip(exercise_ids, predictions):
        results.append({
            'exercise_id': exer_id,
            'predicted_correct_prob': float(pred),
            'predicted_result': '正确' if pred >= threshold else '错误'
        })
    return results
