import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import db, Config
from app.comments.models import Comment
from app.resources.models import LearningResource, StudentResource

# 创建 Flask 应用
from flask import Flask
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

with app.app_context():
    db.create_all() # 创建所有未存在的表
    print('所有数据库表已检查/创建')

    # 检查并添加字段
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    
    # 更新 comments 表
    comment_columns = [column['name'] for column in inspector.get_columns('comments')]
    
    if 'answer_result' not in comment_columns:
        db.session.execute(text('ALTER TABLE comments ADD COLUMN answer_result TEXT'))
        print('添加 answer_result 字段成功')
    else:
        print('answer_result 字段已存在')
    
    if 'cdm_predictions' not in comment_columns:
        db.session.execute(text('ALTER TABLE comments ADD COLUMN cdm_predictions TEXT'))
        print('添加 cdm_predictions 字段成功')
    else:
        print('cdm_predictions 字段已存在')
    
    if 'student_proficiency' not in comment_columns:
        db.session.execute(text('ALTER TABLE comments ADD COLUMN student_proficiency FLOAT'))
        print('添加 student_proficiency 字段成功')
    else:
        print('student_proficiency 字段已存在')

    # 更新 exam_columns 表
    exam_column_columns = [column['name'] for column in inspector.get_columns('exam_columns')]
    if 'human_knowledge' not in exam_column_columns:
        db.session.execute(text('ALTER TABLE exam_columns ADD COLUMN human_knowledge VARCHAR(200)'))
        print('添加 human_knowledge 字段成功')
    else:
        print('human_knowledge 字段已存在')
    db.session.commit() # Commit the changes

print('数据库更新完成')
