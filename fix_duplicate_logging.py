"""
修复web_server.py中的重复日志问题
"""

def fix_duplicate_logging():
    """移除web_server.py中重复的日志语句"""
    file_path = 'web_server.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到并移除重复的日志语句
    # 原始内容有两组完全相同的日志
    duplicate_section = '''        logging.info(f"收到发送请求 - 日期: {date_str}, 环境: {env}")
        
        logging.info(f"收到发送请求 - 日期: {date_str}, 环境: {env}")
        '''
    
    if duplicate_section in content:
        # 只保留一个
        content = content.replace(duplicate_section, '        logging.info(f"收到发送请求 - 日期: {date_str}, 环境: {env}")\n        \n', 1)
        print("✓ 移除了第一组重复的日志语句")
    
    # 移除第二组重复
    duplicate_section2 = '''        # 记录使用的webhook (隐藏部分key)
        masked_url = webhook_url[:60] + '...' if len(webhook_url) > 60 else webhook_url
        logging.info(f"环境: {env}, 使用webhook: {masked_url}")
        logging.info(f"准备发送到{'生产' if env == 'prod' else '测试'}环境")
        # 记录使用的webhook (隐藏部分key)
        masked_url = webhook_url[:60] + '...' if len(webhook_url) > 60 else webhook_url
        logging.info(f"环境: {env}, 使用webhook: {masked_url}")
        logging.info(f"准备发送到{'生产' if env == 'prod' else '测试'}环境")'''
    
    replacement2 = '''        # 记录使用的webhook (隐藏部分key)
        masked_url = webhook_url[:60] + '...' if len(webhook_url) > 60 else webhook_url
        logging.info(f"环境: {env}, 使用webhook: {masked_url}")
        logging.info(f"准备发送到{'生产' if env == 'prod' else '测试'}环境")'''
    
    if duplicate_section2 in content:
        content = content.replace(duplicate_section2, replacement2, 1)
        print("✓ 移除了第二组重复的日志语句")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n已更新 {file_path}")


if __name__ == '__main__':
    print("=" * 60)
    print("修复重复的日志语句")
    print("=" * 60)
    print()
    
    fix_duplicate_logging()
    
    print()
    print("=" * 60)
    print("完成！请重启 web_server.py")
    print("=" * 60)
