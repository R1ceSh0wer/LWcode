import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import db, Config
from app.comments.models import Comment

# 创建 Flask 应用
from flask import Flask
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

with app.app_context():
    # 检查并添加字段
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    columns = [column['name'] for column in inspector.get_columns('comments')]
    
    if 'answer_result' not in columns:
        db.engine.execute('ALTER TABLE comments ADD COLUMN answer_result TEXT')
        print('添加 answer_result 字段成功')
    else:
        print('answer_result 字段已存在')
    
    if 'cdm_predictions' not in columns:
        db.engine.execute('ALTER TABLE comments ADD COLUMN cdm_predictions TEXT')
        print('添加 cdm_predictions 字段成功')
    else:
        print('cdm_predictions 字段已存在')
    
    if 'student_proficiency' not in columns:
        db.engine.execute('ALTER TABLE comments ADD COLUMN student_proficiency FLOAT')
        print('添加 student_proficiency 字段成功')
    else:
        print('student_proficiency 字段已存在')

print('数据库更新完成')
