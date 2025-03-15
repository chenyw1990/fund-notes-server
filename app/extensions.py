from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import redis

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
redis_client = None

def init_extensions(app):
    """初始化所有扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    
    # 初始化Redis
    global redis_client
    redis_client = redis.from_url(app.config['REDIS_URL']) 