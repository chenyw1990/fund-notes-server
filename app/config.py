import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        os.environ.get('DB_USER', 'root'),
        os.environ.get('DB_PASSWORD', 'password'),
        os.environ.get('DB_HOST', 'localhost'),
        os.environ.get('DB_PORT', '3306'),
        os.environ.get('DB_NAME', 'fund_notes')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis配置
    REDIS_URL = 'redis://{}:{}/{}'.format(
        os.environ.get('REDIS_HOST', 'localhost'),
        os.environ.get('REDIS_PORT', '6379'),
        os.environ.get('REDIS_DB', '0')
    )
    if os.environ.get('REDIS_PASSWORD'):
        REDIS_URL = 'redis://:{password}@{host}:{port}/{db}'.format(
            password=os.environ.get('REDIS_PASSWORD'),
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=os.environ.get('REDIS_PORT', '6379'),
            db=os.environ.get('REDIS_DB', '0')
        )
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt_dev_key')
    # 从环境变量获取JWT过期时间，去掉可能的注释部分
    jwt_expires_str = os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '86400')
    if '#' in jwt_expires_str:
        jwt_expires_str = jwt_expires_str.split('#')[0].strip()
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(jwt_expires_str))
    
    # 微信小程序配置
    WECHAT_APPID = os.environ.get('WECHAT_APPID', '')
    WECHAT_SECRET = os.environ.get('WECHAT_SECRET', '')


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# 获取当前配置
def get_config():
    config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, config['default']) 