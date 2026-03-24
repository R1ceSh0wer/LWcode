from datetime import datetime
from config import db


class ExamColumn(db.Model):
    """试题专栏"""
    __tablename__ = 'exam_columns'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # 支持最多6张图片
    question_image_path1 = db.Column(db.String(200))  # 试题截图1
    question_image_path2 = db.Column(db.String(200))  # 试题截图2
    question_image_path3 = db.Column(db.String(200))  # 试题截图3
    question_image_path4 = db.Column(db.String(200))  # 试题截图4
    question_image_path5 = db.Column(db.String(200))  # 试题截图5
    question_image_path6 = db.Column(db.String(200))  # 试题截图6
    question_text = db.Column(db.Text)  # OCR 识别出的题目
    question_knowledge = db.Column(db.Text)  # 知识点映射（JSON 格式）
    archive_id = db.Column(db.Integer, db.ForeignKey('model_archives.id'))  # 关联的存档 ID
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    human_knowledge = db.Column(db.String(200)) # 人工标注知识点文件路径
    created_at = db.Column(db.DateTime, default=datetime.now)


class TeacherKnowledgeGraph(db.Model):
    """教师端知识图谱构建数据"""
    __tablename__ = 'teacher_knowledge_graphs'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey('exam_columns.id'), nullable=False, unique=True)
    nodes_json = db.Column(db.Text, nullable=False, default='[]')
    edges_json = db.Column(db.Text, nullable=False, default='[]')
    partitions_json = db.Column(db.Text, nullable=False, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
