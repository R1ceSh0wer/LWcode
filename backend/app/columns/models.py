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
    question_text = db.Column(db.Text)  # OCR识别出的题目
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
