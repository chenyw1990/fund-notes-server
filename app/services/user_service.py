from app.extensions import db
from app.models import User, Note
from app.utils.wechat import code2session

def get_user_by_openid(openid):
    """通过openid获取用户"""
    return User.query.filter_by(openid=openid).first()


def get_user_by_username(username):
    """通过用户名获取用户"""
    return User.query.filter_by(username=username).first()


def get_user_by_email(email):
    """通过邮箱获取用户"""
    return User.query.filter_by(email=email).first()


def create_user(username, password, email=None, openid=None, avatar=None):
    """创建用户"""
    user = User(
        username=username,
        email=email,
        openid=openid,
        avatar=avatar
    )
    user.password = password
    
    db.session.add(user)
    db.session.commit()
    
    return user


def update_user(user, username=None, email=None, avatar=None):
    """更新用户信息"""
    if username and username != user.username:
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return False, '用户名已存在'
        user.username = username
    
    if email and email != user.email:
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return False, '邮箱已存在'
        user.email = email
    
    if avatar:
        user.avatar = avatar
    
    db.session.commit()
    
    return True, '更新成功'


def wechat_login(code):
    """微信小程序登录"""
    try:
        # 调用微信API获取openid
        wx_data = code2session(code)
        openid = wx_data['openid']
        
        # 查找用户
        user = get_user_by_openid(openid)
        
        # 如果用户不存在，则创建新用户
        if user is None:
            username = f'wx_user_{openid[-8:]}'
            user = create_user(
                username=username,
                password='',  # 微信用户不需要密码
                openid=openid
            )
        
        return user
    except Exception as e:
        return None


def get_user_notes(user_id, page=1, per_page=10):
    """获取用户的笔记"""
    pagination = Note.query.filter_by(
        user_id=user_id
    ).order_by(
        Note.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return pagination 