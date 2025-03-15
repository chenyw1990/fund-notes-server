from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json

from app.extensions import db, redis_client
from app.models import User

# 创建蓝图但不立即导入db和redis_client
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 检查必要字段
    if not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'message': '缺少必要字段'}), 400
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': '用户名已存在'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '邮箱已存在'}), 400
    
    # 创建新用户
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.password = data['password']
    
    db.session.add(user)
    db.session.commit()
    
    # 生成访问令牌
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': '注册成功',
        'access_token': access_token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    # 检查必要字段
    if not all(k in data for k in ('username', 'password')):
        return jsonify({'message': '缺少必要字段'}), 400
    
    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    
    # 验证密码
    if user is None or not user.verify_password(data['password']):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 生成访问令牌
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/wechat_login', methods=['POST'])
def wechat_login():
    """微信小程序登录"""
    data = request.get_json()
    
    # 检查必要字段
    if 'code' not in data:
        return jsonify({'message': '缺少code字段'}), 400
    
    # 获取微信小程序配置
    appid = current_app.config['WECHAT_APPID']
    secret = current_app.config['WECHAT_SECRET']
    
    # 请求微信API获取openid和session_key
    url = f'https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={data["code"]}&grant_type=authorization_code'
    response = requests.get(url)
    
    if response.status_code != 200:
        return jsonify({'message': '微信服务器请求失败'}), 500
    
    wx_data = response.json()
    
    if 'errcode' in wx_data and wx_data['errcode'] != 0:
        return jsonify({'message': f'微信登录失败: {wx_data["errmsg"]}'}), 400
    
    openid = wx_data['openid']
    
    # 查找或创建用户
    user = User.query.filter_by(openid=openid).first()
    
    if user is None:
        # 创建新用户
        username = f'wx_user_{openid[-8:]}'
        user = User(
            openid=openid,
            username=username
        )
        db.session.add(user)
        db.session.commit()
    
    # 生成访问令牌
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取用户资料"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user is None:
        return jsonify({'message': '用户不存在'}), 404
    
    return jsonify(user.to_dict()), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户资料"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user is None:
        return jsonify({'message': '用户不存在'}), 404
    
    data = request.get_json()
    
    # 更新用户资料
    if 'username' in data and data['username'] != user.username:
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': '用户名已存在'}), 400
        user.username = data['username']
    
    if 'email' in data and data['email'] != user.email:
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': '邮箱已存在'}), 400
        user.email = data['email']
    
    if 'avatar' in data:
        user.avatar = data['avatar']
    
    db.session.commit()
    
    return jsonify({
        'message': '资料更新成功',
        'user': user.to_dict()
    }), 200 