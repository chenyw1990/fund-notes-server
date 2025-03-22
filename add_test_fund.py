#!/usr/bin/env python
"""
添加测试基金到数据库

用法:
    python add_test_fund.py
"""

from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import Fund
from app.services.fund_service import fetch_fund_details
import logging

def add_test_fund():
    """添加测试基金到数据库"""
    # 创建应用上下文
    app = create_app()
    
    with app.app_context():
        # 测试基金代码
        fund_codes = ['110022', '005827', '000001', '110020']
        
        funds_added = 0
        
        for code in fund_codes:
            existing_fund = Fund.query.filter_by(code=code).first()
            if not existing_fund:
                # 尝试从API获取基金详情
                fund = fetch_fund_details(code)
                if fund:
                    funds_added += 1
                    print(f"添加基金: {fund.code} - {fund.name}")
                else:
                    # 如果API获取失败，使用基本信息创建
                    fund = Fund(
                        code=code,
                        name=f"基金{code}"
                    )
                    db.session.add(fund)
                    funds_added += 1
                    print(f"添加基金: {fund.code} - {fund.name} (基本信息)")
        
        if funds_added > 0:
            db.session.commit()
            print(f"成功添加 {funds_added} 个测试基金")
        else:
            print("所有测试基金已存在，无需添加")

if __name__ == '__main__':
    add_test_fund() 