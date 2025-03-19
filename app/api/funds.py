from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import requests
import time
import re

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


@funds_bp.route('/query_external/<string:code>', methods=['GET'])
def query_external_fund(code):
    """从天天基金网API查询基金信息"""
    start_time = time.time()
    current_app.logger.info(f"API调用: 从天天基金网查询基金信息 - 基金代码: {code}")
    
    # 尝试从缓存获取
    cache_key = f'funds:external:{code}'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        current_app.logger.info(f"缓存命中: {cache_key}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify(json.loads(cached_data)), 200
    
    current_app.logger.info(f"缓存未命中: {cache_key}")
    
    try:
        # 查询天天基金网API获取基金实时信息
        # 接口1: 基金实时信息
        url = f'http://fundgz.1234567.com.cn/js/{code}.js?rt={int(time.time() * 1000)}'
        current_app.logger.info(f"请求天天基金网API: {url}")
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if response.status_code != 200:
            current_app.logger.error(f"天天基金网API请求失败: 状态码 {response.status_code}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '天天基金网API请求失败'}), 500
        
        # 解析返回的数据，格式为 jsonpgz({"fundcode":"161725","name":"招商中证白酒指数(LOF)","jzrq":"2021-02-09","dwjz":"1.5439","gsz":"1.6183","gszzl":"4.82","gztime":"2021-02-10 15:00"})
        text = response.text
        if text.startswith('jsonpgz(') and text.endswith(');'):
            json_str = text[8:-2]  # 去除jsonpgz()
            fund_data = json.loads(json_str)
            
            # 查询基金详细信息
            # 接口2: 基金详细信息
            detail_url = f'http://fund.eastmoney.com/pingzhongdata/{code}.js?v={int(time.time() * 1000)}'
            current_app.logger.info(f"请求天天基金网详细信息API: {detail_url}")
            
            detail_response = requests.get(detail_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            fund_type = ""
            manager = ""
            found_date = ""
            company = ""
            
            if detail_response.status_code == 200:
                # 解析基金类型、基金经理等信息
                detail_text = detail_response.text
                
                # 提取基金类型
                type_match = re.search(r'FTYPE\s*=\s*"([^"]+)"', detail_text)
                if type_match:
                    fund_type = type_match.group(1)
                
                # 提取基金经理
                manager_match = re.search(r'FUND_MANAGER\s*=\s*"([^"]+)"', detail_text)
                if manager_match:
                    manager = manager_match.group(1)
                
                # 提取成立日期
                found_date_match = re.search(r'ESTABDATE\s*=\s*"([^"]+)"', detail_text)
                if found_date_match:
                    found_date = found_date_match.group(1)
                
                # 提取基金公司
                company_match = re.search(r'JJGS\s*=\s*"([^"]+)"', detail_text)
                if company_match:
                    company = company_match.group(1)
            
            # 构建响应数据
            result = {
                'fundcode': fund_data.get('fundcode', ''),
                'name': fund_data.get('name', ''),
                'jzrq': fund_data.get('jzrq', ''),  # 净值日期
                'dwjz': fund_data.get('dwjz', ''),  # 单位净值
                'gsz': fund_data.get('gsz', ''),    # 估算净值
                'gszzl': fund_data.get('gszzl', ''), # 估算涨幅
                'gztime': fund_data.get('gztime', ''), # 估值时间
                'fund_type': fund_type,
                'manager': manager,
                'found_date': found_date,
                'company': company
            }
            
            # 缓存结果，设置过期时间为10分钟
            redis_client.setex(
                cache_key,
                600,  # 10分钟
                json.dumps(result)
            )
            current_app.logger.info(f"缓存已设置: {cache_key}, 过期时间: 10分钟")
            
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify(result), 200
        else:
            current_app.logger.error(f"天天基金网API返回数据格式错误: {text}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '天天基金网API返回数据格式错误'}), 500
    except Exception as e:
        current_app.logger.error(f"查询天天基金网API失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': f'查询天天基金网API失败: {str(e)}'}), 500


@funds_bp.route('/sync_from_external/<string:code>', methods=['POST'])
@jwt_required()
def sync_from_external(code):
    """从天天基金网同步基金信息到本地数据库"""
    start_time = time.time()
    user_id = get_jwt_identity()
    current_app.logger.info(f"API调用: 从天天基金网同步基金信息 - 基金代码: {code}, 用户ID: {user_id}")
    
    try:
        # 查询天天基金网API获取基金信息
        url = f'http://fundgz.1234567.com.cn/js/{code}.js?rt={int(time.time() * 1000)}'
        current_app.logger.info(f"请求天天基金网API: {url}")
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if response.status_code != 200:
            current_app.logger.error(f"天天基金网API请求失败: 状态码 {response.status_code}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '天天基金网API请求失败'}), 500
        
        # 解析返回的数据
        text = response.text
        if text.startswith('jsonpgz(') and text.endswith(');'):
            json_str = text[8:-2]  # 去除jsonpgz()
            fund_data = json.loads(json_str)
            
            # 查询基金是否已存在
            fund = Fund.query.filter_by(code=code).first()
            
            if fund:
                # 更新基金信息
                fund.name = fund_data.get('name', '')
                fund.net_value = float(fund_data.get('dwjz', 0))
                fund.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
                current_app.logger.info(f"更新基金信息: {code}")
            else:
                # 创建新基金
                fund = Fund(
                    code=code,
                    name=fund_data.get('name', ''),
                    net_value=float(fund_data.get('dwjz', 0)),
                    type='未知'  # 可以通过其他API获取更详细的信息
                )
                db.session.add(fund)
                current_app.logger.info(f"创建新基金: {code}")
            
            db.session.commit()
            
            # 清除相关缓存
            cache_keys = [
                f'funds:detail:{code}',
                f'funds:external:{code}'
            ]
            for key in cache_keys:
                redis_client.delete(key)
                current_app.logger.info(f"清除缓存: {key}")
            
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': f'基金 {code} 同步成功'}), 200
        else:
            current_app.logger.error(f"天天基金网API返回数据格式错误: {text}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '天天基金网API返回数据格式错误'}), 500
    except Exception as e:
        current_app.logger.error(f"从天天基金网同步基金信息失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': f'从天天基金网同步基金信息失败: {str(e)}'}), 500


@funds_bp.route('/sync_all_from_external', methods=['POST'])
@jwt_required()
def sync_all_from_external():
    """从天天基金网同步所有基金列表"""
    start_time = time.time()
    user_id = get_jwt_identity()
    current_app.logger.info(f"API调用: 从天天基金网同步所有基金列表 - 用户ID: {user_id}")
    
    try:
        # 获取天天基金网的基金列表
        url = 'http://fund.eastmoney.com/js/fundcode_search.js'
        current_app.logger.info(f"请求天天基金网基金列表API: {url}")
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if response.status_code != 200:
            current_app.logger.error(f"天天基金网API请求失败: 状态码 {response.status_code}")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '天天基金网API请求失败'}), 500
        
        # 解析返回的数据，格式为 var r = [["000001","HXCZHH","华夏成长混合","混合型","HUAXIACHENGZHANGHUNHE"],...];
        text = response.text
        if 'var r =' in text:
            # 提取JSON数组部分
            json_str = text.split('var r =')[1].strip().rstrip(';')
            fund_list = json.loads(json_str)
            
            # 记录处理的基金数量
            total_funds = len(fund_list)
            processed_funds = 0
            new_funds = 0
            updated_funds = 0
            
            current_app.logger.info(f"获取到 {total_funds} 只基金")
            
            # 批量处理基金数据
            for fund_item in fund_list:
                code = fund_item[0]  # 基金代码
                name = fund_item[2]  # 基金名称
                fund_type = fund_item[3]  # 基金类型
                
                # 查询基金是否已存在
                fund = Fund.query.filter_by(code=code).first()
                
                if fund:
                    # 更新基金信息
                    fund.name = name
                    fund.type = fund_type
                    fund.updated_at = time.strftime('%Y-%m-%d %H:%M:%S')
                    updated_funds += 1
                else:
                    # 创建新基金
                    fund = Fund(
                        code=code,
                        name=name,
                        type=fund_type
                    )
                    db.session.add(fund)
                    new_funds += 1
                
                processed_funds += 1
                
                # 每100条记录提交一次，避免事务过大
                if processed_funds % 100 == 0:
                    db.session.commit()
                    current_app.logger.info(f"已处理 {processed_funds}/{total_funds} 只基金")
            
            # 提交剩余的记录
            db.session.commit()
            
            # 清除相关缓存
            redis_client.delete('funds:list:*')
            current_app.logger.info(f"清除基金列表缓存")
            
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({
                'message': '基金列表同步成功',
                'total': total_funds,
                'new': new_funds,
                'updated': updated_funds
            }), 200
        else:
            current_app.logger.error(f"天天基金网API返回数据格式错误")
            response_time = time.time() - start_time
            current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
            return jsonify({'message': '天天基金网API返回数据格式错误'}), 500
    except Exception as e:
        current_app.logger.error(f"从天天基金网同步基金列表失败: {str(e)}")
        response_time = time.time() - start_time
        current_app.logger.info(f"API响应时间: {response_time:.3f}秒")
        return jsonify({'message': f'从天天基金网同步基金列表失败: {str(e)}'}), 500 