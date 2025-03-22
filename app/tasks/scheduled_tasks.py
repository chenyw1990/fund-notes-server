import logging
from datetime import datetime, time, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.fund_value_service import fetch_fund_value

# 使用名称获取logger，但不进行额外配置
logger = logging.getLogger(__name__)

# 创建定时任务调度器
scheduler = BackgroundScheduler()

def setup_scheduled_tasks():
    """设置定时任务"""
    # 添加每日更新基金净值的任务
    # 设置为每天下午18:00执行，此时大部分基金净值已更新
    scheduler.add_job(
        update_all_fund_values,
        trigger=CronTrigger(hour=18, minute=0),
        id='update_fund_values',
        replace_existing=True,
        misfire_grace_time=3600  # 允许的执行延迟时间（秒）
    )
    
    # 也可以添加其他定时任务
    
    # 启动调度器
    scheduler.start()
    logger.info("定时任务调度器已启动")

def update_all_fund_values():
    """更新所有基金的净值数据"""
    try:
        logger.info("开始执行基金净值更新任务")
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # 获取昨天的基金净值数据
        # 由于基金净值通常是T+1发布，所以获取昨天的数据
        count = fetch_fund_value(
            start_date=yesterday.strftime('%Y-%m-%d'),
            end_date=today.strftime('%Y-%m-%d')
        )
        
        logger.info(f"基金净值更新完成，共更新 {count} 条记录")
    except Exception as e:
        logger.error(f"基金净值更新任务出错: {str(e)}")

def shutdown_scheduler():
    """关闭定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭") 