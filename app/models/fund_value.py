from datetime import datetime
from app.extensions import db

class FundValue(db.Model):
    """基金每日净值信息模型"""
    __tablename__ = 'fund_values'
    
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey('funds.id'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)  # 净值日期
    net_value = db.Column(db.Float, nullable=False)  # 单位净值
    accumulated_value = db.Column(db.Float, nullable=False)  # 累计净值
    daily_change = db.Column(db.Float)  # 日涨跌幅（百分比）
    last_week_change = db.Column(db.Float)  # 最近一周涨跌幅（百分比）
    last_month_change = db.Column(db.Float)  # 最近一月涨跌幅（百分比）
    last_year_change = db.Column(db.Float)  # 最近一年涨跌幅（百分比）
    since_inception_change = db.Column(db.Float)  # 成立以来涨跌幅（百分比）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 添加唯一约束，确保每个基金每天只有一个净值记录
    __table_args__ = (
        db.UniqueConstraint('fund_id', 'date', name='uix_fund_date'),
    )
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'fund_id': self.fund_id,
            'date': self.date.isoformat(),
            'net_value': self.net_value,
            'accumulated_value': self.accumulated_value,
            'daily_change': self.daily_change,
            'last_week_change': self.last_week_change,
            'last_month_change': self.last_month_change,
            'last_year_change': self.last_year_change,
            'since_inception_change': self.since_inception_change,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 