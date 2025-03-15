from flask import Flask
from app.config import get_config
from app.extensions import init_extensions, db

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(get_config())
    
    # 初始化扩展
    init_extensions(app)
    
    # 注册蓝图
    from app.api.auth import auth_bp
    from app.api.notes import notes_bp
    from app.api.funds import funds_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')
    app.register_blueprint(funds_bp, url_prefix='/api/funds')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app 