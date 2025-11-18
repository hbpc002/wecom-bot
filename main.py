import csv
import zipfile
import os
import re
import chardet
import requests
import json
from datetime import datetime, timedelta
import schedule
import time
import logging

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
                    return self.generate_report(report_data, report_date, total_operations, zip_filename)
                    
        except Exception as e:
            logging.error(f"处理文件 {zip_filename} 时出错: {e}")
            return None
            
    def generate_report(self, report_data, report_date, total_operations, filename):
        """生成报表"""
        if not report_data:
            return None
            
        # 按团队分组
        team_data = {}
        for (team, name, account), count in report_data.items():
            if team not in team_data:
                team_data[team] = []
            team_data[team].append({
                'name': name,
                'account': account,
                'count': count
            })
            
        # 生成报表文本
        report_lines = []
        report_lines.append(f"📊 听录音统计报表")
        report_lines.append(f"📅 日期: {report_date}")
        report_lines.append(f"📁 文件: {filename}")
        report_lines.append(f"📈 总操作次数: {total_operations}")
        report_lines.append("")
        
        for team, members in sorted(team_data.items()):
            report_lines.append(f"🏢 {team}")
            for member in sorted(members, key=lambda x: x['count'], reverse=True):
                report_lines.append(f"  👤 {member['name']} ({member['account']}): {member['count']}次")
            report_lines.append("")
            
        # 添加统计摘要
        report_lines.append(f"📋 摘要:")
        report_lines.append(f"  • 参与团队数: {len(team_data)}")
        report_lines.append(f"  • 参与人数: {len(report_data)}")
        report_lines.append(f"  • 平均每人: {total_operations/len(report_data):.1f}次")
        
        report_text = "\n".join(report_lines)
        
        # 保存报表到文件
        report_filename = f"report_{report_date.strftime('%Y%m%d')}.txt"
        report_path = os.path.join(self.file_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
            
        logging.info(f"报表已保存到: {report_path}")
        
        return {
            'text': report_text,
            'date': report_date,
            'total_operations': total_operations,
            'teams': len(team_data),
            'people': len(report_data),
            'filename': report_filename
        }
        
    def send_to_wechat(self, report_data):
        """发送报表到企业微信群"""
        if not report_data:
            logging.warning("没有报表数据可发送")
            return False
            
        try:
            message = {
                "msgtype": "text",
                "text": {
                    "content": report_data['text']
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logging.info("报表发送成功")
                    return True
                else:
                    logging.error(f"发送失败: {result}")
                    return False
            else:
                logging.error(f"HTTP请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"发送报表时出错: {e}")
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