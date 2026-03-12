import os
import sys

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['OMP_NUM_THREADS'] = '1'

venv_base = os.path.dirname(os.path.abspath(__file__))
torch_lib_path = os.path.join(venv_base, '.venv', 'Lib', 'site-packages', 'torch', 'lib')
if os.path.exists(torch_lib_path):
    os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
    if sys.version_info >= (3, 8):
        os.add_dll_directory(torch_lib_path)

from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# MySQL数据库配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'weijinqi20040811')
DB_NAME = os.getenv('DB_NAME', 'test')

# Neo4j数据库配置
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'weijinqi20040811')

# Flask配置类
class Config:
    # Flask核心配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'weijinqi20040811')  # 用于会话加密的密钥
    DEBUG = True  # 开发环境下启用调试模式
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用SQLAlchemy的修改追踪
    SQLALCHEMY_ECHO = False  # 禁用SQLAlchemy的日志输出
    
    # 上传文件配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))  # 文件上传目录
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 最大上传文件大小：500MB
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif').split(','))  # 允许上传的文件类型
    
    # API配置
    API_PREFIX = '/api'  # API路由前缀
    
    # 百度AI配置
    APP_ID = os.getenv('APP_ID', 'your-app-id')  # 百度AI应用ID
    API_KEY = os.getenv('API_KEY', 'your-api-key')  # 百度AI应用密钥
    SECRET_KEY_BAIDU = os.getenv('SECRET_KEY', 'your-secret-key')  # 百度AI应用密钥
    
    # Tesseract OCR配置
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')  # Tesseract可执行文件路径
    
    # Dify AI配置
    DIFY_API_KEY = os.getenv('DIFY_API_KEY', 'app-rS3rKf3JVLMVdYCnAcsoF141')  # Dify 对话智能体API密钥
    DIFY_COMMENT_API_KEY = os.getenv('DIFY_COMMENT_API_KEY', 'app-Hrra4alKn8tM7nOwlYnQ8WyR')  # Dify 评语生成智能体API密钥

# 初始化数据库
db = SQLAlchemy()
