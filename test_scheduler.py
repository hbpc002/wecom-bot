"""
测试脚本 - 验证定时任务功能

此脚本用于验证定时任务的启用/停用功能是否正常工作
"""
import schedule
import threading
import time
from datetime import datetime

# 模拟全局变量
scheduler_running = False
scheduler_thread = None

def test_scheduled_task():
    """测试任务函数"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"✓ 定时任务执行成功! 时间: {current_time}")

def run_scheduler():
    """调度器运行函数"""
    global scheduler_running
    print("调度器线程已启动")
    
    while scheduler_running:
        schedule.run_pending()
        time.sleep(1)
    
    print("调度器线程已停止")

def start_scheduler():
    """启动调度器"""
    global scheduler_thread, scheduler_running
    
    if scheduler_running:
        print("警告: 调度器已在运行")
        return
    
    scheduler_running = True
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✓ 调度器已启动")

def stop_scheduler():
    """停止调度器"""
    global scheduler_thread, scheduler_running
    
    if not scheduler_running:
        print("调度器未运行")
        return
    
    scheduler_running = False
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=5)
    print("✓ 调度器已停止")

if __name__ == "__main__":
    print("=" * 50)
    print("定时任务功能测试")
    print("=" * 50)
    
    # 测试1: 创建定时任务
    print("\n[测试1] 创建定时任务...")
    # 获取当前时间后的2秒
    test_time = (datetime.now().replace(second=0, microsecond=0).strftime("%H:%M"))
    next_minute = (datetime.now().replace(second=0, microsecond=0)).strftime("%H:%M")
    
    # 每分钟执行一次(用于快速测试)
    schedule.every().minute.do(test_scheduled_task)
    print(f"✓ 已创建任务: 每分钟执行一次")
    
    # 测试2: 启动调度器
    print("\n[测试2] 启动调度器...")
    start_scheduler()
    
    # 测试3: 等待任务执行
    print(f"\n[测试3] 等待任务执行 (将在下一分钟 {next_minute}:00 时触发)...")
    print("等待中...(最多等待70秒)")
    time.sleep(70)
    
    # 测试4: 停止调度器
    print("\n[测试4] 停止调度器...")
    stop_scheduler()
    
    # 测试5: 清除任务
    print("\n[测试5] 清除所有任务...")
    schedule.clear()
    print("✓ 所有任务已清除")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
