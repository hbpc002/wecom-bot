import csv
import zipfile
import os
import re
import chardet
import requests
import json
import base64
import hashlib
from datetime import datetime, timedelta
import schedule
import time
import logging
from report_generator import ReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8')
    ]
)

class CallRecordingReporter:
    def __init__(self, webhook_url, file_dir='file'):
        self.webhook_url = webhook_url
        self.file_dir = file_dir
        self.processed_files = set()
        self.team_mapping = {}
        self.load_team_mapping()
        
    def load_team_mapping(self):
        """加载团队映射文件"""
        try:
            mapping_file = os.path.join(self.file_dir, 'team_mapping.csv')
            if not os.path.exists(mapping_file):
                logging.warning(f"团队映射文件不存在: {mapping_file}")
                return
                
            with open(mapping_file, 'rb') as f:
                raw_data = f.read()
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result['encoding'] or 'gbk'
                
            with open(mapping_file, 'r', encoding=encoding) as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # 跳过标题行
                for row in reader:
                    if len(row) >= 2:
                        team_name, account_id = row[0].strip(), row[1].strip()
                        self.team_mapping[account_id] = team_name
                        
            logging.info(f"已加载 {len(self.team_mapping)} 个团队映射")
            
        except Exception as e:
            logging.error(f"加载团队映射文件失败: {e}")
            
    def get_today_files(self):
        """获取今天的新zip文件"""
        today = datetime.now().strftime('%Y%m%d')
        today_files = []
        
        if not os.path.exists(self.file_dir):
            os.makedirs(self.file_dir)
            return today_files
            
        for filename in os.listdir(self.file_dir):
            if filename.endswith('.zip') and today in filename:
                if filename not in self.processed_files:
                    today_files.append(filename)
                    
        return today_files
        
    def extract_date_from_filename(self, filename):
        """从文件名中提取日期"""
        # 匹配文件名中的日期格式，如 20251114155531338
        date_pattern = r'(\d{8})\d{6}'
        match = re.search(date_pattern, filename)
        if match:
            date_str = match.group(1)
            return datetime.strptime(date_str, '%Y%m%d').date()
        return None
        
    def process_zip_file(self, zip_filename):
        """处理单个zip文件"""
        try:
            zip_path = os.path.join(self.file_dir, zip_filename)
            logging.info(f"正在处理文件: {zip_filename}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 获取zip中的csv文件
                csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                if not csv_files:
                    logging.warning(f"zip文件中没有找到csv文件: {zip_filename}")
                    return None
                    
                csv_filename = csv_files[0]
                
                # 读取csv文件内容
                with zip_ref.open(csv_filename, 'r') as csvfile:
                    raw_data = csvfile.read()
                    
                    # 检测编码
                    encoding_result = chardet.detect(raw_data)
                    encoding = encoding_result['encoding'] or 'gbk'
                    logging.info(f"检测到编码: {encoding}")
                    
                    # 尝试多种编码解码
                    content = None
                    encodings_to_try = [encoding, 'gbk', 'utf-8', 'gb2312', 'big5']
                    
                    for enc in encodings_to_try:
                        try:
                            content = raw_data.decode(enc)
                            logging.info(f"成功使用编码: {enc}")
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if content is None:
                        content = raw_data.decode('gbk', errors='ignore')
                        logging.warning("使用忽略错误的方式解码")
                    lines = content.splitlines()
                    
                    # 解析CSV数据
                    reader = csv.reader(lines)
                    header = next(reader, None)
                    if not header:
                        logging.warning(f"CSV文件没有标题行: {csv_filename}")
                        return None
                        
                    logging.info(f"CSV标题: {header}")
                    
                    # 统计数据
                    report_data = {}
                    total_operations = 0
                    
                    for row_num, row in enumerate(reader, start=2):  # 从第2行开始计数
                        try:
                            if len(row) < 6:  # 确保有足够的列
                                continue
                                
                            account = row[1].strip()  # 帐号在第2列
                            name = row[2].strip()     # 姓名在第3列
                            operation_time = row[5].strip()  # 操作时间在第6列
                            
                            # 跳过空行
                            if not account or not name:
                                continue
                                
                            logging.debug(f"处理数据: 账号={account}, 姓名={name}, 时间={operation_time}")
                            
                            # 如果账号在团队映射中，则统计
                            if account in self.team_mapping:
                                team = self.team_mapping[account]
                                key = (team, name, account)
                                if key not in report_data:
                                    report_data[key] = 0
                                report_data[key] += 1
                                total_operations += 1
                                
                        except Exception as e:
                            logging.warning(f"跳过第{row_num}行数据: {e}, 行内容: {row}")
                            continue
                            
                    # 生成报表
                    report_date = self.extract_date_from_filename(zip_filename)
                    return ReportGenerator.generate_report(report_data, report_date, total_operations, zip_filename, self.file_dir, 'both')
                    
        except Exception as e:
            logging.error(f"处理文件 {zip_filename} 时出错: {e}")
            return None
            
        
    def _calculate_md5(self, data):
        """计算数据的MD5值"""
        return hashlib.md5(data).hexdigest()
    
    def _image_to_base64(self, image_path):
        """将图片转换为base64编码"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 检查图片大小（不能超过2M）
            if len(image_data) > 2 * 1024 * 1024:
                logging.error(f"图片大小超过2M限制: {len(image_data)} bytes")
                return None, None
            
            # 计算MD5
            md5_hash = self._calculate_md5(image_data)
            
            # 转换为base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            return base64_data, md5_hash
        except Exception as e:
            logging.error(f"处理图片失败: {e}")
            return None, None
        
    def send_to_wechat(self, report_data):
        """发送报表到企业微信群"""
        if not report_data:
            logging.warning("没有报表数据可发送")
            return False
            
        try:
            # 添加调试日志
            logging.info(f"准备发送报表数据: {report_data.keys()}")
            logging.info(f"文本内容预览: {report_data['text'][:200]}...")
            
            # 检查是否有图片报表
            if 'image_filename' in report_data:
                logging.info("检测到图片报表，准备发送组合消息")
                image_path = os.path.join(self.file_dir, report_data['image_filename'])
                # 尝试使用JPEG格式的图片（如果存在）
                jpeg_path = image_path[:-4] + '.jpg' if image_path.endswith('.png') else image_path
                
                # 优先使用JPEG格式
                if os.path.exists(jpeg_path):
                    image_path = jpeg_path
                    logging.info(f"使用JPEG格式图片: {image_path}")
                elif not os.path.exists(image_path):
                    # 如果图片文件不存在，跳过图片发送
                    logging.warning(f"图片文件不存在: {image_path}")
                else:
                    # 使用PNG格式
                    logging.info(f"使用PNG格式图片: {image_path}")
                
                if os.path.exists(image_path):
                    # 检查文件格式
                    file_extension = os.path.splitext(image_path)[1].lower()
                    if file_extension not in ['.jpg', '.jpeg', '.png']:
                        logging.error(f"不支持的图片格式: {file_extension}")
                    else:
                        # 转换图片为base64和md5
                        base64_data, md5_hash = self._image_to_base64(image_path)
                        
                        if base64_data and md5_hash:
                            # 创建markdown格式的消息，包含文本和图片
                            # 注意：企业微信markdown消息不支持直接嵌入图片，所以我们先发送图片，再发送markdown文本
                            # 但我们可以优化消息格式，让文本更清晰
                            
                            logging.info("发送图片消息...")
                            image_message = {
                                "msgtype": "image",
                                "image": {
                                    "base64": base64_data,
                                    "md5": md5_hash
                                }
                            }
                            
                            response = requests.post(
                                self.webhook_url,
                                json=image_message,
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                if result.get('errcode') == 0:
                                    logging.info("图片报表发送成功")
                                    
                                    # 等待一小段时间确保图片消息显示
                                    import time
                                    time.sleep(0.5)
                                    
                                    # 发送markdown格式的文本消息
                                    markdown_content = report_data['text']
                                    
                                    # 优化文本格式，添加说明
                                    if not markdown_content.startswith("📊 听录音统计报表"):
                                        markdown_content = f"📊 听录音统计报表\n{markdown_content}"
                                    
                                    markdown_message = {
                                        "msgtype": "markdown",
                                        "markdown": {
                                            "content": markdown_content
                                        }
                                    }
                                    
                                    logging.info("发送markdown文本消息...")
                                    response = requests.post(
                                        self.webhook_url,
                                        json=markdown_message,
                                        timeout=10
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        if result.get('errcode') == 0:
                                            logging.info("markdown文本报表发送成功")
                                            return True
                                        else:
                                            logging.error(f"markdown文本发送失败: {result}")
                                            return False
                                    else:
                                        logging.error(f"markdown文本HTTP请求失败: {response.status_code}")
                                        return False
                                else:
                                    logging.error(f"图片发送失败: {result}")
                                    # 如果图片发送失败，尝试发送markdown文本
                                    return self._send_markdown_text_only(report_data['text'])
                            else:
                                logging.error(f"图片HTTP请求失败: {response.status_code}")
                                # 如果图片发送失败，尝试发送markdown文本
                                return self._send_markdown_text_only(report_data['text'])
                        else:
                            logging.error("图片处理失败，无法获取base64或md5")
                            # 如果图片处理失败，尝试发送markdown文本
                            return self._send_markdown_text_only(report_data['text'])
                else:
                    # 如果没有图片文件，只发送markdown文本
                    return self._send_markdown_text_only(report_data['text'])
            else:
                # 如果没有图片报表，只发送markdown文本
                return self._send_markdown_text_only(report_data['text'])
                
        except Exception as e:
            logging.error(f"发送报表时出错: {e}")
            return False
    
    def _send_markdown_text_only(self, text_content):
        """只发送markdown格式的文本消息"""
        try:
            markdown_message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": text_content
                }
            }
            
            logging.info("发送纯markdown文本消息...")
            response = requests.post(
                self.webhook_url,
                json=markdown_message,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logging.info("纯markdown文本报表发送成功")
                    return True
                else:
                    logging.error(f"纯markdown文本发送失败: {result}")
                    return False
            else:
                logging.error(f"纯markdown文本HTTP请求失败: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"发送纯markdown文本时出错: {e}")
            return False
            
    def process_daily_files(self):
        """处理当天的新文件"""
        logging.info("开始检查当天的新文件...")
        
        today_files = self.get_today_files()
        if not today_files:
            logging.info("没有找到当天的新文件")
            return
            
        logging.info(f"找到 {len(today_files)} 个当天的新文件: {today_files}")
        
        for filename in today_files:
            try:
                report_data = self.process_zip_file(filename)
                if report_data:
                    # 发送到企业微信
                    if self.send_to_wechat(report_data):
                        logging.info(f"文件 {filename} 处理完成并发送成功")
                    else:
                        logging.error(f"文件 {filename} 发送失败")
                        
                # 标记为已处理
                self.processed_files.add(filename)
                
            except Exception as e:
                logging.error(f"处理文件 {filename} 时出错: {e}")
                
    def run_scheduler(self):
        """运行定时任务"""
        logging.info("启动定时任务...")
        
        # 每天上午9点执行
        schedule.every().day.at("09:00").do(self.process_daily_files)
        
        # 也可以每小时检查一次新文件
        schedule.every().hour.do(self.process_daily_files)
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
            
    def run_once(self):
        """立即执行一次处理"""
        self.process_daily_files()

def main():
    # 企业微信机器人webhook
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=2645bd5f-4802-45dc-8fd7-c46f67d317a9"
    
    # 创建报表处理器
    reporter = CallRecordingReporter(webhook_url)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--schedule':
        # 定时运行模式
        reporter.run_scheduler()
    else:
        # 立即运行模式
        reporter.run_once()

if __name__ == "__main__":
    main()