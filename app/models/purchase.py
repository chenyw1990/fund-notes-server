from datetime import datetime
from app.extensions import db

class Purchase(db.Model):
    """基金购买记录模型"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    fund_id = db.Column(db.Integer, db.ForeignKey('funds.id'))
    amount = db.Column(db.Float)  # 购买金额
    share = db.Column(db.Float)   # 份额
    price = db.Column(db.Float)   # 购买单价
    purchase_date = db.Column(db.Date)  # 购买日期
    before_cutoff = db.Column(db.Boolean, default=True)  # 是否在15:00截止时间前购买
    fee = db.Column(db.Float, default=0.0)  # 手续费
    notes = db.Column(db.Text)    # 购买备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'fund_id': self.fund_id,
            'amount': self.amount,
            'share': self.share,
            'price': self.price,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'before_cutoff': self.before_cutoff,
            'fee': self.fee,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 