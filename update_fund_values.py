#!/usr/bin/env python
"""
更新基金净值数据的命令行工具

用法:
    python update_fund_values.py                  # 更新所有基金的全部历史净值数据
    python update_fund_values.py -c 000001        # 更新指定基金的全部历史净值数据
    python update_fund_values.py -d 30            # 仅更新最近30天的净值数据
    python update_fund_values.py -s 2023-01-01 -e 2023-12-31  # 更新指定日期范围的净值数据
    python update_fund_values.py -v               # 显示详细日志
"""

import argparse
import sys
import logging
from datetime import datetime, timedelta
from flask import Flask
from app import create_app
from app.services.fund_value_service import fetch_fund_value

def setup_logging(verbose=False):
    """设置日志级别
    
    如果Flask应用已经配置了日志，则只调整日志级别
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # 获取根日志记录器并设置级别
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 如果没有处理器，添加一个简单的控制台处理器
    # 这种情况应该只在未通过Flask应用运行时发生
    if not root_logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        logging.info("临时日志系统已初始化，将在Flask应用启动后被替换")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='更新基金净值数据')
    parser.add_argument('-c', '--code', help='基金代码，不提供则更新所有基金')
    parser.add_argument('-d', '--days', type=int, help='仅获取最近几天的数据，不提供则获取全部历史数据')
    parser.add_argument('-s', '--start-date', help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('-e', '--end-date', help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 设置初始日志级别
    setup_logging(args.verbose)
    
    # 创建应用上下文 - 这将配置Flask的日志
    logging.info("正在创建Flask应用...")
    app = create_app()
    
    # 再次调整日志级别以匹配命令行参数
    setup_logging(args.verbose)
    
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
            
            # 处理日期参数
            if args.days:
                # 如果指定了天数，计算开始日期
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=args.days)
                params['start_date'] = start_date.strftime('%Y-%m-%d')
                params['end_date'] = end_date.strftime('%Y-%m-%d')
                logging.info(f"获取最近 {args.days} 天的数据: {params['start_date']} 到 {params['end_date']}")
            else:
                # 如果指定了具体日期范围
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
                
                if not args.start_date and not args.end_date:
                    logging.info("未指定日期范围，将获取基金全部历史净值数据")
            
            # 执行更新
            count = fetch_fund_value(**params)
            
            logging.info(f"成功更新 {count} 条净值数据")
            return 0
            
        except Exception as e:
            logging.error(f"更新净值数据失败: {str(e)}")
            return 1

if __name__ == '__main__':
    sys.exit(main()) 