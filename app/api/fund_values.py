from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.models import Fund, FundValue
from app.services.fund_value_service import get_latest_fund_values, get_fund_values_by_date_range, fetch_fund_value

fund_values_bp = Blueprint('fund_values', __name__)

@fund_values_bp.route('', methods=['GET'])
@jwt_required()
def get_values():
    """获取基金净值数据
    
    查询参数:
    - fund_id: 基金ID
    - fund_code: 基金代码
    - start_date: 开始日期 (YYYY-MM-DD)
    - end_date: 结束日期 (YYYY-MM-DD)
    - page: 页码 (默认1)
    - per_page: 每页数量 (默认20)
    """
    # 获取查询参数
    fund_id = request.args.get('fund_id', type=int)
    fund_code = request.args.get('fund_code')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 验证参数
    if not fund_id and not fund_code:
        return jsonify({'error': '必须提供fund_id或fund_code'}), 400
    
    # 如果提供了fund_code，获取对应的fund_id
    if fund_code and not fund_id:
        fund = Fund.query.filter_by(code=fund_code).first()
        if not fund:
            return jsonify({'error': f'未找到代码为{fund_code}的基金'}), 404
        fund_id = fund.id
    
    # 解析日期参数
    start_date = None
    end_date = None
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '开始日期格式无效，应为YYYY-MM-DD'}), 400
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '结束日期格式无效，应为YYYY-MM-DD'}), 400
    
    # 如果没有提供日期范围，默认查询最近30天
    if not start_date and not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    elif not end_date:
        end_date = datetime.now().date()
    elif not start_date:
        start_date = end_date - timedelta(days=30)
    
    # 查询基金净值数据
    query = FundValue.query.filter_by(fund_id=fund_id)
    
    if start_date:
        query = query.filter(FundValue.date >= start_date)
    if end_date:
        query = query.filter(FundValue.date <= end_date)
    
    # 按日期降序排序
    query = query.order_by(FundValue.date.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    fund_values = pagination.items
    
    # 获取基金信息
    fund = Fund.query.get(fund_id)
    if not fund:
        return jsonify({'error': f'未找到ID为{fund_id}的基金'}), 404
    
    # 构造响应
    response = {
        'fund': {
            'id': fund.id,
            'code': fund.code,
            'name': fund.name
        },
        'values': [
            {
                'id': value.id,
                'date': value.date.isoformat(),
                'net_value': value.net_value,
                'accumulated_value': value.accumulated_value,
                'daily_change': value.daily_change,
                'last_week_change': value.last_week_change,
                'last_month_change': value.last_month_change,
                'last_year_change': value.last_year_change,
                'since_inception_change': value.since_inception_change
            } for value in fund_values
        ],
        'pagination': {
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page
        }
    }
    
    return jsonify(response)

@fund_values_bp.route('/latest', methods=['GET'])
@jwt_required()
def get_latest_values():
    """获取基金最新净值数据
    
    查询参数:
    - fund_id: 基金ID
    - fund_code: 基金代码
    """
    # 获取查询参数
    fund_id = request.args.get('fund_id', type=int)
    fund_code = request.args.get('fund_code')
    
    # 验证参数
    if not fund_id and not fund_code:
        return jsonify({'error': '必须提供fund_id或fund_code'}), 400
    
    # 如果提供了fund_code，获取对应的fund_id
    if fund_code and not fund_id:
        fund = Fund.query.filter_by(code=fund_code).first()
        if not fund:
            return jsonify({'error': f'未找到代码为{fund_code}的基金'}), 404
        fund_id = fund.id
    
    # 获取基金信息
    fund = Fund.query.get(fund_id)
    if not fund:
        return jsonify({'error': f'未找到ID为{fund_id}的基金'}), 404
    
    # 获取最新净值数据
    latest_value = get_latest_fund_values(fund_id=fund_id, limit=1)
    
    if not latest_value:
        return jsonify({'error': f'未找到基金{fund.code}的净值数据'}), 404
    
    latest_value = latest_value[0]
    
    # 构造响应
    response = {
        'fund': {
            'id': fund.id,
            'code': fund.code,
            'name': fund.name
        },
        'value': {
            'id': latest_value.id,
            'date': latest_value.date.isoformat(),
            'net_value': latest_value.net_value,
            'accumulated_value': latest_value.accumulated_value,
            'daily_change': latest_value.daily_change,
            'last_week_change': latest_value.last_week_change,
            'last_month_change': latest_value.last_month_change,
            'last_year_change': latest_value.last_year_change,
            'since_inception_change': latest_value.since_inception_change
        }
    }
    
    return jsonify(response)

@fund_values_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh_fund_values():
    """手动刷新基金净值数据
    
    请求体:
    {
        "fund_code": "000001", // 可选，如果不提供则刷新所有基金
        "start_date": "2023-01-01", // 可选，开始日期
        "end_date": "2023-01-31" // 可选，结束日期
    }
    """
    # 获取请求数据
    data = request.get_json() or {}
    fund_code = data.get('fund_code')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    # 执行刷新操作
    try:
        count = fetch_fund_value(fund_code=fund_code, start_date=start_date, end_date=end_date)
        return jsonify({
            'success': True,
            'message': f'成功刷新{count}条基金净值数据',
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 