from datetime import datetime
from app.extensions import db

class Fund(db.Model):
    """基金模型"""
    __tablename__ = 'funds'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, index=True)
    name = db.Column(db.String(100), index=True)
    type = db.Column(db.String(50))
    manager = db.Column(db.String(50))
    company = db.Column(db.String(100))
    inception_date = db.Column(db.Date)
    size = db.Column(db.Float)  # 基金规模（亿元）
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    notes = db.relationship('Note', backref='fund', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'type': self.type,
            'manager': self.manager,
            'company': self.company,
            'inception_date': self.inception_date.isoformat() if self.inception_date else None,
            'size': self.size,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 