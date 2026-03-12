from datetime import datetime
from config import db


class ModelArchive(db.Model):
    """模型存档"""
    __tablename__ = 'model_archives'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 存档名称
    word_emb_path = db.Column(db.String(200))  # 词嵌入文件路径（存档名+W）
    diagnosis_model_path = db.Column(db.String(200))  # 诊断模型文件路径（存档名+N）
    knowledge_mapping_path = db.Column(db.String(200))  # 知识点映射文件路径
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 创建者 ID
    status = db.Column(db.String(20), default='pending')  # 状态：pending, training, completed, failed
    training_log = db.Column(db.Text)  # 训练日志
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关联创建者
    teacher = db.relationship('User', backref='model_archives')
    # 关联使用该存档的专栏
    columns = db.relationship('ExamColumn', backref='archive', lazy='dynamic')
