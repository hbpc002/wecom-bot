"""
添加Webhook日志记录的脚本
用于诊断生产环境发送按钮问题
"""

def add_logging_to_main_py():
    """在main.py的send_to_wechat方法中添加日志"""
    file_path = 'main.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找send_to_wechat方法的开始
    target1 = '    def send_to_wechat(self, report_data):\n        """发送报表到企业微信群，只发送图片"""\n        if not report_data:'
    
    replacement1 = '''    def send_to_wechat(self, report_data):
        """发送报表到企业微信群，只发送图片"""
        # 记录使用的webhook (隐藏部分key以保护安全)
        masked_webhook = self.webhook_url[:60] + '...' if len(self.webhook_url) > 60 else self.webhook_url
        logging.info(f"send_to_wechat 使用webhook: {masked_webhook}")
        
        if not report_data:'''
    
    if target1 in content:
        content = content.replace(target1, replacement1)
        print("✓ 已在send_to_wechat开头添加webhook日志")
    else:
        print("✗ 未找到send_to_wechat方法开头")
    
    # 修改base64成功的日志
    target2 = '                                logging.info("图片报表发送成功(base64方式)")'
    replacement2 = '                                logging.info(f"图片报表发送成功(base64方式) -> {masked_webhook}")'
    
    if target2 in content:
        content = content.replace(target2, replacement2)
        print("✓ 已更新base64成功日志")
    else:
        print("✗ 未找到base64成功日志")
    
    # 修改media_id成功的日志
    target3 = '                                        logging.info("图片报表发送成功")'
    replacement3 = '                                        logging.info(f"图片报表发送成功 -> {masked_webhook}")'
    
    if target3 in content:
        content = content.replace(target3, replacement3)
        print("✓ 已更新media_id成功日志")
    else:
        print("✗ 未找到media_id成功日志")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n已更新 {file_path}")


def add_logging_to_web_server_py():
    """在web_server.py的send_to_wecom端点中添加日志"""
    file_path = 'web_server.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到send_to_wecom函数并添加日志
    modified = False
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # 在获取参数后添加日志
        if 'env = data.get(\'env\', \'test\')  # test 或 prod' in line:
            # 检查下一行是否已经有日志
            if i + 1 < len(lines) and 'logging.info(f"收到发送请求' not in lines[i + 1]:
                new_lines.append('        \n')
                new_lines.append('        logging.info(f"收到发送请求 - 日期: {date_str}, 环境: {env}")\n')
                modified = True
                print("✓ 已添加请求接收日志")
        
        # 在选择webhook后添加日志
        elif 'webhook_url = WEBHOOK_TEST if env == \'test\' else WEBHOOK_PROD' in line:
            # 检查下一行是否已经有日志
            if i + 1 < len(lines) and 'masked_url' not in lines[i + 1]:
                new_lines.append('        # 记录使用的webhook (隐藏部分key)\n')
                new_lines.append('        masked_url = webhook_url[:60] + \'...\' if len(webhook_url) > 60 else webhook_url\n')
                new_lines.append('        logging.info(f"环境: {env}, 使用webhook: {masked_url}")\n')
                new_lines.append('        logging.info(f"准备发送到{\'生产\' if env == \'prod\' else \'测试\'}环境")\n')
                modified = True
                print("✓ 已添加webhook选择日志")
        
        # 在发送成功后添加详细日志
        elif '        if reporter.send_to_wechat(result):' in line:
            new_lines.append(lines[i + 1])  # env_name = ...
            i += 1
            # 检查是否已经有详细日志
            if i + 1 < len(lines) and '✓ 报表成功发送到' not in lines[i + 1]:
                new_lines.append('            logging.info(f"✓ 报表成功发送到{env_name} (webhook: {masked_url})")\n')
                modified = True
                print("✓ 已添加发送成功详细日志")
        
        # 在发送失败分支添加日志
        elif '        else:' in line and i > 0 and 'reporter.send_to_wechat' in lines[i - 2]:
            # 检查下一行是否已有详细日志
            if i + 1 < len(lines) and '✗ 报表发送失败' not in lines[i + 1]:
                new_lines.append('            logging.error(f"✗ 报表发送失败 - 环境: {env_name}")\n')
                modified = True
                print("✓ 已添加发送失败日志")
        
        i += 1
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"\n已更新 {file_path}")
    else:
        print(f"\n{file_path} 已包含所需日志或无需修改")


if __name__ == '__main__':
    print("=" * 60)
    print("添加Webhook调试日志")
    print("=" * 60)
    print()
    
    print("正在修改 main.py...")
    add_logging_to_main_py()
    print()
    
    print("正在修改 web_server.py...")
    add_logging_to_web_server_py()
    print()
    
    print("=" * 60)
    print("完成！请重启 web_server.py 以使更改生效")
    print("=" * 60)
