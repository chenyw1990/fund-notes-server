import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture
def app():
    """创建并配置一个Flask应用实例用于测试"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test_secret_key',
    })
    
    with app.app_context():
        _db.create_all()
        
    yield app
    
    with app.app_context():
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def db(app):
    """提供数据库会话"""
    with app.app_context():
        yield _db 