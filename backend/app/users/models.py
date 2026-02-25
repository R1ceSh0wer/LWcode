from datetime import datetime
from config import db


class StudentInfo(db.Model):
    __tablename__ = 'student_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(50))
    grade = db.Column(db.String(20))
    student_number = db.Column(db.String(20))
    features = db.Column(db.Text)  # 学生特征描述
