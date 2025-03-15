from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建应用
app = Flask(__name__)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
    os.environ.get('DB_USER', 'fund_user'),
    os.environ.get('DB_PASSWORD', 'fund_password'),
    os.environ.get('DB_HOST', 'localhost'),
    os.environ.get('DB_PORT', '3306'),
    os.environ.get('DB_NAME', 'fund_notes')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 配置JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret_key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# 初始化扩展
db = SQLAlchemy(app)
jwt = JWTManager(app)

# 定义模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'created_at': self.created_at.isoformat()
        }

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'user_id': self.user_id,
            'fund_id': self.fund_id,
            'created_at': self.created_at.isoformat()
        }

# 创建数据库表
with app.app_context():
    db.create_all()

# 添加一些示例数据
def add_sample_data():
    with app.app_context():
        # 检查是否已有数据
        if User.query.count() == 0:
            # 添加用户
            user = User(username='test_user', email='test@example.com')
            user.password = 'password123'
            db.session.add(user)
            
            # 添加基金
            funds = [
                Fund(code='000001', name='中国平安', type='股票'),
                Fund(code='000002', name='华夏成长', type='股票'),
                Fund(code='000003', name='易方达消费行业', type='股票'),
                Fund(code='000004', name='嘉实沪深300', type='股票'),
                Fund(code='000005', name='华夏沪深300', type='股票')
            ]
            db.session.add_all(funds)
            
            # 添加笔记
            notes = [
                Note(title='中国平安股票分析', content='中国平安是中国最大的保险公司之一，具有强大的市场竞争力。', user_id=1, fund_id=1),
                Note(title='华夏成长股票分析', content='华夏成长是一只以成长为主题的股票基金，适合长期投资。', user_id=1, fund_id=2),
                Note(title='易方达消费行业股票分析', content='易方达消费行业股票基金主要投资于消费行业的股票，适合长期投资。', user_id=1, fund_id=3),
                Note(title='嘉实沪深300股票分析', content='嘉实沪深300指数基金跟踪沪深300指数，适合长期投资。', user_id=1, fund_id=4),
                Note(title='华夏沪深300股票分析', content='华夏沪深300指数基金跟踪沪深300指数，适合长期投资。', user_id=1, fund_id=5)
            ]
            db.session.add_all(notes)
            
            db.session.commit()

add_sample_data() 