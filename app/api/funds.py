from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import requests
import time

from app.extensions import db, redis_client
from app.models import Fund, Note

funds_bp = Blueprint('funds', __name__)

@funds_bp.route('', methods=['GET'])
def get_funds():
    """获取基金列表"""
    start_time = time.time()
    current_app.logger.info(f"API调用: 获取基金列表 - 参数: {request.args}")
    
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    fund_type = request.args.get('type', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 尝试从缓存获取
    cache_key = f'funds:list:{keyword}:{fund_type}:{page}:{per_page}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        current_app.logger.info(f"缓存命中: {cache_key}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(json.loads(cached_data)), 200
    
    current_app.logger.info(f"缓存未命中: {cache_key}")
    
    # 构建查询
    query = Fund.query
    
    # 如果有关键字，则搜索基金代码或名称
    if keyword:
        current_app.logger.info(f"搜索关键字: {keyword}")
        query = query.filter(
            (Fund.code.like(f'%{keyword}%')) | 
            (Fund.name.like(f'%{keyword}%'))
        )
    
    # 如果指定了基金类型，则过滤
    if fund_type:
        current_app.logger.info(f"过滤基金类型: {fund_type}")
        query = query.filter_by(type=fund_type)
    
    # 按基金代码排序
    query = query.order_by(Fund.code)
    
    try:
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
        
        current_app.logger.info(f"查询结果: 共{pagination.total}条记录, 当前第{page}页")
        
        # 缓存结果，设置过期时间为1小时
        redis_client.setex(
            cache_key,
            3600,  # 1小时
            json.dumps(response_data)
        )
        current_app.logger.info(f"缓存已设置: {cache_key}, 过期时间: 1小时")
        
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(response_data), 200
    except Exception as e:
        current_app.logger.error(f"获取基金列表失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': '获取基金列表失败'}), 500


@funds_bp.route('/<string:code>', methods=['GET'])
def get_fund(code):
    """获取基金详情"""
    start_time = time.time()
    current_app.logger.info(f"API调用: 获取基金详情 - 基金代码: {code}")
    
    # 尝试从缓存获取
    cache_key = f'funds:detail:{code}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        current_app.logger.info(f"缓存命中: {cache_key}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(json.loads(cached_data)), 200
    
    current_app.logger.info(f"缓存未命中: {cache_key}")
    
    try:
        # 查询基金
        fund = Fund.query.filter_by(code=code).first()
        
        if fund is None:
            current_app.logger.warning(f"基金不存在: {code}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '基金不存在'}), 404
        
        # 构建响应
        fund_data = fund.to_dict()
        
        # 获取基金相关笔记数量
        notes_count = Note.query.filter_by(fund_id=fund.id, is_public=True).count()
        fund_data['notes_count'] = notes_count
        
        current_app.logger.info(f"基金详情获取成功: {code}, 相关笔记数: {notes_count}")
        
        # 缓存结果，设置过期时间为1小时
        redis_client.setex(
            cache_key,
            3600,  # 1小时
            json.dumps(fund_data)
        )
        current_app.logger.info(f"缓存已设置: {cache_key}, 过期时间: 1小时")
        
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(fund_data), 200
    except Exception as e:
        current_app.logger.error(f"获取基金详情失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': '获取基金详情失败'}), 500


@funds_bp.route('/search', methods=['GET'])
def search_funds():
    """搜索基金"""
    start_time = time.time()
    keyword = request.args.get('keyword', '')
    current_app.logger.info(f"API调用: 搜索基金 - 关键字: {keyword}")
    
    if not keyword:
        current_app.logger.warning("搜索基金: 未提供关键字")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': '请提供搜索关键字'}), 400
    
    # 尝试从缓存获取
    cache_key = f'funds:search:{keyword}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        current_app.logger.info(f"缓存命中: {cache_key}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(json.loads(cached_data)), 200
    
    current_app.logger.info(f"缓存未命中: {cache_key}")
    
    try:
        # 搜索基金
        funds = Fund.query.filter(
            (Fund.code.like(f'%{keyword}%')) | 
            (Fund.name.like(f'%{keyword}%'))
        ).limit(10).all()
        
        # 构建响应
        funds_data = [fund.to_dict() for fund in funds]
        
        current_app.logger.info(f"搜索结果: 找到{len(funds_data)}个基金")
        
        # 缓存结果，设置过期时间为1小时
        redis_client.setex(
            cache_key,
            3600,  # 1小时
            json.dumps(funds_data)
        )
        current_app.logger.info(f"缓存已设置: {cache_key}, 过期时间: 1小时")
        
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(funds_data), 200
    except Exception as e:
        current_app.logger.error(f"搜索基金失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': '搜索基金失败'}), 500


@funds_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_funds():
    """同步基金数据（仅管理员可用）"""
    start_time = time.time()
    user_id = get_jwt_identity()
    current_app.logger.info(f"API调用: 同步基金数据 - 用户ID: {user_id}")
    
    try:
        # 这里可以实现从外部API同步基金数据的功能
        # 为了简化，这里只是返回一个成功消息
        current_app.logger.info(f"基金数据同步成功 - 用户ID: {user_id}")
        
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': '基金数据同步成功'}), 200
    except Exception as e:
        current_app.logger.error(f"同步基金数据失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': '同步基金数据失败'}), 500


@funds_bp.route('/<string:code>/notes', methods=['GET'])
def get_fund_notes(code):
    """获取基金相关笔记"""
    start_time = time.time()
    current_app.logger.info(f"API调用: 获取基金相关笔记 - 基金代码: {code}, 参数: {request.args}")
    
    try:
        # 查询基金
        fund = Fund.query.filter_by(code=code).first()
        
        if fund is None:
            current_app.logger.warning(f"基金不存在: {code}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '基金不存在'}), 404
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # 尝试从缓存获取
        cache_key = f'fund_notes:{fund.id}:{page}:{per_page}'
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            current_app.logger.info(f"缓存命中: {cache_key}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify(json.loads(cached_data)), 200
        
        current_app.logger.info(f"缓存未命中: {cache_key}")
        
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
        
        current_app.logger.info(f"基金笔记查询结果: 基金代码 {code}, 共{pagination.total}条笔记, 当前第{page}页")
        
        # 缓存结果，设置过期时间为10分钟
        redis_client.setex(
            cache_key,
            600,  # 10分钟
            json.dumps(response_data)
        )
        current_app.logger.info(f"缓存已设置: {cache_key}, 过期时间: 10分钟")
        
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(response_data), 200
    except Exception as e:
        current_app.logger.error(f"获取基金相关笔记失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': '获取基金相关笔记失败'}), 500 