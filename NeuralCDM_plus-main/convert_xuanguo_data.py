import json
import os
import re
from tqdm import tqdm
import jieba

# 设置文件路径
DATA_DIR = 'data/玄高数据汇总'
QUESTION_FILE = os.path.join(DATA_DIR, 'question/all-questions.json')
SKILL_TREE_FILE = os.path.join(DATA_DIR, 'question/skill-tag-tree.json')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

# 输出文件路径
OUTPUT_DIR = 'data'
NET_KNOWLEDGE_TRAIN_FILE = os.path.join(OUTPUT_DIR, 'net_knowledge_train.json')
NET_KNOWLEDGE_PRED_FILE = os.path.join(OUTPUT_DIR, 'net_knowledge_pred.json')
TRAIN_SET_FILE = os.path.join(OUTPUT_DIR, 'train_set.json')
VAL_SET_FILE = os.path.join(OUTPUT_DIR, 'val_set.json')
TEST_SET_FILE = os.path.join(OUTPUT_DIR, 'test_set.json')

# 加载数据
def load_data():
    # 加载题目数据
    with open(QUESTION_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # 加载知识点树
    with open(SKILL_TREE_FILE, 'r', encoding='utf-8') as f:
        skill_tree = json.load(f)
    
    # 加载学生答题数据
    student_data = []
    for filename in os.listdir(PROCESSED_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(PROCESSED_DIR, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                student_data.extend(data)
    
    return questions, skill_tree, student_data

# 提取所有知识点并建立映射
def extract_knowledge_points(skill_tree):
    knowledge_points = {}
    
    # 排除的关键词列表
    exclude_keywords = ['未分类', '其他', '默认', '通用', '分类', '标签', '专题']
    
    def traverse(node, level=0):
        # 检查是否包含排除关键词
        tag_name = node['tagName']
        if any(keyword in tag_name for keyword in exclude_keywords):
            return
        
        # 保留知识点
        knowledge_points[node['id']] = tag_name
        if 'children' in node:
            for child in node['children']:
                traverse(child, level + 1)
    
    for root in skill_tree:
        traverse(root)
    
    # 去重相似知识点
    # 1. 先按名称去重，保留第一个出现的ID
    name_to_ids = {}
    for k_id, k_name in knowledge_points.items():
        if k_name not in name_to_ids:
            name_to_ids[k_name] = []
        name_to_ids[k_name].append(k_id)
    
    # 过滤掉重复名称的知识点
    unique_by_name = {}
    for k_name, ids in name_to_ids.items():
        unique_by_name[ids[0]] = k_name
    
    # 2. 处理相似知识点（如"自定义函数及调用"和"自定义函数的调用"）
    # 创建标准化名称的映射
    normalized_points = {}
    
    def normalize_name(name):
        # 标准化处理：
        # 1. 统一括号格式（将中文括号转换为英文括号）
        normalized = name.replace('（', '(').replace('）', ')')
        # 2. 移除冗余词汇
        redundant_patterns = ['的', '及', '与', '和', '了', '是']
        for pattern in redundant_patterns:
            normalized = normalized.replace(pattern, '')
        # 3. 移除空格
        normalized = normalized.replace(' ', '')
        return normalized
    
    for k_id, k_name in unique_by_name.items():
        normalized = normalize_name(k_name)
        # 检查是否已存在相似知识点
        found = False
        for existing_id, existing_name in normalized_points.items():
            if normalize_name(existing_name) == normalized:
                found = True
                break
        if not found:
            normalized_points[k_id] = k_name
    
    # 使用去重后的知识点
    knowledge_points = normalized_points
    
    # 创建连续的知识点编码映射
    knowledge_map = {}
    for idx, (k_id, k_name) in enumerate(knowledge_points.items(), 1):
        knowledge_map[k_id] = idx
    
    # 保存知识点映射到文本文件
    knowledge_mapping_file = os.path.join(OUTPUT_DIR, 'knowledge_mapping.txt')
    with open(knowledge_mapping_file, 'w', encoding='utf-8') as f:
        # 按编码排序
        sorted_knowledge = sorted(knowledge_map.items(), key=lambda x: x[1])
        for k_id, code in sorted_knowledge:
            f.write(f"{code}：{knowledge_points[k_id]}\n")
    print(f"知识点映射已保存到 {knowledge_mapping_file}")
    
    print(f"共提取到 {len(knowledge_map)} 个知识点")
    return knowledge_map

# 清理和分词题目内容
def clean_and_segment_text(text):
    # 移除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', text)
    # 移除特殊符号
    clean_text = re.sub(r'[^一-龥a-zA-Z0-9]', ' ', clean_text)
    # 分词
    words = jieba.lcut(clean_text)
    # 过滤空字符串
    words = [word for word in words if word.strip()]
    return words

# 转换题目数据为net_knowledge格式
def convert_to_net_knowledge(questions, knowledge_map):
    net_knowledge_data = []
    exer_id_map = {}
    
    for idx, question in tqdm(enumerate(questions), desc="转换题目数据"):
        # 获取题目ID
        q_id = question['id']
        
        # 获取题目内容
        if not question.get('questionDetail') or not question['questionDetail'].get('content'):
            continue
        content = question['questionDetail']['content']
        
        # 分词
        segmented_text = clean_and_segment_text(content)
        
        # 获取知识点
        knowledge_codes = []
        for tag in question.get('tags', []):
            tag_id = tag['id']
            if tag_id in knowledge_map:
                knowledge_codes.append(knowledge_map[tag_id])
        
        # 去重
        knowledge_codes = list(set(knowledge_codes))
        
        # 如果没有知识点，跳过
        if not knowledge_codes:
            continue
        
        # 添加到数据
        net_knowledge_data.append({
            'exer_id': idx + 1,
            'text': segmented_text,
            'knowledge_code': knowledge_codes
        })
        
        # 建立题目ID映射
        exer_id_map[q_id] = idx + 1
    
    print(f"共转换 {len(net_knowledge_data)} 道题目")
    return net_knowledge_data, exer_id_map

# 转换学生答题数据为train/val/test格式
def convert_to_student_data(student_data, exer_id_map, knowledge_map, questions):
    user_id_map = {}
    student_records = []
    
    for student in tqdm(student_data, desc="转换学生答题数据"):
        # 获取学生ID
        student_id = student['studentID']
        if student_id not in user_id_map:
            user_id_map[student_id] = len(user_id_map) + 1  # user_id从1开始
        user_id = user_id_map[student_id]
        
        # 获取答题记录
        record = student.get('record', {})
        if record is None:
            continue
        for q_id_str, answer_data in record.items():
            # 过滤掉非数字的题目ID
            if not q_id_str.isdigit():
                continue
            try:
                q_id = int(q_id_str)
                if q_id in exer_id_map:
                    exer_id = exer_id_map[q_id]
                    # 获取score值（answer_data可能是一个字典或直接是score值）
                    if isinstance(answer_data, dict):
                        score = answer_data.get('score', 0)
                    else:
                        score = answer_data
                    # 将score从0/2转换为0/1
                    normalized_score = 1 if score == 2 else 0
                    student_records.append({
                        'user_id': user_id,
                        'exer_id': exer_id,
                        'score': normalized_score
                    })
            except (ValueError, TypeError):
                continue
    
    print(f"共转换 {len(student_records)} 条学生答题记录")
    print(f"共有 {len(user_id_map)} 个学生")
    
    # 添加知识点信息
    for record in tqdm(student_records, desc="添加知识点信息"):
        exer_id = record['exer_id']
        # 找到对应的知识点
        for question in questions:
            q_id = question['id']
            if q_id in exer_id_map and exer_id_map[q_id] == exer_id:
                knowledge_codes = []
                for tag in question.get('tags', []):
                    tag_id = tag['id']
                    if tag_id in knowledge_map:
                        knowledge_codes.append(knowledge_map[tag_id])
                record['knowledge_code'] = list(set(knowledge_codes))
                break
    
    # 过滤没有知识点的记录
    student_records = [record for record in student_records if 'knowledge_code' in record and record['knowledge_code']]
    
    print(f"过滤后剩余 {len(student_records)} 条学生答题记录")
    
    # 划分数据集
    train_ratio = 0.7
    val_ratio = 0.15
    
    train_size = int(len(student_records) * train_ratio)
    val_size = int(len(student_records) * val_ratio)
    
    train_set = student_records[:train_size]
    val_set = student_records[train_size:train_size+val_size]
    test_set = student_records[train_size+val_size:]
    
    # 转换val_set和test_set为main.py期望的格式（包含user_id和logs数组）
    def convert_to_val_test_format(records):
        user_logs = {}
        for record in records:
            user_id = record['user_id']
            if user_id not in user_logs:
                user_logs[user_id] = []
            user_logs[user_id].append({
                'exer_id': record['exer_id'],
                'score': record['score'],
                'knowledge_code': record['knowledge_code']
            })
        
        formatted_data = []
        for user_id, logs in user_logs.items():
            formatted_data.append({
                'user_id': user_id,
                'logs': logs
            })
        return formatted_data
    
    val_set_formatted = convert_to_val_test_format(val_set)
    test_set_formatted = convert_to_val_test_format(test_set)
    
    print(f"训练集: {len(train_set)} 条")
    print(f"验证集: {len(val_set_formatted)} 个用户")
    print(f"测试集: {len(test_set_formatted)} 个用户")
    
    return train_set, val_set_formatted, test_set_formatted

# 保存数据到JSON文件
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {filename}")

if __name__ == '__main__':
    print("开始转换玄高数据到NeuralCDM_plus格式...")
    
    # 1. 加载数据
    print("加载数据...")
    questions, skill_tree, student_data = load_data()
    
    # 2. 提取知识点映射
    print("提取知识点映射...")
    knowledge_map = extract_knowledge_points(skill_tree)
    
    # 3. 转换为net_knowledge格式
    print("转换为net_knowledge格式...")
    net_knowledge_data, exer_id_map = convert_to_net_knowledge(questions, knowledge_map)
    
    # 4. 划分训练和预测数据集
    print("划分训练和预测数据集...")
    train_size = int(len(net_knowledge_data) * 0.8)
    net_knowledge_train = net_knowledge_data[:train_size]
    net_knowledge_pred = net_knowledge_data[train_size:]
    
    # 5. 保存net_knowledge数据
    print("保存net_knowledge数据...")
    save_to_json(net_knowledge_train, NET_KNOWLEDGE_TRAIN_FILE)
    save_to_json(net_knowledge_pred, NET_KNOWLEDGE_PRED_FILE)
    
    # 6. 转换为学生答题数据格式
    print("转换为学生答题数据格式...")
    train_set, val_set, test_set = convert_to_student_data(student_data, exer_id_map, knowledge_map, questions)
    
    # 7. 保存学生答题数据
    print("保存学生答题数据...")
    save_to_json(train_set, TRAIN_SET_FILE)
    save_to_json(val_set, VAL_SET_FILE)
    save_to_json(test_set, TEST_SET_FILE)
    
    print("转换完成！")
    print(f"知识点数量: {len(knowledge_map)}")
    print(f"题目数量: {len(exer_id_map)}")
    print(f"学生数量: {len(set(record['user_id'] for record in train_set))}")
