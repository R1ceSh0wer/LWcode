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


class StudentInfo(db.Model):
    __tablename__ = 'student_info'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(50))
    grade = db.Column(db.String(20))
    student_number = db.Column(db.String(20))
    features = db.Column(db.Text)  # 学生特征描述


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
    question_text = db.Column(db.Text)  # OCR识别出的题目文本（JSON格式: {"1": "题目1...", "2": "题目2..."}）
    question_knowledge = db.Column(db.Text)  # NetKnowledge预测的知识点（JSON格式: {"1": [1,2], "2": [3]}）
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)


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
    answer_result = db.Column(db.Text)  # 教师批改的对错情况
    
    cdm_predictions = db.Column(db.Text)  # NeuralCDM模型预测结果
    student_proficiency = db.Column(db.Float)  # 学生整体掌握度

    column = db.relationship('ExamColumn', backref='comments')
    student = db.relationship('User', backref='comments')


class SummaryComment(db.Model):
    """阶段总结评语"""
    __tablename__ = 'summary_comments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class Conversation(db.Model):
    """智能问答会话"""
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    dify_conversation_id = db.Column(db.String(100))  # Dify返回的会话ID
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 关联学生用户
    title = db.Column(db.String(100))  # 会话标题
    status = db.Column(db.String(20), default='active')  # 会话状态
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联消息
    messages = db.relationship('Message', backref='conversation', lazy='dynamic')


class Message(db.Model):
    """会话消息"""
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'))
    role = db.Column(db.String(10))  # 'user' 或 'assistant'
    content = db.Column(db.Text)  # 消息内容
    dify_message_id = db.Column(db.String(100))  # Dify返回的消息ID
    name = db.Column(db.String(100))  # 消息发送者的用户名
    created_at = db.Column(db.DateTime, default=datetime.now)
