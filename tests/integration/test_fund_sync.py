import json
import pytest
from unittest.mock import patch, MagicMock
from app.models import Fund, User

@pytest.fixture
def admin_user(app, db):
    """创建测试管理员用户"""
    user = User(
        username='admin_test',
        email='admin@example.com',
        role='admin'  # 使用 role 字段而不是 is_admin
    )
    user.set_password('password123')
    
    # 如果 User 模型有 role 字段，可以使用它来标识管理员
    # user.role = 'admin'
    
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def admin_token(client, admin_user):
    """获取管理员用户的JWT令牌"""
    response = client.post('/api/auth/login', json={
        'username': 'admin_test',
        'password': 'password123'
    })
    return json.loads(response.data)['access_token']

@pytest.fixture
def mock_fund_list_response():
    """模拟天天基金网返回的基金列表数据"""
    return """
    var r = [
        ["000001","HXCZHH","华夏成长混合","混合型","HUAXIACHENGZHANGHUNHE"],
        ["000002","HXCZHH","华夏成长混合C","混合型","HUAXIACHENGZHANGHUNHEC"],
        ["000003","ZHKZZZQA","中海可转债债券A","债券型","ZHONGHAIKEZHUANZHAIZHAIQUANA"],
        ["000004","ZHKZZZQC","中海可转债债券C","债券型","ZHONGHAIKEZHUANZHAIZHAIQUANC"],
        ["000005","JSZQXYDQZQ","建信稳定增利债券C","债券型","JIANXINWENDINGZENGLIZHAIQUANC"]
    ];
    """

def test_sync_all_from_external(client, mocker):
    # 模拟 jwt_required 装饰器，使其不检查权限
    mocker.patch('app.api.funds.jwt_required', return_value=lambda f: f)
    mocker.patch('app.api.funds.get_jwt_identity', return_value=1)  # 返回一个用户 ID
    
    # 模拟requests.get返回的响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_fund_list_response
    
    # 使用mocker替换requests.get方法
    mocker.patch('requests.get', return_value=mock_response)
    
    # 模拟Redis缓存操作
    mocker.patch('app.api.funds.redis_client.delete')
    
    # 发送请求
    response = client.post(
        '/api/funds/sync_all_from_external'
    )
    
    # 验证响应
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == '基金列表同步成功'
    assert data['total'] == 5
    assert data['new'] == 5  # 假设所有基金都是新的
    
    # 验证数据库中的基金数据
    funds = Fund.query.all()
    assert len(funds) == 5
    
    # 验证第一个基金的信息
    fund = Fund.query.filter_by(code='000001').first()
    assert fund is not None
    assert fund.name == '华夏成长混合'
    assert fund.type == '混合型'
    
    # 验证Redis缓存被清除
    app.api.funds.redis_client.delete.assert_called_once()

def test_sync_all_from_external_unauthorized(client):
    """测试未授权访问同步接口"""
    response = client.post('/api/funds/sync_all_from_external')
    assert response.status_code == 401

def test_sync_all_from_external_api_error(client, mocker):
    """测试天天基金网API请求失败的情况"""
    # 模拟requests.get抛出异常
    mocker.patch('requests.get', side_effect=Exception('API连接失败'))
    
    # 发送请求
    response = client.post(
        '/api/funds/sync_all_from_external'
    )
    
    # 验证响应
    assert response.status_code == 500
    data = json.loads(response.data)
    assert '从天天基金网同步基金列表失败' in data['message']

def test_sync_all_from_external_bad_response(client, mocker):
    """测试天天基金网返回错误格式数据的情况"""
    # 模拟requests.get返回的响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "错误的数据格式"
    
    # 使用mocker替换requests.get方法
    mocker.patch('requests.get', return_value=mock_response)
    
    # 发送请求
    response = client.post(
        '/api/funds/sync_all_from_external'
    )
    
    # 验证响应
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data['message'] == '天天基金网API返回数据格式错误'

def test_sync_all_from_external_update_existing(client, mocker, db):
    """测试更新已存在的基金信息"""
    # 先创建一个已存在的基金
    existing_fund = Fund(
        code='000001',
        name='旧名称',
        type='旧类型'
    )
    db.session.add(existing_fund)
    db.session.commit()
    
    # 模拟requests.get返回的响应
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = mock_fund_list_response
    
    # 使用mocker替换requests.get方法
    mocker.patch('requests.get', return_value=mock_response)
    
    # 模拟Redis缓存操作
    mocker.patch('app.api.funds.redis_client.delete')
    
    # 发送请求
    response = client.post(
        '/api/funds/sync_all_from_external'
    )
    
    # 验证响应
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == '基金列表同步成功'
    assert data['total'] == 5
    assert data['new'] == 4  # 应该有4个新基金
    assert data['updated'] == 1  # 应该有1个更新的基金
    
    # 验证基金信息已更新
    updated_fund = Fund.query.filter_by(code='000001').first()
    assert updated_fund.name == '华夏成长混合'
    assert updated_fund.type == '混合型'
    
    # 验证Redis缓存被清除
    app.api.funds.redis_client.delete.assert_called_once() 