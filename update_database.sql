-- 创建模型存档表
CREATE TABLE IF NOT EXISTS model_archives (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,  -- 存档名称
    word_emb_path VARCHAR(200),  -- 词嵌入文件路径（存档名+W）
    diagnosis_model_path VARCHAR(200),  -- 诊断模型文件路径（存档名+N）
    knowledge_mapping_path VARCHAR(200),  -- 知识点映射文件路径
    teacher_id INTEGER NOT NULL,  -- 创建者 ID
    status VARCHAR(20) DEFAULT 'pending',  -- 状态：pending, training, completed, failed
    training_log TEXT,  -- 训练日志
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

-- 为 exam_columns 表添加 archive_id 字段
ALTER TABLE exam_columns ADD COLUMN archive_id INTEGER;

-- 添加外键约束
ALTER TABLE exam_columns ADD CONSTRAINT fk_exam_columns_archive 
    FOREIGN KEY (archive_id) REFERENCES model_archives(id);