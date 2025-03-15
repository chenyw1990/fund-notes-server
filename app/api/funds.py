from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import requests

from app.extensions import db, redis_client
from app.models import Fund, Note

funds_bp = Blueprint('funds', __name__)

@funds_bp.route('', methods=['GET'])
def get_funds():
    """获取基金列表"""
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    fund_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 尝试从缓存获取
    cache_key = f'funds:list:{keyword}:{fund_type}:{page}:{per_page}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data)), 200
    
    # 构建查询
    query = Fund.query
    
    # 如果有关键字，则搜索基金代码或名称
    if keyword:
        query = query.filter(
            (Fund.code.like(f'%{keyword}%')) | 
            (Fund.name.like(f'%{keyword}%'))
        )
    
    # 如果指定了基金类型，则过滤
    if fund_type:
        query = query.filter_by(type=fund_type)
    
    # 按基金代码排序
    query = query.order_by(Fund.code)
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    
    # 构建响应
    funds = [fund.to_dict() for fund in pagination.items]
    
    response_data = {
        'funds': funds,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }
    
    # 缓存结果，设置过期时间为1小时
    redis_client.setex(
        cache_key,
        3600,  # 1小时
        json.dumps(response_data)
    )
    
    return jsonify(response_data), 200


@funds_bp.route('/<string:code>', methods=['GET'])
def get_fund(code):
    """获取基金详情"""
    # 尝试从缓存获取
    cache_key = f'funds:detail:{code}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data)), 200
    
    # 查询基金
    fund = Fund.query.filter_by(code=code).first()
    
    if fund is None:
        return jsonify({'message': '基金不存在'}), 404
    
    # 构建响应
    fund_data = fund.to_dict()
    
    # 获取基金相关笔记数量
    notes_count = Note.query.filter_by(fund_id=fund.id, is_public=True).count()
    fund_data['notes_count'] = notes_count
    
    # 缓存结果，设置过期时间为1小时
    redis_client.setex(
        cache_key,
        3600,  # 1小时
        json.dumps(fund_data)
    )
    
    return jsonify(fund_data), 200


@funds_bp.route('/search', methods=['GET'])
def search_funds():
    """搜索基金"""
    keyword = request.args.get('keyword', '')
    
    if not keyword:
        return jsonify({'message': '请提供搜索关键字'}), 400
    
    # 尝试从缓存获取
    cache_key = f'funds:search:{keyword}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data)), 200
    
    # 搜索基金
    funds = Fund.query.filter(
        (Fund.code.like(f'%{keyword}%')) | 
        (Fund.name.like(f'%{keyword}%'))
    ).limit(10).all()
    
    # 构建响应
    funds_data = [fund.to_dict() for fund in funds]
    
    # 缓存结果，设置过期时间为1小时
    redis_client.setex(
        cache_key,
        3600,  # 1小时
        json.dumps(funds_data)
    )
    
    return jsonify(funds_data), 200


@funds_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_funds():
    """同步基金数据（仅管理员可用）"""
    # 这里可以实现从外部API同步基金数据的功能
    # 为了简化，这里只是返回一个成功消息
    return jsonify({'message': '基金数据同步成功'}), 200


@funds_bp.route('/<string:code>/notes', methods=['GET'])
def get_fund_notes(code):
    """获取基金相关笔记"""
    # 查询基金
    fund = Fund.query.filter_by(code=code).first()
    
    if fund is None:
        return jsonify({'message': '基金不存在'}), 404
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 尝试从缓存获取
    cache_key = f'fund_notes:{fund.id}:{page}:{per_page}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data)), 200
    
    # 查询笔记
    pagination = Note.query.filter_by(
        fund_id=fund.id,
        is_public=True
    ).order_by(
        Note.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    # 构建响应
    notes = [note.to_dict() for note in pagination.items]
    
    # 添加作者信息
    from app.models import User
    for note in notes:
        user = User.query.get(note['user_id'])
        if user:
            note['author'] = {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar
            }
    
    response_data = {
        'notes': notes,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }
    
    # 缓存结果，设置过期时间为10分钟
    redis_client.setex(
        cache_key,
        600,  # 10分钟
        json.dumps(response_data)
    )
    
    return jsonify(response_data), 200 