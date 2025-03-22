#!/usr/bin/env python
"""
更新基金详细信息的命令行工具

用法:
    python update_fund_details.py               # 更新所有基金的详细信息
    python update_fund_details.py -c 000001     # 更新指定基金的详细信息
    python update_fund_details.py -v            # 显示详细日志
"""

import argparse
import sys
import logging
from app import create_app
from app.models import Fund
from app.services.fund_service import fetch_fund_details

def setup_logging(verbose=False):
    """设置日志级别"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # 获取根日志记录器并设置级别
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 检查是否已有处理器
    if not root_logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        logging.info("临时日志系统已初始化")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='更新基金详细信息')
    parser.add_argument('-c', '--code', help='基金代码，不提供则更新所有基金')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 设置初始日志级别
    setup_logging(args.verbose)
    
    # 创建应用上下文
    logging.info("正在创建Flask应用...")
    app = create_app()
    
    with app.app_context():
        try:
            logging.info("开始更新基金详细信息...")
            
            # 准备参数
            if args.code:
                funds = Fund.query.filter_by(code=args.code).all()
                logging.info(f"更新基金: {args.code}")
            else:
                funds = Fund.query.all()
                logging.info(f"更新所有基金: 共 {len(funds)} 个")
            
            updated_count = 0
            
            # 逐个更新基金信息
            for fund in funds:
                logging.info(f"正在更新基金: {fund.code} - {fund.name}")
                updated_fund = fetch_fund_details(fund.code)
                
                if updated_fund:
                    updated_count += 1
                    logging.info(f"成功更新基金: {fund.code} - {fund.name}")
                else:
                    logging.warning(f"无法获取基金详情: {fund.code} - {fund.name}")
            
            logging.info(f"成功更新 {updated_count} 个基金的详细信息")
            return 0
            
        except Exception as e:
            logging.error(f"更新基金详情失败: {str(e)}")
            return 1

if __name__ == '__main__':
    sys.exit(main()) 