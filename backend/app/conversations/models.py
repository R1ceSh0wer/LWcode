from datetime import datetime
from config import db


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
