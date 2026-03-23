from datetime import datetime
from config import db

class LearningResource(db.Model):
    __tablename__ = 'learning_resources'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False) # 文档, 视频, 练习题, PPT, 其它
    file_path = db.Column(db.String(255), nullable=False) # 资源在后端存储的路径
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    teacher = db.relationship('User', backref='uploaded_resources')

    def __repr__(self):
        return f'<LearningResource {self.name}>'

class StudentResource(db.Model):
    __tablename__ = 'student_resources'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('learning_resources.id'), nullable=False)
    distributed_at = db.Column(db.DateTime, default=datetime.now)
    read_status = db.Column(db.Boolean, default=False) # 学生是否已阅读

    student = db.relationship('User', backref='received_resources')
    resource = db.relationship('LearningResource', backref='distributed_to_students')

    def __repr__(self):
        return f'<StudentResource student_id={self.student_id} resource_id={self.resource_id}>'
