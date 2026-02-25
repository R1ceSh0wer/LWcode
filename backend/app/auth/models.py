from datetime import datetime
from config import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'teacher' or 'student'
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关联学生信息（如果是学生）
    student_info = db.relationship('StudentInfo', backref='user', uselist=False)
