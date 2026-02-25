import sys
import os
import re

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

print("="*60)
print("两阶段完整训练流程")
print("="*60)

print("\n第一步：训练NetKnowledge...")

from net_knowledge import prepare_embedding, train, test, extract_topk
import pickle
from bintrees import FastRBTree

prepare_embedding()
train(epoch_n=30)
test(K=20, test_fpath='data/net_knowledge_pred.json', epoch_low=1, epoch_high=31)

print("\n自动查找最佳epoch...")

best_epoch = 1
best_map = 0

with open('result/netknowledge_test.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    last_lines = lines[-30:] if len(lines) >= 30 else lines
    print(f"读取文件最后 {len(last_lines)} 行")
    
for line in last_lines:
    line = line.strip()
    if not line:
        continue
    match = re.search(r'epoch= (\d+), MAP= ([\d.]+)', line)
    if match:
        epoch = int(match.group(1))
        map_val = float(match.group(2))
        if map_val > best_map:
            best_map = map_val
            best_epoch = epoch

print(f"最佳epoch: {best_epoch}, MAP: {best_map}")

print(f"\n使用epoch={best_epoch}生成知识点对...")

extract_topk(K=20, epoch=best_epoch, test_fpath='data/net_knowledge_train.json', dst_path='data/temp_train_pairs.FastRBTree')
extract_topk(K=20, epoch=best_epoch, test_fpath='data/net_knowledge_pred.json', dst_path='data/temp_pred_pairs.FastRBTree')

print("合并知识点对...")
with open('data/temp_train_pairs.FastRBTree', 'rb') as f:
    train_pairs = pickle.load(f)
with open('data/temp_pred_pairs.FastRBTree', 'rb') as f:
    pred_pairs = pickle.load(f)

all_pairs = FastRBTree()
for exer_id, pairs in train_pairs.items():
    all_pairs.insert(exer_id, pairs)
for exer_id, pairs in pred_pairs.items():
    all_pairs.insert(exer_id, pairs)

with open('data/netknowledge_pred_topk_knowledge_pairs.FastRBTree', 'wb') as o_f:
    pickle.dump(all_pairs, o_f)

if os.path.exists('data/temp_train_pairs.FastRBTree'):
    os.remove('data/temp_train_pairs.FastRBTree')
if os.path.exists('data/temp_pred_pairs.FastRBTree'):
    os.remove('data/temp_pred_pairs.FastRBTree')

print(f"知识点对生成完成！共 {len(all_pairs)} 道题目")

print("\n" + "="*60)
print("第二步：训练NeuralCDM+...")
print("="*60)

from main import train as train_cdm, test as test_cdm

train_cdm(epoch_n=40)
test_cdm(epoch_n=40)

print("\n训练全部完成！")
print("="*60)
