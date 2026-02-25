import sys
import os
import pickle

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

old_stdout = sys.stdout
sys.stdout = sys.stderr

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

import torch
import torch.nn as nn
import torch.nn.functional as F
import jieba
import types

if 'bintrees.cython_trees' not in sys.modules:
    cython_trees = types.ModuleType('bintrees.cython_trees')
    sys.modules['bintrees.cython_trees'] = cython_trees
    
    class DummyFastRBTree(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        def __setstate__(self, state):
            self.update(state)
        def __reduce__(self):
            return (dict, (dict(self),))
    
    cython_trees.FastRBTree = DummyFastRBTree
    
    if 'bintrees' not in sys.modules:
        sys.modules['bintrees'] = types.ModuleType('bintrees')
        sys.modules['bintrees'].FastRBTree = DummyFastRBTree
        sys.modules['bintrees'].cython_trees = cython_trees

gpu_n = 0
device = torch.device(('cuda:'+str(gpu_n)) if torch.cuda.is_available() else 'cpu')

class NetKnowledge(nn.Module):
    def __init__(self, word2id_len, emb_npy):
        self.embedding_len = 200
        self.sequence_len = 600
        self.output_len = 196
        self.channel_num1, self.channel_num2, self.channel_num3 = 400, 200, 100
        self.kernel_size1, self.kernel_size2, self.kernel_size3 = 3, 4, 5
        self.pool1 = 3
        self.full_in = (self.sequence_len + self.kernel_size1 - 1) // self.pool1 + self.kernel_size2 + self.kernel_size3 - 2
        super(NetKnowledge, self).__init__()

        self.word_emb = nn.Embedding(word2id_len + 1, self.embedding_len, padding_idx=0)
        self.word_emb.weight.data.copy_(torch.from_numpy(emb_npy))
        self.conv1 = nn.Conv1d(self.embedding_len, self.channel_num1, kernel_size=self.kernel_size1, padding=self.kernel_size1-1, stride=1)
        self.conv2 = nn.Conv1d(self.channel_num1, self.channel_num2, kernel_size=self.kernel_size2, padding=self.kernel_size2-1, stride=1)
        self.conv3 = nn.Conv1d(self.channel_num2, self.channel_num3, kernel_size=self.kernel_size3, padding=self.kernel_size3 - 1, stride=1)
        self.full = nn.Linear(self.full_in, self.output_len)

    def forward(self, x):
        x = self.word_emb(x)
        x = torch.transpose(x, 1, 2)
        x = F.relu(self.conv1(x))
        x = F.max_pool1d(x, kernel_size=self.pool1)
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = torch.transpose(x, 1, 2)
        x = F.max_pool1d(x, self.channel_num3)
        x = torch.transpose(x, 1, 2).view(-1, self.full_in)
        ret = self.full(x)
        return ret

word2id = None
word_emb = None

def load_resources():
    global word2id, word_emb
    
    with open('data/word2id.FastRBTree', 'rb') as f:
        word2id = pickle.load(f)
    with open('data/word_emb_100', 'rb') as f:
        word_emb = pickle.load(f)
    
    if hasattr(word2id, 'items'):
        word2id = dict(word2id)

def load_model(model_path):
    model = NetKnowledge(len(word2id), word_emb)
    f = open(model_path, 'rb')
    model.load_state_dict(torch.load(f, map_location=lambda s, loc: s))
    f.close()
    model = model.to(device)
    model.eval()
    return model

def text_to_word_ids(text, max_len=600):
    words = jieba.lcut(text)
    word_ids = []
    for word in words:
        word_id = word2id.get(word)
        if word_id is not None:
            word_ids.append(word_id)
    
    if len(word_ids) < max_len:
        word_ids += [0] * (max_len - len(word_ids))
    else:
        word_ids = word_ids[:max_len]
    
    return word_ids

def predict_knowledge(model, text, top_k=5):
    import numpy as np
    
    word_ids = text_to_word_ids(text)
    if word_ids is None:
        return []
    
    x = torch.LongTensor([word_ids]).to(device)
    
    with torch.no_grad():
        pred = model(x)
        pred = torch.sigmoid(pred)
    
    pred = pred.cpu().numpy()[0]
    
    knowledge_scores = [(i + 1, pred[i]) for i in range(len(pred))]
    knowledge_scores.sort(key=lambda x: x[1], reverse=True)
    
    result = {}
    for k_id, score in knowledge_scores[:top_k]:
        result[str(k_id)] = score
    
    return result

if __name__ == '__main__':
    import json
    
    load_resources()
    
    input_data = json.loads(sys.stdin.read())
    
    text = input_data['text']
    model_path = input_data['model_path']
    top_k = input_data.get('top_k', 5)
    
    model = load_model(model_path)
    if model:
        result = predict_knowledge(model, text, top_k)
        output = {'success': True, 'knowledge': result}
    else:
        output = {'success': False, 'error': 'Model load failed'}
    
    old_stdout.write(json.dumps(output) + '\n')
    old_stdout.flush()
