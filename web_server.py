from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import logging
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
from main import CallRecordingReporter
import json
import socket
import glob
import zipfile
import schedule
import threading
import time

# Monkeypatch socket.getfqdn to avoid UnicodeDecodeError on Windows with non-ASCII hostnames
def getfqdn(name=''):
    return name or 'localhost'
socket.getfqdn = getfqdn

import sys
import codecs

# 强制设置标准输出和错误输出为UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 配置日志
# 移除可能存在的旧handler
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 创建新的handler
file_handler = logging.FileHandler('web_server.log', encoding='utf-8')
stream_handler = logging.StreamHandler(sys.stdout)

# 设置格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# 配置根logger
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'file'
app.config['DATABASE_PATH'] = os.getenv('DATABASE_PATH', 'data/wecom_bot.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JSON_AS_ASCII'] = False  # 确保JSON不使用ASCII编码,支持中文

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 默认用户配置（生产环境请修改）
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin123'

# 企业微信Webhook配置

WEBHOOK_PROD = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=33cfebf3-b005-41c2-a472-8e52b9c70b44"  # 新闻
WEBHOOK_TEST = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=afa40fa1-1e9f-4e99-ba99-bf774f195a08"  # 测试环境
# WEBHOOK_PROD = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=f063326c-45a0-4d87-bea3-131ceab86714"  # 生产环境

# 定时任务配置
scheduler_thread = None
scheduler_running = False

# 用户类
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# 简单的用户存储（生产环境应使用数据库）
users = {
    DEFAULT_USERNAME: generate_password_hash(DEFAULT_PASSWORD)
}

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id, user_id)
    return None

# 确保必要的目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# 数据库路径（使用临时连接而非全局实例，避免锁定问题）
# db = Database(app.config['DATABASE_PATH'])  # 已移除全局实例，改用临时连接

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'zip'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.after_request
def after_request(response):
    """确保所有响应都使用UTF-8编码,避免latin-1编码错误"""
    if response.content_type and 'application/json' in response.content_type:
        if 'charset' not in response.content_type.lower():
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response


def validate_zip_file(filepath):
    """验证 ZIP 文件的有效性
    
    Args:
        filepath: ZIP 文件路径
        
    Returns:
        tuple: (是否有效, 错误信息)
    """
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            bad_file = zip_ref.testzip()
            if bad_file:
                return False, f"ZIP 文件损坏: {bad_file}"
            
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                return False, "ZIP 文件中没有 CSV 文件"
            
            return True, "验证通过"
    except zipfile.BadZipFile:
        return False, "不是有效的 ZIP 文件"
    except Exception as e:
        return False, f"验证失败: {str(e)}"

def cleanup_old_files(file_dir='file', days_to_keep=30):
    """清理超过指定天数的临时文件
    
    Args:
        file_dir: 文件目录
        days_to_keep: 保留天数
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        patterns = ['table_*.png', 'table_*.jpg', 'summary_*.txt']
        for pattern in patterns:
            for filepath in glob.glob(os.path.join(file_dir, pattern)):
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        cleaned_count += 1
                        logging.info(f"已删除旧文件: {os.path.basename(filepath)}")
                except Exception as e:
                    logging.warning(f"删除文件失败 {filepath}: {e}")
        
        if cleaned_count > 0:
            logging.info(f"清理完成，删除了 {cleaned_count} 个文件（保留最近 {days_to_keep} 天）")
        else:
            logging.info(f"无需清理，所有文件都在 {days_to_keep} 天内")
    except Exception as e:
        logging.error(f"清理文件失败: {e}")

def scheduled_send_task():
    """定时发送任务 - 发送前一天的报表到生产环境"""
    try:
        logging.info("========== 执行定时发送任务 ==========")
        
        # 获取前一天的日期（因为当天上传的是前一天的数据）
        yesterday = datetime.now().date() - timedelta(days=1)
        logging.info(f"查询日期: {yesterday}")
        
        # 使用临时数据库连接
        with Database(app.config['DATABASE_PATH']) as db:
            # 尝试获取任务锁
            lock_name = "scheduled_report"
            if not db.acquire_task_lock(lock_name, yesterday):
                logging.warning(f"任务锁获取失败，任务可能已在其他进程执行: {lock_name} - {yesterday}")
                return

            # 查询前一天的数据
            daily_data = db.get_daily_summary(yesterday)
            
            if not daily_data:
                logging.warning(f"没有找到 {yesterday} 的数据，跳过发送")
                return
            
            logging.info(f"找到 {len(daily_data)} 条数据记录")
            
            # 构造报表数据格式
            report_data = {}
            for item in daily_data:
                key = (item['team'], item['name'], item['account'])
                report_data[key] = item['count']
            
            total_operations = sum(item['count'] for item in daily_data)
            
            # 获取月累计数据
            monthly_data = None
            try:
                year_month = yesterday.strftime('%Y-%m')
                monthly_summary = db.get_monthly_summary(year_month)
                monthly_data = {item['account']: item['total_count'] for item in monthly_summary}
                logging.info(f"获取到月累计数据: {len(monthly_data)} 条")
            except Exception as e:
                logging.error(f"获取月累计数据失败: {e}")
            
            # 生成报表
            from report_generator import ReportGenerator
            result = ReportGenerator.generate_report(
                report_data, yesterday, total_operations,
                f"scheduled_{yesterday}.zip", app.config['UPLOAD_FOLDER'], 'both', monthly_data
            )
            
            # 创建报表处理器并发送到生产环境
            reporter = CallRecordingReporter(WEBHOOK_PROD, app.config['UPLOAD_FOLDER'])
            reporter.db = db
            
            if reporter.send_to_wechat(result):
                logging.info(f"✓ 定时报表发送成功 - 日期: {yesterday}, 总次数: {total_operations}")
            else:
                logging.error(f"✗ 定时报表发送失败 - 日期: {yesterday}")
                
    except Exception as e:
        logging.error(f"定时发送任务执行失败: {e}", exc_info=True)

def run_scheduler():
    """调度器运行函数 - 在后台线程中运行"""
    global scheduler_running
    logging.info("定时任务调度器线程已启动")
    
    while scheduler_running:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"调度器运行错误: {e}")
    
    logging.info("定时任务调度器线程已停止")

def start_scheduler():
    """启动调度器线程"""
    global scheduler_thread, scheduler_running
    
    if scheduler_running:
        logging.warning("调度器已在运行，无需重复启动")
        return
    
    scheduler_running = True
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logging.info("定时任务调度器已启动")

def stop_scheduler():
    """停止调度器线程"""
    global scheduler_thread, scheduler_running
    
    if not scheduler_running:
        return
    
    scheduler_running = False
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=5)
    logging.info("定时任务调度器已停止")


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面和处理"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        if username in users and check_password_hash(users[username], password):
            user = User(username, username)
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'message': '登录成功'})
            return redirect(url_for('index'))
        
        if request.is_json:
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """登出"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """返回主页"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_files():
    """处理文件上传"""
    try:
        # 检查是否有文件
        if 'files[]' not in request.files:
            return jsonify({'success': False, 'error': '没有文件上传'}), 400
        
        files = request.files.getlist('files[]')
        
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        results = []
        webhook_url = request.form.get('webhook_url', '')
        
        # 创建报表处理器，使用临时数据库连接
        reporter = CallRecordingReporter(webhook_url if webhook_url else None, app.config['UPLOAD_FOLDER'])
        with Database(app.config['DATABASE_PATH']) as db:
            reporter.db = db  # 注入临时数据库实例
        
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # 保存文件
                    file.save(filepath)
                    logging.info(f"文件已保存: {filepath}")
                    
                    # 验证 ZIP 文件
                    is_valid, validation_message = validate_zip_file(filepath)
                    if not is_valid:
                        os.remove(filepath)  # 删除无效文件
                        logging.warning(f"文件验证失败: {filename} - {validation_message}")
                        results.append({
                            'filename': filename,
                            'success': False,
                            'message': f'文件验证失败：{validation_message}'
                        })
                        continue
                    
                    # 处理文件
                    try:
                        report_data = reporter.process_zip_file(filename)
                        
                        if report_data:
                            results.append({
                                'filename': filename,
                                'success': True,
                                'message': '处理成功',
                                'data': {
                                    'date': str(report_data.get('date', '')),
                                    'total_operations': report_data.get('total_operations', 0),
                                    'people': report_data.get('people', 0)
                                }
                            })
                        else:
                            results.append({
                                'filename': filename,
                                'success': False,
                                'message': '处理失败：无法生成报表'
                            })
                            
                    except Exception as e:
                        logging.error(f"处理文件 {filename} 时出错: {e}")
                        results.append({
                            'filename': filename,
                            'success': False,
                            'message': f'处理失败：{str(e)}'
                        })
                else:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'message': '不支持的文件格式，只允许.zip文件'
                    })
            
            # 统计成功和失败数量
            success_count = sum(1 for r in results if r['success'])
            
            return jsonify({
                'success': True,
                'message': f'上传完成：{success_count}/{len(results)} 个文件处理成功',
                'results': results
            })
        
    except Exception as e:
        logging.error(f"上传处理失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/daily/<date_str>', methods=['GET'])
@login_required
def get_daily_report(date_str):
    """获取指定日期的报表数据（包含月累计）"""
    try:
        # 解析日期
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 使用临时数据库连接获取数据（包含月累计）
        with Database(app.config['DATABASE_PATH']) as db:
            data = db.get_daily_with_monthly(target_date)
        
            if not data:
                return jsonify({
                    'success': False,
                    'message': '没有找到该日期的数据'
                }), 404
            
            # 计算汇总信息
            total_operations = sum(item['daily_count'] for item in data)
            
            return jsonify({
                'success': True,
                'date': date_str,
                'total_operations': total_operations,
                'people_count': len(data),
                'data': data
            })
        
    except ValueError:
        return jsonify({'success': False, 'error': '日期格式错误，应为 YYYY-MM-DD'}), 400
    except Exception as e:
        logging.error(f"获取日报表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/monthly/<year_month>', methods=['GET'])
@login_required
def get_monthly_report(year_month):
    """获取指定月份的报表数据"""
    try:
        # 验证格式
        datetime.strptime(year_month, '%Y-%m')
        
        # 使用临时数据库连接获取数据
        with Database(app.config['DATABASE_PATH']) as db:
            data = db.get_monthly_summary(year_month)
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': '没有找到该月份的数据'
                }), 404
            
            # 计算汇总信息
            total_operations = sum(item['total_count'] for item in data)
            
            return jsonify({
                'success': True,
                'year_month': year_month,
                'total_operations': total_operations,
                'people_count': len(data),
                'data': data
            })
        
    except ValueError:
        return jsonify({'success': False, 'error': '月份格式错误，应为 YYYY-MM'}), 400
    except Exception as e:
        logging.error(f"获取月报表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
@login_required
def list_files():
    """获取已上传的文件列表"""
    try:
        files = []
        upload_folder = app.config['UPLOAD_FOLDER']
        
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                if filename.endswith('.zip'):
                    filepath = os.path.join(upload_folder, filename)
                    stat = os.stat(filepath)
                    files.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
        
        # 按修改时间降序排序
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        logging.error(f"获取文件列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/files/<filename>', methods=['DELETE'])
@login_required
def delete_file(filename):
    """删除已上传的文件"""
    try:
        # 安全检查：只允许删除.zip文件
        if not filename.endswith('.zip'):
            return jsonify({'success': False, 'error': '只能删除.zip文件'}), 400
        
        # 构建文件路径
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 删除文件
        os.remove(filepath)
        logging.info(f"文件已删除: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'文件 {filename} 已成功删除'
        })
        
    except Exception as e:
        logging.error(f"删除文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-to-wecom', methods=['POST'])
@login_required
def send_to_wecom():
    """发送报表到企业微信"""
    try:
        data = request.get_json()
        date_str = data.get('date')
        env = data.get('env', 'test')  # test 或 prod
        
        logging.info(f"收到发送请求 - 日期: {date_str}, 环境: {env}")
        

        if not date_str:
            response = jsonify({'success': False, 'error': '请选择日期'})
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response, 400
        
        # 选择webhook
        webhook_url = WEBHOOK_TEST if env == 'test' else WEBHOOK_PROD
        # 记录使用的webhook (隐藏部分key)
        masked_url = webhook_url[:60] + '...' if len(webhook_url) > 60 else webhook_url
        logging.info(f"环境: {env}, 使用webhook: {masked_url}")
        logging.info(f"准备发送到{'生产' if env == 'prod' else '测试'}环境")
        
        # 使用临时数据库连接
        with Database(app.config['DATABASE_PATH']) as db:
            # 创建报表处理器
            reporter = CallRecordingReporter(webhook_url, app.config['UPLOAD_FOLDER'])
            reporter.db = db
            
            # 获取指定日期的数据
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            daily_data = db.get_daily_summary(target_date)
            
            if not daily_data:
                response = jsonify({'success': False, 'error': '该日期没有数据'})
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response, 404
            
            # 构造报表数据格式
            report_data = {}
            for item in daily_data:
                key = (item['team'], item['name'], item['account'])
                report_data[key] = item['count']
            
            total_operations = sum(item['count'] for item in daily_data)
            
            # 获取月累计数据
            monthly_data = None
            try:
                year_month = target_date.strftime('%Y-%m')
                monthly_summary = db.get_monthly_summary(year_month)
                monthly_data = {item['account']: item['total_count'] for item in monthly_summary}
            except Exception as e:
                logging.error(f"获取月累计数据失败: {e}")
            
            # 生成报表
            from report_generator import ReportGenerator
            result = ReportGenerator.generate_report(
                report_data, target_date, total_operations,
                f"manual_{date_str}.zip", app.config['UPLOAD_FOLDER'], 'both', monthly_data
            )
        
            # 发送到企业微信
            if reporter.send_to_wechat(result):
                env_name = '测试环境' if env == 'test' else '生产环境'
                logging.info(f"✓ 报表成功发送到{env_name} (webhook: {masked_url})")
                response = jsonify({
                    'success': True,
                    'message': f'报表已成功发送到{env_name}'
                })
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response
            else:
                env_name = '测试环境' if env == 'test' else '生产环境'
                logging.error(f"✗ 报表发送失败 - 环境: {env_name}")
                response = jsonify({'success': False, 'error': '发送失败'})
                response.headers['Content-Type'] = 'application/json; charset=utf-8'
                return response, 500
            
    except Exception as e:
        error_msg = str(e)
        logging.error(f"发送到企业微信失败: {error_msg}", exc_info=True)
        response = jsonify({'success': False, 'error': error_msg})
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response, 500

@app.route('/api/schedule/status', methods=['GET'])
@login_required
def get_schedule_status():
    """获取定时任务状态"""
    try:
        with Database(app.config['DATABASE_PATH']) as db:
            enabled = db.get_setting('schedule_enabled', 'false') == 'true'
            time_str = db.get_setting('schedule_time', '10:00')
            
            return jsonify({
                'success': True,
                'enabled': enabled,
                'time': time_str
            })
    except Exception as e:
        logging.error(f"获取定时任务状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/schedule/update', methods=['POST'])
@login_required
def update_schedule():
    """更新定时任务配置"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        time_str = data.get('time', '10:00')
        
        with Database(app.config['DATABASE_PATH']) as db:
            # 保存设置到数据库
            db.set_setting('schedule_enabled', 'true' if enabled else 'false')
            db.set_setting('schedule_time', time_str)
        
        if enabled:
            # 清除现有的所有定时任务
            schedule.clear()
            
            # 创建新的定时任务
            schedule.every().day.at(time_str).do(scheduled_send_task)
            logging.info(f"已创建定时任务: 每天 {time_str} 执行")
            
            # 启动调度器
            start_scheduler()
            
            return jsonify({
                'success': True,
                'message': f'定时任务已启用，将在每天 {time_str} 自动发送报表',
                'enabled': True,
                'time': time_str
            })
        else:
            # 停止调度器并清除任务
            stop_scheduler()
            schedule.clear()
            logging.info("定时任务已停用")
            
            return jsonify({
                'success': True,
                'message': '定时任务已停用',
                'enabled': False,
                'time': time_str
            })
            
    except Exception as e:
        logging.error(f"更新定时任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/team-leaders', methods=['GET'])
@login_required
def get_team_leaders():
    """获取所有团队组长"""
    try:
        with Database(app.config['DATABASE_PATH']) as db:
            leaders = db.get_all_team_leaders()
            return jsonify({
                'success': True,
                'data': leaders
            })
    except Exception as e:
        logging.error(f"获取团队组长列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/team-leaders', methods=['POST'])
@login_required
def create_team_leader():
    """添加团队组长"""
    try:
        data = request.get_json()
        team_name = data.get('team_name', '').strip()
        account_id = data.get('account_id', '').strip()
        name = data.get('name', '').strip()
        
        if not team_name or not account_id or not name:
            return jsonify({'success': False, 'error': '所有字段都是必填的'}), 400
        
        with Database(app.config['DATABASE_PATH']) as db:
            success = db.add_team_leader(team_name, account_id, name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '添加成功'
                })
            else:
                return jsonify({'success': False, 'error': '添加失败，账号可能已存在'}), 400
            
    except Exception as e:
        logging.error(f"添加团队组长失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/team-leaders/<int:leader_id>', methods=['PUT'])
@login_required
def update_team_leader(leader_id):
    """更新团队组长"""
    try:
        data = request.get_json()
        team_name = data.get('team_name', '').strip()
        account_id = data.get('account_id', '').strip()
        name = data.get('name', '').strip()
        
        if not team_name or not account_id or not name:
            return jsonify({'success': False, 'error': '所有字段都是必填的'}), 400
        
        with Database(app.config['DATABASE_PATH']) as db:
            success = db.update_team_leader(leader_id, team_name, account_id, name)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '更新成功'
                })
            else:
                return jsonify({'success': False, 'error': '更新失败，组长不存在或账号已被使用'}), 400
            
    except Exception as e:
        logging.error(f"更新团队组长失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/team-leaders/<int:leader_id>', methods=['DELETE'])
@login_required
def delete_team_leader(leader_id):
    """删除团队组长"""
    try:
        with Database(app.config['DATABASE_PATH']) as db:
            success = db.delete_team_leader(leader_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': '删除成功'
                })
            else:
                return jsonify({'success': False, 'error': '删除失败，组长不存在'}), 404
            
    except Exception as e:
        logging.error(f"删除团队组长失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/static/<path:path>')
def send_static(path):
    """提供静态文件"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    logging.info("启动Web服务器...")
    logging.info(f"数据库路径: {app.config['DATABASE_PATH']}")
    logging.info(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    
    # 清理旧的临时文件
    logging.info("清理旧的临时文件...")
    cleanup_old_files(app.config['UPLOAD_FOLDER'], days_to_keep=30)
    
    # 初始化定时任务
    try:
        with Database(app.config['DATABASE_PATH']) as db:
            enabled = db.get_setting('schedule_enabled', 'false') == 'true'
            time_str = db.get_setting('schedule_time', '10:00')
            
            if enabled:
                schedule.every().day.at(time_str).do(scheduled_send_task)
                start_scheduler()
                logging.info(f"定时任务已自动启用: 每天 {time_str}")
            else:
                logging.info("定时任务未启用")
    except Exception as e:
        logging.error(f"初始化定时任务失败: {e}")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=False)

