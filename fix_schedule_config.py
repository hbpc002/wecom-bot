#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修改定时发送配置的脚本
1. 将定时时间从9点改到10点
2. 修复日期检查逻辑：定时任务应该检查前一天的数据并发送前一天的数据
"""

import os
import re


def modify_web_server():
    """修改 web_server.py"""
    filepath = 'web_server.py'
    print(f"正在修改 {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改默认定时时间
    content = re.sub(
        r'scheduled_task_time = "09:00"',
        r'scheduled_task_time = "10:00"',
        content
    )
    
    # 修改API默认值
    content = re.sub(
        r"scheduled_task_time = data\.get\('time', '09:00'\)",
        r"scheduled_task_time = data.get('time', '10:00')",
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ {filepath} 修改完成")


def modify_index_html():
    """修改 templates/index.html"""
    filepath = 'templates/index.html'
    print(f"正在修改 {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改默认时间输入框的值
    content = re.sub(
        r'value="09:00"',
        r'value="10:00"',
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ {filepath} 修改完成")


def modify_main_py():
    """修改 main.py"""
    filepath = 'main.py'
    print(f"正在修改 {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到并替换 get_today_files 方法
    in_get_today_files = False
    method_start = -1
    method_end = -1
    
    for i, line in enumerate(lines):
        if 'def get_today_files(self):' in line:
            in_get_today_files = True
            method_start = i
        elif in_get_today_files and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            method_end = i
            break
        elif in_get_today_files and 'def ' in line and 'get_today_files' not in line:
            method_end = i
            break
    
    # 替换 get_today_files 方法为 get_yesterday_data
    if method_start >= 0 and method_end >= 0:
        new_method = '''    def get_yesterday_data(self):
        """获取前一天的数据（用于定时发送）
        
        当天上传的是前一天的数据，所以定时任务应该检查前一天有没有数据
        """
        yesterday = (datetime.now() - timedelta(days=1)).date()
        
        # 检查数据库中前一天有没有数据
        if hasattr(self, 'db') and self.db:
            try:
                daily_data = self.db.get_daily_summary(yesterday)
                if daily_data:
                    logging.info(f"找到前一天({yesterday})的数据，共 {len(daily_data)} 条记录")
                    return yesterday, daily_data
                else:
                    logging.info(f"前一天({yesterday})没有数据")
                    return None, None
            except Exception as e:
                logging.error(f"查询前一天数据失败: {e}")
                return None, None
        else:
            logging.warning("数据库未连接，无法查询前一天数据")
            return None, None
        
'''
        lines[method_start:method_end] = [new_method]
    
    # 重新读取lines（因为行号可能已改变）
    content = ''.join(lines)
    
    # 替换 process_daily_files 方法
    process_daily_files_pattern = r'(    def process_daily_files\(self\):.*?\n)(.*?)((?=\n    def )|(?=\ndef )|$)'
    
    new_process_daily_files = '''    def process_daily_files(self):
        """处理前一天的数据并发送（用于定时任务）
        
        因为当天上传的是前一天的数据，所以定时任务应该检查前一天有没有数据
        如果有，就生成报表并发送前一天的数据
        """
        logging.info("开始检查前一天的数据...")
        
        yesterday, daily_data = self.get_yesterday_data()
        if not yesterday or not daily_data:
            logging.info("前一天没有数据，跳过定时发送")
            return
        
        logging.info(f"前一天({yesterday})找到 {len(daily_data)} 条数据，准备生成报表...")
        
        try:
            # 构造报表数据格式
            report_data_dict = {}
            for item in daily_data:
                key = (item['team'], item['name'], item['account'])
                report_data_dict[key] = item['count']
            
            total_operations = sum(item['count'] for item in daily_data)
            
            # 获取月累计数据
            monthly_data = None
            try:
                year_month = yesterday.strftime('%Y-%m')
                monthly_summary = self.db.get_monthly_summary(year_month)
                monthly_data = {item['account']: item['total_count'] for item in monthly_summary}
            except Exception as e:
                logging.error(f"获取月累计数据失败: {e}")
            
            # 生成报表
            result = ReportGenerator.generate_report(
                report_data_dict, yesterday, total_operations,
                f"scheduled_{yesterday}.zip", self.file_dir, 'both', monthly_data
            )
            
            # 发送到企业微信
            if self.send_to_wechat(result):
                logging.info(f"前一天({yesterday})的数据报表发送成功")
            else:
                logging.error(f"前一天({yesterday})的数据报表发送失败")
                
        except Exception as e:
            logging.error(f"处理前一天数据时出错: {e}")
'''
    
    content = re.sub(process_daily_files_pattern, new_process_daily_files + '\n', content, flags=re.DOTALL)
    
    # 修改定时时间
    content = re.sub(
        r'schedule\.every\(\)\.day\.at\("09:00"\)',
        r'schedule.every().day.at("10:00")',
        content
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ {filepath} 修改完成")


def main():
    """主函数"""
    print("=" * 60)
    print("开始修改定时发送配置...")
    print("=" * 60)
    
    try:
        modify_web_server()
        modify_index_html()
        modify_main_py()
        
        print("=" * 60)
        print("✓ 所有文件修改完成！")
        print("=" * 60)
        print("\n修改内容:")
        print("1. 定时时间从 9:00 改为 10:00")
        print("2. 定时任务逻辑修改为：检查前一天的数据，发送前一天的数据")
        print("\n请重启 web_server.py 以使更改生效")
        
    except Exception as e:
        print(f"✗ 修改失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
