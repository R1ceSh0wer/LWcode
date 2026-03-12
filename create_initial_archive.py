import os
import shutil
import json
from datetime import datetime

def create_initial_archive():
    """
    打包现有文件为初始存档
    """
    print("开始创建初始存档...")
    
    # 创建存档目录
    archive_name = f"initial_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    archive_dir = os.path.join("backend", "uploads", "archives", archive_name)
    os.makedirs(archive_dir, exist_ok=True)
    
    print(f"创建存档目录: {archive_dir}")
    
    # 1. 复制知识点映射文件
    knowledge_mapping_src = os.path.join("NeuralCDM_plus-main", "data", "knowledge_mapping.txt")
    knowledge_mapping_dst = os.path.join(archive_dir, "knowledge_mapping.txt")
    
    if os.path.exists(knowledge_mapping_src):
        shutil.copy2(knowledge_mapping_src, knowledge_mapping_dst)
        print(f"复制知识点映射文件: {knowledge_mapping_src} -> {knowledge_mapping_dst}")
    else:
        print(f"警告: 知识点映射文件不存在: {knowledge_mapping_src}")
        # 创建一个示例知识点映射文件
        with open(knowledge_mapping_dst, 'w', encoding='utf-8') as f:
            f.write("1：知识点1\n2：知识点2\n3：知识点3\n")
        print(f"创建示例知识点映射文件: {knowledge_mapping_dst}")
    
    # 2. 复制一个最佳模型文件（假设epoch28是最佳模型）
    best_model_src = os.path.join("NeuralCDM_plus-main", "model", "model_epoch28")
    best_model_dst = os.path.join(archive_dir, f"{archive_name}N")
    
    if os.path.exists(best_model_src):
        shutil.copy2(best_model_src, best_model_dst)
        print(f"复制诊断模型: {best_model_src} -> {best_model_dst}")
    else:
        print(f"警告: 诊断模型不存在: {best_model_src}")
        # 创建一个示例模型文件
        with open(best_model_dst, 'w') as f:
            f.write("# 示例模型文件\n")
        print(f"创建示例诊断模型: {best_model_dst}")
    
    # 3. 复制词嵌入文件
    word_emb_src = os.path.join("NeuralCDM_plus-main", "result", "word2vec.model")
    word_emb_dst = os.path.join(archive_dir, f"{archive_name}W")
    
    if os.path.exists(word_emb_src):
        shutil.copy2(word_emb_src, word_emb_dst)
        print(f"复制词嵌入文件: {word_emb_src} -> {word_emb_dst}")
    else:
        print(f"警告: 词嵌入文件不存在: {word_emb_src}")
        # 创建一个示例词嵌入文件
        with open(word_emb_dst, 'w') as f:
            f.write("# 示例词嵌入文件\n")
        print(f"创建示例词嵌入文件: {word_emb_dst}")
    
    # 4. 复制训练数据文件
    data_dir = os.path.join("NeuralCDM_plus-main", "data")
    for filename in os.listdir(data_dir):
        if filename.endswith(('.json', '.txt')) and any(keyword in filename.lower() for keyword in ['train', 'test', 'val']):
            src_file = os.path.join(data_dir, filename)
            dst_file = os.path.join(archive_dir, filename)
            shutil.copy2(src_file, dst_file)
            print(f"复制训练数据: {src_file} -> {dst_file}")
    
    # 5. 创建存档信息文件
    archive_info = {
        "name": archive_name,
        "description": "初始模型存档",
        "created_at": datetime.now().isoformat(),
        "source_files": [
            "knowledge_mapping.txt",
            f"{archive_name}N",  # 诊断模型
            f"{archive_name}W",  # 词嵌入
        ],
        "status": "completed"
    }
    
    info_file = os.path.join(archive_dir, "archive_info.json")
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump(archive_info, f, ensure_ascii=False, indent=2)
    
    print(f"创建存档信息文件: {info_file}")
    print(f"\n初始存档创建完成: {archive_dir}")
    print(f"存档名称: {archive_name}")
    print(f"存档路径: {os.path.abspath(archive_dir)}")
    
    return archive_name, archive_dir

if __name__ == "__main__":
    create_initial_archive()