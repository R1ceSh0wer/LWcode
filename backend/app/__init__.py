import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from config import Config, db


def create_app(config_class=Config):
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_class)
    
    # 初始化数据库
    db.init_app(app)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册 uploads 文件夹的静态文件服务
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        return send_from_directory(upload_folder, filename)
    
    # 注册蓝图
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.users import bp as users_bp
    app.register_blueprint(users_bp)
    
    from app.students import bp as students_bp
    app.register_blueprint(students_bp)
    
    from app.columns import bp as columns_bp
    app.register_blueprint(columns_bp)
    
    from app.comments import bp as comments_bp
    app.register_blueprint(comments_bp)
    
    from app.conversations import bp as conversations_bp
    app.register_blueprint(conversations_bp)
    
    from app.files import bp as files_bp
    app.register_blueprint(files_bp)
    
    from app.neo4j import bp as neo4j_bp
    app.register_blueprint(neo4j_bp)
    
    from app.archives import bp as archives_bp
    app.register_blueprint(archives_bp)

    from app.resources.routes import bp as resources_bp
    app.register_blueprint(resources_bp)
    
    return app
