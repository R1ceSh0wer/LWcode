import json
import os
import re
from tqdm import tqdm
import jieba

DATA_DIR = 'data/玄高数据汇总'
QUESTION_FILE = os.path.join(DATA_DIR, 'question/all-questions.json')
SKILL_TREE_FILE = os.path.join(DATA_DIR, 'question/skill-tag-tree.json')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

OUTPUT_DIR = 'data'
TRAIN_SET_FILE = os.path.join(OUTPUT_DIR, 'train_set_merged.json')
VAL_SET_FILE = os.path.join(OUTPUT_DIR, 'val_set_merged.json')
TEST_SET_FILE = os.path.join(OUTPUT_DIR, 'test_set_merged.json')
NET_KNOWLEDGE_TRAIN_FILE = os.path.join(OUTPUT_DIR, 'net_knowledge_train_merged.json')
NET_KNOWLEDGE_PRED_FILE = os.path.join(OUTPUT_DIR, 'net_knowledge_pred_merged.json')

print("=" * 60)
print("合并 RAW + PROCESSED 数据源")
print("=" * 60)

print("\n1. 加载题库和知识点树...")
with open(QUESTION_FILE, 'r', encoding='utf-8') as f:
    questions = json.load(f)
print(f"   题库: {len(questions)}道")

with open(SKILL_TREE_FILE, 'r', encoding='utf-8') as f:
    skill_tree = json.load(f)

print("\n2. 提取知识点映射...")
knowledge_points = {}
exclude_keywords = ['未分类', '其他', '默认', '通用', '分类', '标签', '专题']

def traverse(node):
    tag_name = node['tagName']
    if any(k in tag_name for k in exclude_keywords):
        return
    knowledge_points[node['id']] = tag_name
    if 'children' in node:
        for child in node['children']:
            traverse(child)

for root in skill_tree:
    traverse(root)

knowledge_map = {}
seen_names = set()
for idx, (k_id, k_name) in enumerate(knowledge_points.items(), 1):
    if k_name not in seen_names:
        seen_names.add(k_name)
        knowledge_map[k_id] = len(knowledge_map) + 1

print(f"   知识点: {len(knowledge_map)}个")

knowledge_mapping_file = os.path.join(OUTPUT_DIR, 'knowledge_mapping_merged.txt')
with open(knowledge_mapping_file, 'w', encoding='utf-8') as f:
    for k_id, code in sorted(knowledge_map.items(), key=lambda x: x[1]):
        f.write(f"{code}：{knowledge_points[k_id]}\n")
print(f"   映射已保存: {knowledge_mapping_file}")

print("\n3. 转换题目数据...")
def clean_and_segment_text(text):
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'[^一-龥a-zA-Z0-9]', ' ', clean_text)
    words = jieba.lcut(clean_text)
    return [w for w in words if w.strip()]

exer_id_map = {}
net_knowledge_data = []
for idx, q in enumerate(tqdm(questions, desc="处理题目")):
    if not q.get('questionDetail') or not q['questionDetail'].get('content'):
        continue
    content = q['questionDetail']['content']
    segmented = clean_and_segment_text(content)
    
    knowledge_codes = []
    for tag in q.get('tags', []):
        if tag['id'] in knowledge_map:
            knowledge_codes.append(knowledge_map[tag['id']])
    
    knowledge_codes = list(set(knowledge_codes))
    if not knowledge_codes:
        continue
    
    net_knowledge_data.append({
        'exer_id': idx + 1,
        'text': segmented,
        'knowledge_code': knowledge_codes
    })
    exer_id_map[q['id']] = idx + 1

print(f"   有效题目: {len(exer_id_map)}道")

train_size_nk = int(len(net_knowledge_data) * 0.8)
save_to_json = lambda d, p: open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2))
save_to_json(net_knowledge_data[:train_size_nk], NET_KNOWLEDGE_TRAIN_FILE)
save_to_json(net_knowledge_data[train_size_nk:], NET_KNOWLEDGE_PRED_FILE)

print(f"\n4. 加载所有答题记录...")

all_records = {}

print("   从raw加载:")
for fname in os.listdir(RAW_DIR):
    if not fname.endswith('.json'):
        continue
    with open(os.path.join(RAW_DIR, fname), 'r', encoding='utf-8') as f:
        data = json.load(f)
        for record in data:
            sid = record.get('studentID')
            if not sid:
                continue
            if sid not in all_records:
                all_records[sid] = {}
            
            rec = record.get('record') or {}
            for qid, ans in rec.items():
                if not str(qid).isdigit():
                    continue
                try:
                    qid_int = int(qid)
                    if qid_int not in exer_id_map:
                        continue
                    if isinstance(ans, dict):
                        score = ans.get('score')
                        if score is None:
                            result = ans.get('result')
                            score = 2 if result else 0 if result is not None else None
                    else:
                        score = ans
                    if score is not None:
                        all_records[sid][qid_int] = float(score)
                except:
                    continue
    print(f"     {fname}: {len(data)}条")

print("   从processed加载:")
for fname in os.listdir(PROCESSED_DIR):
    if not fname.endswith('.json'):
        continue
    with open(os.path.join(PROCESSED_DIR, fname), 'r', encoding='utf-8') as f:
        data = json.load(f)
        added = 0
        for record in data:
            sid = record.get('studentID')
            if not sid:
                continue
            if sid not in all_records:
                all_records[sid] = {}
            
            rec = record.get('record') or {}
            for qid, ans in rec.items():
                if not str(qid).isdigit():
                    continue
                try:
                    qid_int = int(qid)
                    if qid_int not in exer_id_map:
                        continue
                    if qid_int in all_records[sid]:  # 优先用raw中的数据
                        continue
                    if isinstance(ans, dict):
                        score = ans.get('score')
                    else:
                        score = ans
                    if score is not None:
                        all_records[sid][qid_int] = float(score)
                        added += 1
                except:
                    continue
    print(f"     {fname}: 补充{added}条")

print(f"\n5. 转换为训练格式...")
user_id_map = {}
student_records = []

for sid, q_records in tqdm(all_records.items(), desc="转换记录"):
    if not q_records:
        continue
    if sid not in user_id_map:
        user_id_map[sid] = len(user_id_map) + 1
    user_id = user_id_map[sid]
    
    for qid, score in q_records.items():
        exer_id = exer_id_map[qid]
        normalized = 1 if score >= 1 else 0
        
        student_records.append({
            'user_id': user_id,
            'exer_id': exer_id,
            'score': normalized
        })

for rec in tqdm(student_records, desc="添加知识点"):
    exer_id = rec['exer_id']
    for q in questions:
        if exer_id_map.get(q['id']) == exer_id:
            codes = []
            for tag in q.get('tags', []):
                if tag['id'] in knowledge_map:
                    codes.append(knowledge_map[tag['id']])
            rec['knowledge_code'] = list(set(codes))
            break

student_records = [r for r in student_records if r.get('knowledge_code')]
print(f"   有效记录: {len(student_records)}条")
print(f"   学生数: {len(user_id_map)}人")
print(f"   题目数: {len(set(r['exer_id'] for r in student_records))}道")

print(f"\n6. 划分数据集...")
train_ratio = 0.7
val_ratio = 0.15

train_size = int(len(student_records) * train_ratio)
val_size = int(len(student_records) * val_ratio)

train_set = student_records[:train_size]
val_set = student_records[train_size:train_size+val_size]
test_set = student_records[train_size+val_size:]

def format_val_test(records):
    user_logs = {}
    for r in records:
        uid = r['user_id']
        if uid not in user_logs:
            user_logs[uid] = []
        user_logs[uid].append({
            'exer_id': r['exer_id'],
            'score': r['score'],
            'knowledge_code': r['knowledge_code']
        })
    return [{'user_id': k, 'logs': v} for k, v in user_logs.items()]

val_formatted = format_val_test(val_set)
test_formatted = format_val_test(test_set)

print(f"   训练集: {len(train_set)}条, {len(set(r['user_id'] for r in train_set))}学生")
print(f"   验证集: {len(val_formatted)}用户, {len(val_set)}条")
print(f"   测试集: {len(test_formatted)}用户, {len(test_set)}条")

print(f"\n7. 保存数据...")
save_to_json(train_set, TRAIN_SET_FILE)
save_to_json(val_formatted, VAL_SET_FILE)
save_to_json(test_formatted, TEST_SET_FILE)

print("\n" + "=" * 60)
print("完成!")
print("=" * 60)
print(f"\n最终统计:")
print(f"  总记录: {len(student_records)}条")
print(f"  学生: {len(user_id_map)}人")
print(f"  题目: {len(set(r['exer_id'] for r in student_records))}道")
print(f"  知识点: {len(knowledge_map)}个")
scores = [r['score'] for r in student_records]
print(f"  正确率: {scores.count(1)/len(scores)*100:.1f}%")
