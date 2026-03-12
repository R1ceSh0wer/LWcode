import sys
import os
import json

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

old_stdout = sys.stdout
sys.stdout = sys.stderr

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

import torch
import torch.nn as nn
import torch.nn.functional as F

exer_n = 3790
knowledge_n = 196
student_n = 190

class NeuralCDMNet(nn.Module):
    def __init__(self):
        self.knowledge_dim = knowledge_n
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

def load_model(model_path):
    model = NeuralCDMNet().to(device)
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

def predict(model, student_id, exercise_ids, knowledge_codes):
    import numpy as np
    
    student_id = torch.LongTensor([student_id]).to(device)
    exercise_ids_tensor = torch.LongTensor(exercise_ids).to(device)
    
    knowledge_masks = torch.zeros((len(exercise_ids), knowledge_n)).to(device)
    for i, codes in enumerate(knowledge_codes):
        for code in codes:
            if 0 <= code < knowledge_n:
                knowledge_masks[i, code] = 1
    
    with torch.no_grad():
        stu_id_expanded = student_id.expand(len(exercise_ids))
        output, _ = model(stu_id_expanded, exercise_ids_tensor, knowledge_masks)
        predictions = output[:, 1].cpu().numpy().tolist()
    
    stu_idx = torch.LongTensor([student_id.item()]).to(device)
    mastery = model.get_knowledge_status(stu_idx).squeeze().cpu().numpy().tolist()
    
    return predictions, mastery

if __name__ == '__main__':
    input_data = json.loads(sys.stdin.read())
    
    student_id = input_data['student_id']
    exercise_ids = input_data['exercise_ids']
    knowledge_codes = input_data['knowledge_codes']
    model_path = input_data['model_path']
    
    model = load_model(model_path)
    if model:
        predictions, mastery = predict(model, student_id, exercise_ids, knowledge_codes)
        result = {'success': True, 'predictions': predictions, 'mastery': mastery}
    else:
        result = {'success': False, 'error': 'Model load failed'}
    
    old_stdout.write(json.dumps(result) + '\n')
    old_stdout.flush()
