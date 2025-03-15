from datetime import datetime
from app.extensions import db

class Note(db.Model):
    """基金笔记模型"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5星评分
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fund_id = db.Column(db.Integer, db.ForeignKey('funds.id'))
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'rating': self.rating,
            'user_id': self.user_id,
            'fund_id': self.fund_id,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 