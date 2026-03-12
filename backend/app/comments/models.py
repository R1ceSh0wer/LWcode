from datetime import datetime
from config import db


class Comment(db.Model):
    """单次评语"""
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    column_id = db.Column(db.Integer, db.ForeignKey('exam_columns.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 支持最多6张图片
    answer_image_path1 = db.Column(db.String(200))  # 学生答题截图1
    answer_image_path2 = db.Column(db.String(200))  # 学生答题截图2
    answer_image_path3 = db.Column(db.String(200))  # 学生答题截图3
    answer_image_path4 = db.Column(db.String(200))  # 学生答题截图4
    answer_image_path5 = db.Column(db.String(200))  # 学生答题截图5
    answer_image_path6 = db.Column(db.String(200))  # 学生答题截图6


    content = db.Column(db.Text)  # AI生成的评语
    style = db.Column(db.String(50))  # 评语风格（严厉、鼓励、幽默等）

    feedback = db.Column(db.Text)  # 学生反馈
    feedback_time = db.Column(db.DateTime)

    is_regenerated = db.Column(db.Boolean, default=False)  # 是否根据反馈重新生成过
    created_at = db.Column(db.DateTime, default=datetime.now)
    addition = db.Column(db.Text)  # 附加评语

    answer_result = db.Column(db.Text)  # 答案对错结果
    cdm_predictions = db.Column(db.Text)  # 神经认知诊断模型预测结果
    student_proficiency = db.Column(db.Float)  # 学生能力水平

    column = db.relationship('ExamColumn', backref='comments')
    student = db.relationship('User', backref='comments')


class SummaryComment(db.Model):
    """阶段总结评语"""
    __tablename__ = 'summary_comments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
