from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

from app.extensions import db, redis_client
from app.models import Note, User, Fund

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('', methods=['GET'])
def get_notes():
    """获取笔记列表"""
    # 获取查询参数
    fund_id = request.args.get('fund_id', type=int)
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 构建查询
    query = Note.query
    
    # 只返回公开的笔记，除非指定了用户ID
    if user_id:
        query = query.filter_by(user_id=user_id)
    else:
        query = query.filter_by(is_public=True)
    
    # 如果指定了基金ID，则过滤
    if fund_id:
        query = query.filter_by(fund_id=fund_id)
    
    # 按创建时间降序排序
    query = query.order_by(Note.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    
    # 构建响应
    notes = [note.to_dict() for note in pagination.items]
    
    # 添加作者和基金信息
    for note in notes:
        user = User.query.get(note['user_id'])
        fund = Fund.query.get(note['fund_id'])
        
        if user:
            note['author'] = {
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar
            }
        
        if fund:
            note['fund'] = {
                'id': fund.id,
                'code': fund.code,
                'name': fund.name
            }
    
    return jsonify({
        'notes': notes,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@notes_bp.route('/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """获取单个笔记"""
    note = Note.query.get(note_id)
    
    if note is None:
        return jsonify({'message': '笔记不存在'}), 404
    
    # 检查笔记是否公开
    if not note.is_public:
        # 如果用户已登录，检查是否是笔记作者
        current_user_id = get_jwt_identity() if request.headers.get('Authorization') else None
        
        if current_user_id is None or current_user_id != note.user_id:
            return jsonify({'message': '无权访问此笔记'}), 403
    
    # 构建响应
    note_data = note.to_dict()
    
    # 添加作者和基金信息
    user = User.query.get(note.user_id)
    fund = Fund.query.get(note.fund_id)
    
    if user:
        note_data['author'] = {
            'id': user.id,
            'username': user.username,
            'avatar': user.avatar
        }
    
    if fund:
        note_data['fund'] = {
            'id': fund.id,
            'code': fund.code,
            'name': fund.name
        }
    
    return jsonify(note_data), 200


@notes_bp.route('', methods=['POST'])
@jwt_required()
def create_note():
    """创建笔记"""
    data = request.get_json()
    
    # 检查必要字段
    if not all(k in data for k in ('title', 'content', 'fund_id')):
        return jsonify({'message': '缺少必要字段'}), 400
    
    # 检查基金是否存在
    fund = Fund.query.get(data['fund_id'])
    if fund is None:
        return jsonify({'message': '基金不存在'}), 404
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 创建笔记
    note = Note(
        title=data['title'],
        content=data['content'],
        rating=data.get('rating'),
        user_id=user_id,
        fund_id=data['fund_id'],
        is_public=data.get('is_public', True)
    )
    
    db.session.add(note)
    db.session.commit()
    
    # 清除相关缓存
    cache_key = f'fund_notes:{data["fund_id"]}'
    if redis_client.exists(cache_key):
        redis_client.delete(cache_key)
    
    return jsonify({
        'message': '笔记创建成功',
        'note': note.to_dict()
    }), 201


@notes_bp.route('/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(note_id):
    """更新笔记"""
    note = Note.query.get(note_id)
    
    if note is None:
        return jsonify({'message': '笔记不存在'}), 404
    
    # 检查权限
    user_id = get_jwt_identity()
    if note.user_id != user_id:
        return jsonify({'message': '无权更新此笔记'}), 403
    
    data = request.get_json()
    
    # 更新笔记
    if 'title' in data:
        note.title = data['title']
    
    if 'content' in data:
        note.content = data['content']
    
    if 'rating' in data:
        note.rating = data['rating']
    
    if 'is_public' in data:
        note.is_public = data['is_public']
    
    db.session.commit()
    
    # 清除相关缓存
    cache_key = f'fund_notes:{note.fund_id}'
    if redis_client.exists(cache_key):
        redis_client.delete(cache_key)
    
    return jsonify({
        'message': '笔记更新成功',
        'note': note.to_dict()
    }), 200


@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(note_id):
    """删除笔记"""
    note = Note.query.get(note_id)
    
    if note is None:
        return jsonify({'message': '笔记不存在'}), 404
    
    # 检查权限
    user_id = get_jwt_identity()
    if note.user_id != user_id:
        return jsonify({'message': '无权删除此笔记'}), 403
    
    # 保存基金ID用于清除缓存
    fund_id = note.fund_id
    
    # 删除笔记
    db.session.delete(note)
    db.session.commit()
    
    # 清除相关缓存
    cache_key = f'fund_notes:{fund_id}'
    if redis_client.exists(cache_key):
        redis_client.delete(cache_key)
    
    return jsonify({'message': '笔记删除成功'}), 200 