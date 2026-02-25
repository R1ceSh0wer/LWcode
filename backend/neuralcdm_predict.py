import os
import sys
import json
import subprocess

exer_n = 3790
knowledge_n = 196
student_n = 190

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
NEURALCDM_DIR = os.path.join(PROJECT_ROOT, 'NeuralCDM_plus-main')
NEURALCDM_PYTHON = os.path.join(NEURALCDM_DIR, '.venv', 'Scripts', 'python.exe')
DIAGNOSIS_SCRIPT = os.path.join(NEURALCDM_DIR, 'diagnosis_service.py')

def _call_diagnosis_service(student_id, exercise_ids, knowledge_codes, model_path):
    input_data = {
        'student_id': student_id,
        'exercise_ids': exercise_ids,
        'knowledge_codes': knowledge_codes,
        'model_path': model_path
    }
    
    try:
        result = subprocess.run(
            [NEURALCDM_PYTHON, DIAGNOSIS_SCRIPT],
            cwd=NEURALCDM_DIR,
            input=json.dumps(input_data),
            capture_output=True,
            encoding='utf-8',
            timeout=30
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            if output.get('success'):
                return output['predictions'], output['mastery']
            else:
                print(f'[NeuralCDM] 诊断服务失败: {output.get("error")}')
        else:
            print(f'[NeuralCDM] 诊断服务错误: {result.stderr}')
    except Exception as e:
        print(f'[NeuralCDM] 调用诊断服务失败: {str(e)}')
        import traceback
        traceback.print_exc()
    
    return None, None


def load_neuralcdm_model(model_path):
    if not os.path.exists(model_path):
        print(f'[NeuralCDM] 模型文件不存在: {model_path}')
        return None
    
    print(f'[NeuralCDM] 模型路径: {model_path}')
    return {'path': model_path}


def predict_student_performance(model, student_id, exercise_ids, knowledge_codes):
    if model is None:
        print(f'[NeuralCDM] 模型未加载，返回默认预测值')
        return [0.5] * len(exercise_ids)
    
    model_path = model.get('path') if isinstance(model, dict) else model
    
    predictions, mastery = _call_diagnosis_service(
        student_id, exercise_ids, knowledge_codes, model_path
    )
    
    if predictions is not None:
        print(f'[NeuralCDM] 诊断服务返回预测成功')
        return predictions
    else:
        print(f'[NeuralCDM] 诊断服务失败，返回默认预测值')
        return [0.5] * len(exercise_ids)


def get_student_knowledge_status(model, student_id):
    import numpy as np
    
    if model is None:
        return np.array([0.5] * knowledge_n)
    
    model_path = model.get('path') if isinstance(model, dict) else model
    
    predictions, mastery = _call_diagnosis_service(
        student_id, [0], [[0]], model_path
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
