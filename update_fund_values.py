#!/usr/bin/env python
"""
更新基金净值数据的命令行工具

用法:
    python update_fund_values.py                  # 更新所有基金的净值数据
    python update_fund_values.py -c 000001        # 更新指定基金的净值数据
    python update_fund_values.py -d 30            # 更新最近30天的净值数据
    python update_fund_values.py -s 2023-01-01 -e 2023-12-31  # 更新指定日期范围的净值数据
    python update_fund_values.py -v               # 显示详细日志
"""

import argparse
import sys
import logging
from datetime import datetime
from flask import Flask
from app import create_app
from app.services.fund_value_service import fetch_fund_value

def setup_logging(verbose=False):
    """设置日志"""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='更新基金净值数据')
    parser.add_argument('-c', '--code', help='基金代码，不提供则更新所有基金')
    parser.add_argument('-d', '--days', type=int, help='获取最近几天的数据')
    parser.add_argument('-s', '--start-date', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('-e', '--end-date', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    setup_logging(args.verbose)
    
    # 创建应用上下文
    app = create_app()
    with app.app_context():
        try:
            logging.info("开始更新基金净值数据...")
            
            # 准备参数
            params = {}
            if args.code:
                params['fund_code'] = args.code
                logging.info(f"更新基金: {args.code}")
            else:
                logging.info("更新所有基金")
            
            if args.start_date:
                try:
                    # 验证日期格式
                    datetime.strptime(args.start_date, '%Y-%m-%d')
                    params['start_date'] = args.start_date
                    logging.info(f"开始日期: {args.start_date}")
                except ValueError:
                    logging.error("开始日期格式无效，应为YYYY-MM-DD")
                    return 1
            
            if args.end_date:
                try:
                    # 验证日期格式
                    datetime.strptime(args.end_date, '%Y-%m-%d')
                    params['end_date'] = args.end_date
                    logging.info(f"结束日期: {args.end_date}")
                except ValueError:
                    logging.error("结束日期格式无效，应为YYYY-MM-DD")
                    return 1
            
            # 执行更新
            count = fetch_fund_value(**params)
            
            logging.info(f"成功更新 {count} 条净值数据")
            return 0
            
        except Exception as e:
            logging.error(f"更新净值数据失败: {str(e)}")
            return 1

if __name__ == '__main__':
    sys.exit(main()) 