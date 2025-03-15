import requests
import json
from flask import current_app

def get_access_token():
    """获取微信小程序全局接口调用凭据"""
    from app import redis_client
    
    # 尝试从缓存获取
    access_token = redis_client.get('wechat:access_token')
    if access_token:
        return access_token.decode('utf-8')
    
    # 获取配置
    appid = current_app.config['WECHAT_APPID']
    secret = current_app.config['WECHAT_SECRET']
    
    # 请求微信API
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception('微信服务器请求失败')
    
    data = response.json()
    
    if 'errcode' in data and data['errcode'] != 0:
        raise Exception(f'获取access_token失败: {data["errmsg"]}')
    
    access_token = data['access_token']
    expires_in = data['expires_in']
    
    # 缓存access_token，设置过期时间比微信返回的少300秒，以防止临界点问题
    redis_client.setex('wechat:access_token', expires_in - 300, access_token)
    
    return access_token


def code2session(code):
    """微信小程序登录凭证校验"""
    # 获取配置
    appid = current_app.config['WECHAT_APPID']
    secret = current_app.config['WECHAT_SECRET']
    
    # 请求微信API
    url = f'https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code'
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception('微信服务器请求失败')
    
    data = response.json()
    
    if 'errcode' in data and data['errcode'] != 0:
        raise Exception(f'登录凭证校验失败: {data["errmsg"]}')
    
    return data 