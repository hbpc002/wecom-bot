import logging
import json
import requests
from main import CallRecordingReporter

# 配置日志 - 同时输出到文件和控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_message.log', encoding='utf-8'),
        logging.StreamHandler()  # 添加控制台输出
    ]
)

def test_message_format():
    """测试不同的消息格式"""
    
    # 企业微信机器人webhook
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=2645bd5f-4802-45dc-8fd7-c46f67d317a9"
    
    # 创建报表处理器
    reporter = CallRecordingReporter(webhook_url)
    
    # 测试1: 纯文本消息（带emoji）
    logging.info("=== 测试1: 纯文本消息（带emoji）===")
    text_message = {
        "msgtype": "text",
        "text": {
            "content": "📊 听录音统计报表\n📅 日期: 2025-11-19\n\n## 📈 汇总信息\n- **总操作次数**: 100\n- **参与人数**: 10\n- **平均每人操作次数**: 10.0"
        }
    }
    
    response = requests.post(webhook_url, json=text_message, timeout=10)
    logging.info(f"纯文本消息响应: {response.status_code}, {response.json()}")
    
    # 测试2: 纯文本消息（不带markdown格式）
    logging.info("=== 测试2: 纯文本消息（不带markdown格式）===")
    plain_text_message = {
        "msgtype": "text",
        "text": {
            "content": "听录音统计报表\n日期: 2025-11-19\n\n汇总信息\n- 总操作次数: 100\n- 参与人数: 10\n- 平均每人操作次数: 10.0"
        }
    }
    
    response = requests.post(webhook_url, json=plain_text_message, timeout=10)
    logging.info(f"纯文本消息（无markdown）响应: {response.status_code}, {response.json()}")
    
    # 测试3: 先发送图片，再发送文本
    logging.info("=== 测试3: 先发送图片，再发送文本 ===")
    
    # 尝试发送一个测试图片（如果存在）
    import os
    test_image_path = "file/test_image.png"
    if os.path.exists(test_image_path):
        # 转换图片为base64和md5
        base64_data, md5_hash = reporter._image_to_base64(test_image_path)
        
        if base64_data and md5_hash:
            # 发送图片消息
            image_message = {
                "msgtype": "image",
                "image": {
                    "base64": base64_data,
                    "md5": md5_hash
                }
            }
            
            response = requests.post(webhook_url, json=image_message, timeout=10)
            logging.info(f"图片消息响应: {response.status_code}, {response.json()}")
            
            # 等待1秒后发送文本
            import time
            time.sleep(1)
            
            # 发送文本消息
            response = requests.post(webhook_url, json=text_message, timeout=10)
            logging.info(f"图片后文本消息响应: {response.status_code}, {response.json()}")
        else:
            logging.error("无法处理测试图片")
    else:
        logging.warning("测试图片不存在，跳过图片发送测试")
    
    # 测试4: 使用markdown格式
    logging.info("=== 测试4: 使用markdown格式 ===")
    markdown_message = {
        "msgtype": "markdown",
        "markdown": {
            "content": "📊 听录音统计报表\n📅 日期: 2025-11-19\n\n## 📈 汇总信息\n- **总操作次数**: 100\n- **参与人数**: 10\n- **平均每人操作次数**: 10.0"
        }
    }
    
    response = requests.post(webhook_url, json=markdown_message, timeout=10)
    logging.info(f"markdown消息响应: {response.status_code}, {response.json()}")

if __name__ == "__main__":
    test_message_format()