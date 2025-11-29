from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import logging
from datetime import datetime, date
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
from main import CallRecordingReporter
import json
import socket

# Monkeypatch socket.getfqdn to avoid UnicodeDecodeError on Windows with non-ASCII hostnames
def getfqdn(name=''):
    return name or 'localhost'
socket.getfqdn = getfqdn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'file'
app.config['DATABASE_PATH'] = os.getenv('DATABASE_PATH', 'data/wecom_bot.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 默认用户配置（生产环境请修改）
DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin123'

# 企业微信Webhook配置
WEBHOOK_TEST = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=afa40fa1-1e9f-4e99-ba99-bf774f195a08"  # 测试环境
WEBHOOK_PROD = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=f063326c-45a0-4d87-bea3-131ceab86714"  # 生产环境

# 定时任务配置
scheduled_task_enabled = False
scheduled_task_time = "09:00"

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

# 初始化数据库
db = Database(app.config['DATABASE_PATH'])

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'zip'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        # 创建报表处理器
        reporter = CallRecordingReporter(webhook_url if webhook_url else None, app.config['UPLOAD_FOLDER'])
        reporter.db = db  # 注入数据库实例
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # 保存文件
                file.save(filepath)
                logging.info(f"文件已保存: {filepath}")
                
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
        
        # 获取数据（包含月累计）
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
        
        # 获取数据
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
        
        if not date_str:
            return jsonify({'success': False, 'error': '请选择日期'}), 400
        
        # 选择webhook
        webhook_url = WEBHOOK_TEST if env == 'test' else WEBHOOK_PROD
        
        # 创建报表处理器
        reporter = CallRecordingReporter(webhook_url, app.config['UPLOAD_FOLDER'])
        reporter.db = db
        
        # 获取指定日期的数据
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        daily_data = db.get_daily_summary(target_date)
        
        if not daily_data:
            return jsonify({'success': False, 'error': '该日期没有数据'}), 404
        
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
            return jsonify({
                'success': True,
                'message': f'报表已成功发送到{env_name}'
            })
        else:
            return jsonify({'success': False, 'error': '发送失败'}), 500
            
    except Exception as e:
        logging.error(f"发送到企业微信失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/schedule/status', methods=['GET'])
@login_required
def get_schedule_status():
    """获取定时任务状态"""
    global scheduled_task_enabled, scheduled_task_time
    return jsonify({
        'success': True,
        'enabled': scheduled_task_enabled,
        'time': scheduled_task_time
    })

@app.route('/api/schedule/update', methods=['POST'])
@login_required
def update_schedule():
    """更新定时任务配置"""
    global scheduled_task_enabled, scheduled_task_time
    try:
        data = request.get_json()
        scheduled_task_enabled = data.get('enabled', False)
        scheduled_task_time = data.get('time', '09:00')
        
        # TODO: 这里可以实际启动或停止定时任务
        # 使用schedule库或APScheduler
        
        return jsonify({
            'success': True,
            'message': '定时任务配置已更新',
            'enabled': scheduled_task_enabled,
            'time': scheduled_task_time
        })
    except Exception as e:
        logging.error(f"更新定时任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/static/<path:path>')
def send_static(path):
    """提供静态文件"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    logging.info("启动Web服务器...")
    logging.info(f"数据库路径: {app.config['DATABASE_PATH']}")
    logging.info(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=False)
