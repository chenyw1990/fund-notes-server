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
    from app.api.purchases import purchases_bp
    from app.api.fund_values import fund_values_bp
    from app.web import web_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(notes_bp, url_prefix='/api/notes')
    app.register_blueprint(funds_bp, url_prefix='/api/funds')
    app.register_blueprint(purchases_bp, url_prefix='/api/purchases')
    app.register_blueprint(fund_values_bp, url_prefix='/api/fund-values')
    app.register_blueprint(web_bp, url_prefix='')
    
    # 添加模板函数
    from app.web.template_utils import register_template_utils
    register_template_utils(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 在非调试模式下启动定时任务
    if not app.debug:
        from app.tasks.scheduled_tasks import setup_scheduled_tasks
        setup_scheduled_tasks()
    
    @app.teardown_appcontext
    def shutdown_scheduler(exception=None):
        """在应用关闭时关闭调度器"""
        if not app.debug:
            from app.tasks.scheduled_tasks import shutdown_scheduler
            shutdown_scheduler()
    
    return app 