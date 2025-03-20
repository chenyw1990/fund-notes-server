from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.extensions import db
from app.models import Purchase, Fund

purchases_bp = Blueprint('purchases', __name__)

@purchases_bp.route('', methods=['GET'])
@jwt_required()
def get_purchases():
    """获取用户的基金购买记录"""
    user_id = get_jwt_identity()
    fund_id = request.args.get('fund_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 构建查询
    query = Purchase.query.filter_by(user_id=user_id)
    
    # 如果指定了基金ID，则过滤
    if fund_id:
        query = query.filter_by(fund_id=fund_id)
    
    # 按购买日期降序排序
    query = query.order_by(Purchase.purchase_date.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    
    # 构建响应
    purchases = []
    for purchase in pagination.items:
        purchase_data = purchase.to_dict()
        
        # 添加基金信息
        fund = Fund.query.get(purchase.fund_id)
        if fund:
            purchase_data['fund'] = {
                'id': fund.id,
                'code': fund.code,
                'name': fund.name
            }
        
        purchases.append(purchase_data)
    
    return jsonify({
        'purchases': purchases,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@purchases_bp.route('/<int:purchase_id>', methods=['GET'])
@jwt_required()
def get_purchase(purchase_id):
    """获取单个购买记录"""
    user_id = get_jwt_identity()
    
    purchase = Purchase.query.get(purchase_id)
    
    if purchase is None:
        return jsonify({'message': '购买记录不存在'}), 404
    
    # 检查权限
    if purchase.user_id != user_id:
        return jsonify({'message': '无权访问此购买记录'}), 403
    
    # 构建响应
    purchase_data = purchase.to_dict()
    
    # 添加基金信息
    fund = Fund.query.get(purchase.fund_id)
    if fund:
        purchase_data['fund'] = {
            'id': fund.id,
            'code': fund.code,
            'name': fund.name
        }
    
    return jsonify(purchase_data), 200


@purchases_bp.route('', methods=['POST'])
@jwt_required()
def create_purchase():
    """创建购买记录"""
    data = request.get_json()
    
    # 检查必要字段
    if not all(k in data for k in ('fund_id', 'amount', 'purchase_date')):
        return jsonify({'message': '缺少必要字段'}), 400
    
    # 检查基金是否存在
    fund = Fund.query.get(data['fund_id'])
    if fund is None:
        return jsonify({'message': '基金不存在'}), 404
    
    # 获取当前用户ID
    user_id = get_jwt_identity()
    
    # 处理日期
    try:
        purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': '日期格式无效，应为YYYY-MM-DD'}), 400
    
    # 创建购买记录
    purchase = Purchase(
        user_id=user_id,
        fund_id=data['fund_id'],
        amount=data['amount'],
        share=data.get('share'),
        price=data.get('price'),
        purchase_date=purchase_date,
        fee=data.get('fee', 0.0),
        notes=data.get('notes', '')
    )
    
    db.session.add(purchase)
    db.session.commit()
    
    return jsonify({
        'message': '购买记录创建成功',
        'purchase': purchase.to_dict()
    }), 201


@purchases_bp.route('/<int:purchase_id>', methods=['PUT'])
@jwt_required()
def update_purchase(purchase_id):
    """更新购买记录"""
    purchase = Purchase.query.get(purchase_id)
    
    if purchase is None:
        return jsonify({'message': '购买记录不存在'}), 404
    
    # 检查权限
    user_id = get_jwt_identity()
    if purchase.user_id != user_id:
        return jsonify({'message': '无权更新此购买记录'}), 403
    
    data = request.get_json()
    
    # 更新购买记录
    if 'amount' in data:
        purchase.amount = data['amount']
    
    if 'share' in data:
        purchase.share = data['share']
    
    if 'price' in data:
        purchase.price = data['price']
    
    if 'purchase_date' in data:
        try:
            purchase.purchase_date = datetime.strptime(data['purchase_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': '日期格式无效，应为YYYY-MM-DD'}), 400
    
    if 'fee' in data:
        purchase.fee = data['fee']
    
    if 'notes' in data:
        purchase.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({
        'message': '购买记录更新成功',
        'purchase': purchase.to_dict()
    }), 200


@purchases_bp.route('/<int:purchase_id>', methods=['DELETE'])
@jwt_required()
def delete_purchase(purchase_id):
    """删除购买记录"""
    purchase = Purchase.query.get(purchase_id)
    
    if purchase is None:
        return jsonify({'message': '购买记录不存在'}), 404
    
    # 检查权限
    user_id = get_jwt_identity()
    if purchase.user_id != user_id:
        return jsonify({'message': '无权删除此购买记录'}), 403
    
    db.session.delete(purchase)
    db.session.commit()
    
    return jsonify({'message': '购买记录删除成功'}), 200 