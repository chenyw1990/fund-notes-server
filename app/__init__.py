from flask import Flask
from app.config import get_config
from app.extensions import init_extensions, db
import logging
import sys

def configure_logging(app):
    """配置应用日志"""
    # 获取根日志记录器
    root_logger = logging.getLogger()
    
    # 配置日志级别
    if app.debug:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
    
    # 清除现有的handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 添加控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 添加文件handler (可选)
    # file_handler = logging.FileHandler('app.log')
    # file_handler.setFormatter(formatter)
    # root_logger.addHandler(file_handler)
    
    # 设置Flask内部日志器
    app.logger.handlers = []
    for handler in root_logger.handlers:
        app.logger.addHandler(handler)
    
    # 设置其他库的日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    app.logger.info("日志系统已初始化")

def create_app():
    """创建并配置Flask应用"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(get_config())
    
    # 配置日志
    configure_logging(app)
    
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