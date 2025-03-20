from flask import Markup
from app.models import User, Fund

def get_user(user_id):
    """获取用户信息"""
    return User.query.get(user_id)

def get_fund(fund_id):
    """获取基金信息"""
    return Fund.query.get(fund_id)

def nl2br(value):
    """将换行符转换为<br>标签"""
    return Markup(value.replace('\n', '<br>'))

def register_template_utils(app):
    """注册模板工具函数"""
    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.globals.update({
        'get_user': get_user,
        'get_fund': get_fund
    }) 