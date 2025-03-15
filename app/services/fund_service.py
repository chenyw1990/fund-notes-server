import requests
from app.extensions import db
from app.models import Fund
from app.utils.redis_utils import cache_clear_pattern

def sync_fund_data(fund_codes=None):
    """同步基金数据
    
    Args:
        fund_codes: 基金代码列表，如果为None则同步所有基金
    
    Returns:
        同步的基金数量
    """
    # 这里应该实现从外部API获取基金数据的逻辑
    # 为了示例，这里只是创建一些示例数据
    
    sample_funds = [
        {
            'code': '000001',
            'name': '华夏成长混合',
            'type': '混合型',
            'manager': '王经理',
            'company': '华夏基金',
            'size': 56.78,
            'description': '该基金是一只混合型基金，投资于股票和债券市场。'
        },
        {
            'code': '000002',
            'name': '博时现金收益货币',
            'type': '货币型',
            'manager': '李经理',
            'company': '博时基金',
            'size': 123.45,
            'description': '该基金是一只货币市场基金，投资于短期货币市场工具。'
        },
        {
            'code': '000003',
            'name': '嘉实增长混合',
            'type': '混合型',
            'manager': '张经理',
            'company': '嘉实基金',
            'size': 78.90,
            'description': '该基金是一只混合型基金，投资于具有良好增长潜力的上市公司股票。'
        }
    ]
    
    count = 0
    
    for fund_data in sample_funds:
        if fund_codes and fund_data['code'] not in fund_codes:
            continue
        
        # 查找或创建基金
        fund = Fund.query.filter_by(code=fund_data['code']).first()
        
        if fund is None:
            fund = Fund(code=fund_data['code'])
            db.session.add(fund)
        
        # 更新基金数据
        fund.name = fund_data['name']
        fund.type = fund_data['type']
        fund.manager = fund_data['manager']
        fund.company = fund_data['company']
        fund.size = fund_data['size']
        fund.description = fund_data['description']
        
        count += 1
    
    db.session.commit()
    
    # 清除相关缓存
    cache_clear_pattern('funds:*')
    
    return count


def get_fund_value_trend(fund_code, days=30):
    """获取基金净值走势
    
    Args:
        fund_code: 基金代码
        days: 天数
    
    Returns:
        净值走势数据
    """
    # 这里应该实现从外部API获取基金净值走势的逻辑
    # 为了示例，这里只是返回一些示例数据
    
    import random
    from datetime import datetime, timedelta
    
    trend_data = []
    base_value = 1.0
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        change = (random.random() - 0.5) * 0.02  # -1% 到 1% 的随机变化
        value = base_value * (1 + change)
        base_value = value
        
        trend_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'value': round(value, 4),
            'change': round(change * 100, 2)  # 转换为百分比
        })
    
    return trend_data 