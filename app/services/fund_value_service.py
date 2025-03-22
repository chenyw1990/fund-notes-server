import requests
import logging
import json
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Fund, FundValue

logger = logging.getLogger(__name__)

def fetch_fund_value(fund_code=None, start_date=None, end_date=None):
    """获取指定基金的净值数据
    
    Args:
        fund_code: 基金代码，如果为None则获取所有基金
        start_date: 开始日期，格式为YYYY-MM-DD
        end_date: 结束日期，格式为YYYY-MM-DD
    
    Returns:
        更新的基金净值数量
    """
    funds_to_update = []
    if fund_code:
        fund = Fund.query.filter_by(code=fund_code).first()
        if fund:
            funds_to_update.append(fund)
    else:
        funds_to_update = Fund.query.all()
    
    if not funds_to_update:
        logger.warning("No funds found to update values")
        return 0
    
    updated_count = 0
    for fund in funds_to_update:
        try:
            logger.info(f"Fetching fund value data for {fund.code} - {fund.name}")
            
            # 如果没有提供日期范围，默认获取从基金成立至今的所有数据
            if not end_date:
                end_date = datetime.now().date().strftime('%Y-%m-%d')
            
            if not start_date:
                # 首先检查数据库中是否已有该基金的净值信息
                latest_value = FundValue.query.filter_by(fund_id=fund.id).order_by(FundValue.date.desc()).first()
                logger.info(f"Latest value: {latest_value}")
                if latest_value:
                    # 如果数据库中有净值信息，从最近一次净值的日期开始获取
                    # 加1天是为了避免重复获取最后一天的数据
                    start_date = (latest_value.date + timedelta(days=1)).strftime('%Y-%m-%d')
                    logger.info(f"Using latest value date from database: {start_date}")
                elif hasattr(fund, 'inception_date') and fund.inception_date:
                    # 如果数据库中没有净值但有成立日期，则从成立日期开始获取
                    start_date = fund.inception_date.strftime('%Y-%m-%d')
                    logger.info(f"Using inception date from database: {start_date}")
                else:
                    logger.info(f"No latest value or inception date found for fund {fund.code}")
                    # 如果既没有净值记录也没有成立日期信息，默认获取近2000天的数据
                    # 天天基金API通常最多返回约2000条记录
                    end = datetime.strptime(end_date, '%Y-%m-%d').date()
                    start = end - timedelta(days=2000)
                    start_date = start.strftime('%Y-%m-%d')
            
            logger.info(f"Fetching data from {start_date} to {end_date}")
            
            # 调用天天基金网API获取数据
            values = fetch_eastmoney_fund_data(fund.code, start_date, end_date)
            
            if values:
                # 保存获取到的净值数据
                for value_data in values:
                    try:
                        value_date = datetime.strptime(value_data['date'], '%Y-%m-%d').date()
                        net_value = float(value_data['net_value'])
                        accumulated_value = float(value_data['accumulated_value'])
                        daily_change = float(value_data['daily_change']) if value_data['daily_change'] not in [None, '--', ''] else None
                        
                        # 保存到数据库
                        save_fund_value(
                            fund.id, 
                            value_date,
                            net_value,
                            accumulated_value,
                            daily_change
                        )
                        updated_count += 1
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error processing value data for {fund.code}: {str(e)}, data: {value_data}")
                        continue
                
                # 在所有值都保存后，计算并更新各时间段的收益率
                if updated_count > 0:
                    update_performance_metrics(fund.id)
            else:
                logger.warning(f"No data returned for fund {fund.code}")
                
        except Exception as e:
            logger.error(f"Error fetching fund value for {fund.code}: {str(e)}")
    
    return updated_count

def fetch_eastmoney_fund_data(fund_code, start_date=None, end_date=None):
    """从天天基金网获取基金净值数据
    
    Args:
        fund_code: 基金代码
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        包含净值数据的列表
    """
    try:
        # 构建API URL
        api_url = "https://api.fund.eastmoney.com/f10/lsjz"
        
        # 设置较大的页面大小，减少请求次数
        page_size = 50  # 天天基金API单页最大记录数
        
        # 设置请求头以模拟浏览器行为
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'http://fund.eastmoney.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
        }
        
        # 首先获取第一页，了解总页数和记录数
        params = {
            'fundCode': fund_code,
            'pageIndex': 1,
            'pageSize': page_size,
        }
        
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        logger.info(f"Making initial request to EastMoney API for fund {fund_code}")
        response = requests.get(api_url, params=params, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch data from EastMoney API: {response.status_code}")
            return []
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response from EastMoney API: {response.text[:200]}")
            return []
        
        if 'Data' not in data or 'LSJZList' not in data['Data']:
            logger.error(f"Unexpected API response structure: {data}")
            return []
        
        # 初始化结果列表
        result = []
        
        # 处理第一页数据
        for item in data['Data']['LSJZList']:
            value_data = {
                'date': item['FSRQ'],  # 净值日期
                'net_value': item['DWJZ'],  # 单位净值
                'accumulated_value': item['LJJZ'],  # 累计净值
                'daily_change': item['JZZZL'],  # 日增长率
            }
            result.append(value_data)
        
        # 计算总页数和总记录数
        total_count = data.get('TotalCount', len(result))
        # 如果数据中没有TotalPages，则根据TotalCount和PageSize计算总页数
        if 'TotalPages' in data:
            total_pages = data['TotalPages']
        else:
            # 确保计算总页数时不会除以零
            total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1

        logger.info(f"Response data structure: {data.keys()}")
        logger.info(f"Fund {fund_code} has {total_count} records across {total_pages} pages")
        
        # 继续获取其他页的数据
        if total_pages > 1:
            for page in range(2, total_pages + 1):
                try:
                    logger.info(f"Fetching page {page}/{total_pages} for fund {fund_code}")
                    params['pageIndex'] = page
                    page_response = requests.get(api_url, params=params, headers=headers)
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if 'Data' in page_data and 'LSJZList' in page_data['Data']:
                            for item in page_data['Data']['LSJZList']:
                                value_data = {
                                    'date': item['FSRQ'],
                                    'net_value': item['DWJZ'],
                                    'accumulated_value': item['LJJZ'],
                                    'daily_change': item['JZZZL'],
                                }
                                result.append(value_data)
                    else:
                        logger.warning(f"Failed to fetch page {page} for fund {fund_code}: {page_response.status_code}")
                    
                except Exception as e:
                    logger.error(f"Error fetching page {page} for fund {fund_code}: {str(e)}")
        
        logger.info(f"Successfully retrieved {len(result)} records for fund {fund_code}")
        return result
    
    except Exception as e:
        logger.error(f"Exception in fetch_eastmoney_fund_data: {str(e)}")
        return []

def save_fund_value(fund_id, value_date, net_value, accumulated_value, daily_change=None):
    """保存基金净值数据
    
    Args:
        fund_id: 基金ID
        value_date: 净值日期
        net_value: 单位净值
        accumulated_value: 累计净值
        daily_change: 日涨跌幅
    
    Returns:
        保存的FundValue对象
    """
    try:
        # 检查是否已存在相同日期的净值数据
        existing_value = FundValue.query.filter_by(
            fund_id=fund_id, 
            date=value_date
        ).first()
        
        if existing_value:
            # 更新现有记录
            existing_value.net_value = net_value
            existing_value.accumulated_value = accumulated_value
            existing_value.daily_change = daily_change
            existing_value.updated_at = datetime.utcnow()
            db.session.commit()
            return existing_value
        else:
            # 创建新记录
            fund_value = FundValue(
                fund_id=fund_id,
                date=value_date,
                net_value=net_value,
                accumulated_value=accumulated_value,
                daily_change=daily_change
            )
            db.session.add(fund_value)
            db.session.commit()
            return fund_value
    
    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Integrity error saving fund value for fund_id={fund_id}, date={value_date}")
        return None
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving fund value: {str(e)}")
        return None

def get_latest_fund_values(fund_id=None, limit=1):
    """获取最新的基金净值数据
    
    Args:
        fund_id: 基金ID，如果为None则获取所有基金
        limit: 返回数量限制
    
    Returns:
        FundValue对象列表
    """
    query = FundValue.query
    
    if fund_id:
        query = query.filter_by(fund_id=fund_id)
    
    return query.order_by(FundValue.date.desc()).limit(limit).all()

def get_fund_values_by_date_range(fund_id, start_date, end_date):
    """获取指定日期范围内的基金净值数据
    
    Args:
        fund_id: 基金ID
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        FundValue对象列表
    """
    return FundValue.query.filter_by(fund_id=fund_id)\
        .filter(FundValue.date >= start_date)\
        .filter(FundValue.date <= end_date)\
        .order_by(FundValue.date.desc())\
        .all()

def calculate_fund_performance(fund_id):
    """计算基金收益表现
    
    Args:
        fund_id: 基金ID
    
    Returns:
        包含各时间段收益率的字典
    """
    today = date.today()
    latest_value = get_latest_fund_values(fund_id=fund_id, limit=1)
    
    if not latest_value:
        return {
            'week': None,
            'month': None,
            'three_month': None,
            'six_month': None,
            'year': None,
            'three_year': None,
            'five_year': None,
            'since_inception': None
        }
    
    latest_value = latest_value[0]
    latest_date = latest_value.date
    
    # 计算各个时间范围的日期
    week_ago = latest_date - timedelta(days=7)
    month_ago = latest_date.replace(month=latest_date.month-1) if latest_date.month > 1 else latest_date.replace(year=latest_date.year-1, month=12)
    three_month_ago = latest_date.replace(month=latest_date.month-3) if latest_date.month > 3 else latest_date.replace(year=latest_date.year-1, month=latest_date.month+9)
    six_month_ago = latest_date.replace(month=latest_date.month-6) if latest_date.month > 6 else latest_date.replace(year=latest_date.year-1, month=latest_date.month+6)
    year_ago = latest_date.replace(year=latest_date.year-1)
    three_year_ago = latest_date.replace(year=latest_date.year-3)
    five_year_ago = latest_date.replace(year=latest_date.year-5)
    
    # 查找对应日期的净值数据
    week_value = find_closest_value(fund_id, week_ago)
    month_value = find_closest_value(fund_id, month_ago)
    three_month_value = find_closest_value(fund_id, three_month_ago)
    six_month_value = find_closest_value(fund_id, six_month_ago)
    year_value = find_closest_value(fund_id, year_ago)
    three_year_value = find_closest_value(fund_id, three_year_ago)
    five_year_value = find_closest_value(fund_id, five_year_ago)
    
    # 查找最早的净值数据作为成立以来基准
    inception_value = FundValue.query.filter_by(fund_id=fund_id).order_by(FundValue.date.asc()).first()
    
    # 计算收益率
    return {
        'week': calculate_return(latest_value, week_value),
        'month': calculate_return(latest_value, month_value),
        'three_month': calculate_return(latest_value, three_month_value),
        'six_month': calculate_return(latest_value, six_month_value),
        'year': calculate_return(latest_value, year_value),
        'three_year': calculate_return(latest_value, three_year_value),
        'five_year': calculate_return(latest_value, five_year_value),
        'since_inception': calculate_return(latest_value, inception_value)
    }

def find_closest_value(fund_id, target_date):
    """查找最接近目标日期的净值记录
    
    Args:
        fund_id: 基金ID
        target_date: 目标日期
    
    Returns:
        FundValue对象或None
    """
    # 先查找刚好等于目标日期的记录
    value = FundValue.query.filter_by(fund_id=fund_id, date=target_date).first()
    if value:
        return value
    
    # 如果没有找到，尝试查找最接近的记录（目标日期之前的最近一条）
    value = FundValue.query.filter_by(fund_id=fund_id).filter(FundValue.date <= target_date).order_by(FundValue.date.desc()).first()
    if value:
        return value
    
    # 如果还没找到，则查找最早的记录
    return FundValue.query.filter_by(fund_id=fund_id).order_by(FundValue.date.asc()).first()

def calculate_return(current_value, base_value):
    """计算收益率
    
    Args:
        current_value: 当前净值记录
        base_value: 基准净值记录
    
    Returns:
        收益率百分比或None
    """
    if not current_value or not base_value:
        return None
    
    # 检查accumulated_value是否为有效值
    if current_value.accumulated_value is None or base_value.accumulated_value is None or base_value.accumulated_value == 0:
        return None
    
    return round((current_value.accumulated_value / base_value.accumulated_value - 1) * 100, 2)

def update_performance_metrics(fund_id):
    """计算并更新基金的业绩指标
    
    Args:
        fund_id: 基金ID
    
    Returns:
        是否成功更新
    """
    try:
        # 获取最新的净值数据
        latest_value = get_latest_fund_values(fund_id=fund_id, limit=1)
        if not latest_value:
            logger.warning(f"No fund value found for fund_id={fund_id}")
            return False
            
        latest_value = latest_value[0]
        latest_date = latest_value.date
        
        # 计算各个时间范围的日期
        week_ago = latest_date - timedelta(days=7)
        month_ago = latest_date.replace(month=latest_date.month-1) if latest_date.month > 1 else latest_date.replace(year=latest_date.year-1, month=12)
        year_ago = latest_date.replace(year=latest_date.year-1)
        
        # 查找对应日期的净值数据
        week_value = find_closest_value(fund_id, week_ago)
        month_value = find_closest_value(fund_id, month_ago)
        year_value = find_closest_value(fund_id, year_ago)
        
        # 查找最早的净值数据作为成立以来基准
        inception_value = FundValue.query.filter_by(fund_id=fund_id).order_by(FundValue.date.asc()).first()
        
        # 计算各时间段收益率
        week_change = calculate_return(latest_value, week_value)
        month_change = calculate_return(latest_value, month_value)
        year_change = calculate_return(latest_value, year_value)
        since_inception_change = calculate_return(latest_value, inception_value)
        
        # 更新最新净值记录的收益率字段
        latest_value.last_week_change = week_change
        latest_value.last_month_change = month_change
        latest_value.last_year_change = year_change
        latest_value.since_inception_change = since_inception_change
        
        # 提交更新
        db.session.commit()
        logger.info(f"Updated performance metrics for fund_id={fund_id}, latest_date={latest_date}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating performance metrics: {str(e)}")
        return False 