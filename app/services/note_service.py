from app.extensions import db
from app.models import Note, Fund, User
from app.utils.redis_utils import cache_delete, cache_clear_pattern

def get_note_by_id(note_id):
    """通过ID获取笔记"""
    return Note.query.get(note_id)


def get_notes_by_user(user_id, page=1, per_page=10):
    """获取用户的笔记"""
    pagination = Note.query.filter_by(
        user_id=user_id
    ).order_by(
        Note.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return pagination


def get_notes_by_fund(fund_id, page=1, per_page=10, public_only=True):
    """获取基金的笔记"""
    query = Note.query.filter_by(fund_id=fund_id)
    
    if public_only:
        query = query.filter_by(is_public=True)
    
    pagination = query.order_by(
        Note.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return pagination


def create_note(user_id, fund_id, title, content, rating=None, is_public=True):
    """创建笔记"""
    # 检查基金是否存在
    fund = Fund.query.get(fund_id)
    if fund is None:
        return None, '基金不存在'
    
    # 创建笔记
    note = Note(
        title=title,
        content=content,
        rating=rating,
        user_id=user_id,
        fund_id=fund_id,
        is_public=is_public
    )
    
    db.session.add(note)
    db.session.commit()
    
    # 清除相关缓存
    cache_clear_pattern(f'fund_notes:{fund_id}:*')
    
    return note, '笔记创建成功'


def update_note(note, title=None, content=None, rating=None, is_public=None):
    """更新笔记"""
    if title:
        note.title = title
    
    if content:
        note.content = content
    
    if rating is not None:
        note.rating = rating
    
    if is_public is not None:
        note.is_public = is_public
    
    db.session.commit()
    
    # 清除相关缓存
    cache_clear_pattern(f'fund_notes:{note.fund_id}:*')
    
    return note


def delete_note(note):
    """删除笔记"""
    fund_id = note.fund_id
    
    db.session.delete(note)
    db.session.commit()
    
    # 清除相关缓存
    cache_clear_pattern(f'fund_notes:{fund_id}:*')
    
    return True


def get_note_with_details(note_id):
    """获取笔记详情，包括作者和基金信息"""
    note = get_note_by_id(note_id)
    
    if note is None:
        return None
    
    # 构建响应
    note_data = note.to_dict()
    
    # 添加作者和基金信息
    user = User.query.get(note.user_id)
    fund = Fund.query.get(note.fund_id)
    
    if user:
        note_data['author'] = {
            'id': user.id,
            'username': user.username,
            'avatar': user.avatar
        }
    
    if fund:
        note_data['fund'] = {
            'id': fund.id,
            'code': fund.code,
            'name': fund.name
        }
    
    return note_data 