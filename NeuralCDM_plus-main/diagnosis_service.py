import sys
import os
import json
import pickle
import numpy as np
import re

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

old_stdout = sys.stdout
sys.stdout = sys.stderr

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

import torch
import torch.nn as nn
import torch.nn.functional as F

# 导入 net_knowledge
from net_knowledge import NetKnowledge, TestDataLoader as NetKnowledgeTestDataLoader # 避免名称冲突

exer_n = 3790
knowledge_n = 196
student_n = 190

class NeuralCDMNet(nn.Module):
    def __init__(self, knowledge_dim):
        self.knowledge_dim = knowledge_dim
        self.exer_n = exer_n
        self.emb_num = student_n
        self.stu_dim = self.knowledge_dim
        self.prednet_input_len = self.knowledge_dim
        self.prednet_len1, self.prednet_len2 = 512, 256

        super(NeuralCDMNet, self).__init__()

        self.student_emb = nn.Embedding(self.emb_num, self.stu_dim)
        self.k_difficulty = nn.Embedding(self.exer_n, self.knowledge_dim)
        self.e_discrimination = nn.Embedding(self.exer_n, 1)
        self.e_k_prob = nn.Embedding(self.exer_n, self.knowledge_dim)
        self.prednet_full1 = nn.Linear(self.prednet_input_len, self.prednet_len1)
        self.drop_1 = nn.Dropout(p=0.5)
        self.prednet_full2 = nn.Linear(self.prednet_len1, self.prednet_len2)
        self.drop_2 = nn.Dropout(p=0.5)
        self.prednet_full3 = nn.Linear(self.prednet_len2, 1)

        for name, param in self.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)

    def forward(self, stu_id, input_exercise, knowledge_masks):
        stu_emb = self.student_emb(stu_id)
        stat_emb = F.sigmoid(stu_emb)
        k_difficulty = F.sigmoid(self.k_difficulty(input_exercise))
        e_discrimination = F.sigmoid(self.e_discrimination(input_exercise)) * 10
        e_k_prob = self.e_k_prob(input_exercise)
        e_k_prob_2 = F.sigmoid(e_k_prob)
        
        input_x = e_discrimination * (stat_emb - k_difficulty) * (knowledge_masks * e_k_prob_2)
        input_x = self.drop_1(F.sigmoid(self.prednet_full1(input_x)))
        input_x = self.drop_2(F.sigmoid(self.prednet_full2(input_x)))
        output_1 = F.sigmoid(self.prednet_full3(input_x))
        output_0 = torch.ones(output_1.size()).to(device) - output_1
        output = torch.cat((output_0, output_1), 1)

        return output, e_k_prob

    def get_knowledge_status(self, stat_idx):
        stat_emb = torch.sigmoid(self.student_emb(stat_idx))
        return stat_emb.data

gpu_n = 0
device = torch.device(('cuda:'+str(gpu_n)) if torch.cuda.is_available() else 'cpu')

def load_model(model_path, knowledge_dim_param):
    model = NeuralCDMNet(knowledge_dim=knowledge_dim_param).to(device)
    if os.path.exists(model_path):
        try:
            checkpoint = torch.load(model_path, map_location=device, weights_only=False)
            # 尝试不同的键名
            if 'state_dict' in checkpoint:
                model.load_state_dict(checkpoint['state_dict'])
            elif 'model_state_dict' in checkpoint:
                model.load_state_dict(checkpoint['model_state_dict'])
            else:
                model.load_state_dict(checkpoint)
            model.eval()
            return model
        except Exception as e:
            print(f'[ERROR] 加载模型失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return None
    return None

def predict(model, student_id, exercise_ids, knowledge_codes_dict, knowledge_num):
    import numpy as np
    
    student_id = torch.LongTensor([student_id]).to(device)
    exercise_ids_tensor = torch.LongTensor(exercise_ids).to(device)
    
    knowledge_masks = torch.zeros((len(exercise_ids), knowledge_num)).to(device)
    for i, exer_id in enumerate(exercise_ids):
        # Construct the key for knowledge_codes_dict, e.g., "img_1", "img_2"
        key = f'img_{exer_id}'
        if key in knowledge_codes_dict:
            codes = knowledge_codes_dict[key]
            for code in codes:
                if 0 <= code < knowledge_num:
                    knowledge_masks[i, code] = 1
    
    with torch.no_grad():
        stu_id_expanded = student_id.expand(len(exercise_ids))
        output, _ = model(stu_id_expanded, exercise_ids_tensor, knowledge_masks)
        predictions = output[:, 1].cpu().numpy().tolist()
    
    stu_idx = torch.LongTensor([student_id.item()]).to(device)
    mastery = model.get_knowledge_status(stu_idx).squeeze().cpu().numpy().tolist()
    
    return predictions, mastery

def predict_knowledge_from_text(text_input, cdm_model_path, word_emb_path, knowledge_map, knowledge_num, K=20, epoch=21):
    # 假设 cdm_model_path 实际上是 netknowledge 模型的 epoch 路径
    # 加载 netknowledge 模型
    netknowledge = NetKnowledge()
    netknowledge_model_path = os.path.join(os.path.dirname(cdm_model_path), f'netknowledge/model_epoch{epoch}')
    
    if not os.path.exists(netknowledge_model_path):
        # 尝试在当前目录或项目根目录寻找
        if os.path.exists(f'./netknowledge/model_epoch{epoch}'):
            netknowledge_model_path = f'./netknowledge/model_epoch{epoch}'
        elif os.path.exists(f'../netknowledge/model_epoch{epoch}'): # PROJECT_ROOT
            netknowledge_model_path = f'../netknowledge/model_epoch{epoch}'
        else:
            print(f'[ERROR] NetKnowledge 模型文件不存在: {netknowledge_model_path}')
            return {}

    try:
        checkpoint = torch.load(netknowledge_model_path, map_location=device, weights_only=False)
        if 'state_dict' in checkpoint:
            netknowledge.load_state_dict(checkpoint['state_dict'])
        elif 'model_state_dict' in checkpoint:
            netknowledge.load_state_dict(checkpoint['model_state_dict'])
        else:
            netknowledge.load_state_dict(checkpoint)
        netknowledge.eval()
    except Exception as e:
        print(f'[ERROR] 加载 NetKnowledge 模型失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return {}

    # 准备 word2id 和 word_emb_100
    # 注意：这里的 word_emb_path 应该是直接指向 word_emb_100 和 word2id.FastRBTree 的路径
    word2id_path = os.path.join(os.path.dirname(word_emb_path), 'word2id.FastRBTree')
    word_emb_npy_path = os.path.join(os.path.dirname(word_emb_path), 'word_emb_100')
    
    if not os.path.exists(word2id_path):
        print(f'[ERROR] word2id 文件不存在: {word2id_path}')
        return {}
    if not os.path.exists(word_emb_npy_path):
        print(f'[ERROR] word_emb_100 文件不存在: {word_emb_npy_path}')
        return {}
    
    # 为了 NetKnowledgeTestDataLoader，需要将 text_input 转换为 data/net_knowledge_pred.json 类似的格式
    # { 'text': ['word1', 'word2'], 'exer_id': 1, 'knowledge_code': [] }
    formatted_data = []
    exer_ids_map = {}
    current_exer_id = 1

    # 使用正则表达式解析题目文本
    # 匹配模式：数字 + 冒号（中英文） + 题目内容 + 分号（中英文）或文件末尾\n    # (?s) 允许 . 匹配换行符\n    # (.+?) 非贪婪匹配题目内容\n    # (?=...|\\Z) 正向先行断言，确保匹配到下一个题目或字符串末尾\n    question_pattern = re.compile(r\'(?s)(\\d+)\\s*[:：]\\s*(.+?)(?=[\s;；]*\\d+\\s*[:：]|[\s;；]*\\Z)\')
    parsed_questions = {}

    # 在解析之前，先对文本进行预处理，确保每道题目都有明确的编号和分隔符
    # 将中文冒号替换为英文冒号，方便统一处理
    processed_text_input = text_input.replace('：', ':')
    
    # 查找所有匹配项
    matches = question_pattern.findall(processed_text_input)
    if not matches:
        print('[Text] 未能解析出任何题目，尝试使用换行符分隔')
        # 尝试通过换行符分隔，并为每行分配一个虚拟题号
        lines = [line.strip() for line in processed_text_input.split('\n') if line.strip()]
        if lines:
            for idx, line in enumerate(lines):
                parsed_questions[str(idx + 1)] = line
    else:
        for match in matches:
            q_num = match[0].strip()
            q_text = match[1].strip()
            if q_text:
                parsed_questions[q_num] = q_text

    if not parsed_questions:
        print(f'[Text] 解析到 0 道题目')
        return {}
    
    print(f'[Text] 解析到 {len(parsed_questions)} 道题目')

    for q_num, q_text in parsed_questions.items():
        # 简单分词，可以根据实际情况替换为更复杂的分词器
        words = q_text.split()
        formatted_data.append({
            'text': words,
            'exer_id': current_exer_id,
            'knowledge_code': [] # 预测时不需要真实知识点
        })
        exer_ids_map[current_exer_id] = q_num
        current_exer_id += 1
    
    # 创建一个临时的 JSON 文件供 TestDataLoader 读取
    temp_json_path = os.path.join(os.getcwd(), 'temp_net_knowledge_pred.json')
    with open(temp_json_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=4)
    
    # 修改 NetKnowledgeTestDataLoader 的初始化，使其能接受 word2id_path 和 word_emb_npy_path
    # 或者直接在当前脚本中构建 data_loader 所需的 word2id
    # 这里直接加载 word2id
    with open(word2id_path, 'rb') as i_f:
        word2id = pickle.load(i_f)

    # 模拟 NetKnowledgeTestDataLoader 的行为
    batch_size = 16
    sequence_len = 600
    all_predictions = {}
    
    # 手动处理 batch
    for i in range(0, len(formatted_data), batch_size):
        batch_data = formatted_data[i:i+batch_size]
        
        x_batch = []
        for exer in batch_data:
            word_ids = []
            for word in exer['text'][:sequence_len]:
                word_id = word2id.get(word)
                if word_id is not None:
                    word_ids.append(word_id)
            if len(word_ids) < sequence_len:
                word_ids += [0] * (sequence_len - len(word_ids))
            x_batch.append(word_ids)
            
        x_tensor = torch.LongTensor(x_batch).to(device)
        
        with torch.no_grad():
            knowledge_pred = netknowledge.forward(x_tensor)
            # 应用 sigmoid 得到概率
            probabilities = torch.sigmoid(knowledge_pred)
            _, topk_indices = torch.topk(probabilities, K, dim=1)
        
        # 知识点标号从1开始
        topk_indices = topk_indices + 1
        
        for j, exer in enumerate(batch_data):
            original_q_num = exer_ids_map[exer['exer_id']]
            predicted_codes = topk_indices[j].cpu().numpy().tolist()
            
            # 将预测到的知识点编号转换为名称
            predicted_knowledge_names = []
            for code in predicted_codes:
                if code in knowledge_map:
                    predicted_knowledge_names.append(f'{code}:{knowledge_map[code]}')
                else:
                    predicted_knowledge_names.append(str(code)) # 如果没有映射，直接使用编号
            
            all_predictions[original_q_num] = predicted_codes
    
    # 清理临时文件
    if os.path.exists(temp_json_path):
        os.remove(temp_json_path)

    return all_predictions

if __name__ == '__main__':
    input_data = json.loads(sys.stdin.read())

    # 根据输入判断是进行学生表现预测还是题目知识点预测
    if 'student_id' in input_data and 'exercise_ids' in input_data:
        # 学生表现预测
        student_id = input_data['student_id']
        exercise_ids = input_data['exercise_ids']
        knowledge_codes = input_data['knowledge_codes']
        model_path = input_data['model_path']
        knowledge_num = input_data['knowledge_num']

        model = load_model(model_path, knowledge_num)
        if model:
            predictions, mastery = predict(model, student_id, exercise_ids, knowledge_codes, knowledge_num)
            result = {'success': True, 'predictions': predictions, 'mastery': mastery}
        else:
            result = {'success': False, 'error': 'Model load failed'}
    elif 'text_input' in input_data and 'word_emb_path' in input_data:
        # 题目知识点预测
        text_input = input_data['text_input']
        cdm_model_path = input_data['cdm_model_path']
        word_emb_path = input_data['word_emb_path']
        knowledge_map = input_data['knowledge_map']
        knowledge_num = input_data['knowledge_num']
        K = input_data.get('K', 20)
        epoch = input_data.get('epoch', 21)

        predicted_knowledge = predict_knowledge_from_text(text_input, cdm_model_path, word_emb_path, knowledge_map, knowledge_num, K, epoch)
        if predicted_knowledge is not None:
            result = {'success': True, 'predicted_knowledge': predicted_knowledge}
        else:
            result = {'success': False, 'error': 'Knowledge prediction failed'}
    else:
        result = {'success': False, 'error': 'Invalid input data'}

    old_stdout.write(json.dumps(result) + '\n')
    old_stdout.flush()
