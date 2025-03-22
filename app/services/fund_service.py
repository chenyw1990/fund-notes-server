import requests
from app.extensions import db
from app.models import Fund
from app.utils.redis_utils import cache_clear_pattern
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_fund_details(fund_code):
    """从天天基金网获取基金详细信息并更新数据库
    
    Args:
        fund_code: 基金代码
    
    Returns:
        更新后的基金对象或None
    """
    try:
        logger.info(f"正在从东方财富获取基金 {fund_code} 的详细信息")
        
        # 使用基金净值API获取基金基本信息
        url = f"https://api.fund.eastmoney.com/f10/lsjz"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "http://fund.eastmoney.com/"
        }
        params = {
            "fundCode": fund_code,
            "pageIndex": 1,
            "pageSize": 1
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to fetch fund details for {fund_code}: {response.status_code}")
            return None
        
        data = response.json()
        
        # 调试API响应结构
        logger.debug(f"API response structure: {data.keys()}")
        
        # 如果API返回错误
        if data.get("ErrCode") != 0:
            logger.error(f"API error for fund {fund_code}: {data.get('ErrMsg')}")
            return None
        
        # 获取基金数据
        fund_data = data.get("Data", {})
        logger.debug(f"Fund data structure: {fund_data.keys()}")
        
        # 提取基金列表
        fund_list = fund_data.get("LSJZList", [])
        if not fund_list:
            logger.warning(f"No fund data found for {fund_code}")
            
        # 获取基金名称
        fund_name = None
        
        # 尝试从不同位置获取基金名称
        if "FundName" in fund_data:
            fund_name = fund_data.get("FundName")
        elif "BuyRateRemark" in fund_data:
            # 有时名称在其他字段的描述中
            buy_rate_remark = fund_data.get("BuyRateRemark", "")
            if buy_rate_remark and "：" in buy_rate_remark:
                fund_name = buy_rate_remark.split("：")[0].strip()
        
        # 如果在主数据中没有找到，则尝试使用另一个API
        if not fund_name:
            logger.info(f"Trying alternative API to get fund name for {fund_code}")
            alt_url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            try:
                alt_response = requests.get(alt_url, headers=headers)
                if alt_response.status_code == 200:
                    text = alt_response.text
                    # 提取基金名称
                    name_start = text.find('fS_name = "')
                    if name_start > 0:
                        name_start += 11  # "fS_name = "" 的长度
                        name_end = text.find('"', name_start)
                        if name_end > name_start:
                            fund_name = text[name_start:name_end]
                            logger.debug(f"Found fund name from alternative API: {fund_name}")
            except Exception as e:
                logger.warning(f"Error fetching alternative fund info for {fund_code}: {str(e)}")
        
        if not fund_name:
            # 如果仍无法获取名称，尝试使用移动端API
            try:
                mobile_url = f"https://fundmobapi.eastmoney.com/FundMNewApi/FundMNFInfo"
                mobile_params = {
                    "plat": "Android",
                    "appType": "ttjj",
                    "product": "EFund",
                    "Version": "1",
                    "deviceid": "123",
                    "FCODE": fund_code
                }
                mobile_response = requests.get(mobile_url, headers=headers, params=mobile_params)
                if mobile_response.status_code == 200:
                    mobile_data = mobile_response.json()
                    if mobile_data.get("ErrCode") == 0:
                        mobile_fund_data = mobile_data.get("Datas", {})
                        fund_name = mobile_fund_data.get("SHORTNAME")
                        logger.debug(f"Found fund name from mobile API: {fund_name}")
            except Exception as e:
                logger.warning(f"Error fetching mobile fund info for {fund_code}: {str(e)}")
        
        if not fund_name:
            logger.warning(f"Could not find name for fund {fund_code}")
            return None
        
        logger.info(f"获取到基金名称: {fund_name}")
        
        # 获取基金详情
        fund_details = {
            "company": None,
            "manager": None,
            "inception_date": None,
            "type": None,
            "description": None,
            "size": None
        }
        
        # 尝试从JS中提取更多信息
        try:
            fund_js_url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            fund_js_response = requests.get(fund_js_url, headers=headers)
            if fund_js_response.status_code == 200:
                js_text = fund_js_response.text
                
                # 提取基金类型
                type_start = js_text.find('fS_classification = "')
                if type_start > 0:
                    type_start += 20
                    type_end = js_text.find('"', type_start)
                    if type_end > type_start:
                        fund_details["type"] = js_text[type_start:type_end]
                
                # 提取基金公司
                company_start = js_text.find('fS_corpManager = "')
                if company_start > 0:
                    company_start += 18
                    company_end = js_text.find('"', company_start)
                    if company_end > company_start:
                        fund_details["company"] = js_text[company_start:company_end]
        except Exception as e:
            logger.warning(f"Error extracting info from JS for fund {fund_code}: {str(e)}")
        
        # 查找或创建基金记录
        fund = Fund.query.filter_by(code=fund_code).first()
        if not fund:
            fund = Fund(code=fund_code)
            db.session.add(fund)
        
        # 更新基金信息
        fund.name = fund_name
        
        # 更新其他详细信息（如果有）
        if fund_details.get("company"):
            fund.company = fund_details["company"]
        
        if fund_details.get("manager"):
            fund.manager = fund_details["manager"]
        
        if fund_details.get("type"):
            fund.type = fund_details["type"]
        
        if fund_details.get("description"):
            fund.description = fund_details["description"]
        
        # 处理成立日期
        if fund_details.get("inception_date"):
            try:
                inception_date = datetime.strptime(fund_details["inception_date"], "%Y-%m-%d").date()
                fund.inception_date = inception_date
            except Exception as e:
                logger.warning(f"Error parsing inception date for fund {fund_code}: {str(e)}")
        
        # 处理基金规模
        if fund_details.get("size") is not None:
            fund.size = fund_details["size"]
        
        db.session.commit()
        logger.info(f"Successfully updated details for fund {fund_code}")
        
        # 清除相关缓存
        cache_clear_pattern(f'funds:{fund_code}*')
        
        return fund
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Exception in fetch_fund_details for {fund_code}: {str(e)}")
        return None

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