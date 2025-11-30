"""
项目健壮性优化自动修改脚本
自动应用日志轮转、文件验证和临时文件清理功能
"""

import os
import shutil
from datetime import datetime


def backup_file(filepath):
    """备份文件"""
    backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ 已备份: {backup_path}")
    return backup_path


def modify_main_py():
    """修改 main.py 文件"""
    filepath = 'main.py'
    print(f"\n📝 修改 {filepath}...")
    
    # 备份
    backup_file(filepath)
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改1: 添加日志轮转
    old_import = """# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_message.log', encoding='utf-8')
    ]
)"""
    
    new_import = """# 配置日志
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'test_message.log',
            encoding='utf-8',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5  # 保留5个备份文件
        )
    ]
)"""
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print("  ✓ 已添加日志轮转配置")
    else:
        print("  ⚠ 警告: 未找到日志配置代码，可能已经修改过")
    
    # 修改2: 添加临时文件清理方法（在 send_to_wechat 方法之前）
    cleanup_method = '''    
    def _cleanup_temp_image(self, image_path):
        """清理临时图片文件（包括PNG和JPEG版本）
        
        Args:
            image_path: 图片文件路径
        """
        try:
            # 删除主图片文件
            if os.path.exists(image_path):
                os.remove(image_path)
                logging.info(f"已删除临时图片: {os.path.basename(image_path)}")
            
            # 删除对应的JPEG/PNG副本
            if image_path.endswith('.png'):
                jpeg_path = image_path[:-4] + '.jpg'
                if os.path.exists(jpeg_path):
                    os.remove(jpeg_path)
                    logging.info(f"已删除临时图片: {os.path.basename(jpeg_path)}")
            elif image_path.endswith('.jpg') or image_path.endswith('.jpeg'):
                png_path = image_path.rsplit('.', 1)[0] + '.png'
                if os.path.exists(png_path):
                    os.remove(png_path)
                    logging.info(f"已删除临时图片: {os.path.basename(png_path)}")
        except Exception as e:
            logging.warning(f"清理临时图片失败: {e}")
    '''
    
    # 在 send_to_wechat 方法定义之前插入
    send_to_wechat_marker = '    def send_to_wechat(self, report_data):'
    if send_to_wechat_marker in content and '_cleanup_temp_image' not in content:
        content = content.replace(send_to_wechat_marker, cleanup_method + '\n' + send_to_wechat_marker)
        print("  ✓ 已添加临时文件清理方法")
    elif '_cleanup_temp_image' in content:
        print("  ⚠ 临时文件清理方法已存在")
    else:
        print("  ✗ 未找到 send_to_wechat 方法定义位置")
    
    # 修改3: 在 base64 发送成功后调用清理
    old_base64_return = '''                        logging.info("图片报表发送成功（base64方式）")
                        return True'''
    new_base64_return = '''                        logging.info("图片报表发送成功（base64方式）")
                        # 发送成功后删除临时图片文件
                        self._cleanup_temp_image(image_path)
                        return True'''
    
    if old_base64_return in content:
        content = content.replace(old_base64_return, new_base64_return)
        print("  ✓ 已添加 base64 发送后清理调用")
    else:
        print("  ⚠ base64 发送代码可能已修改")
    
    # 修改4: 在 media_id 发送成功后调用清理
    old_media_return = '''                                    if result.get('errcode') == 0:
                                        logging.info("图片报表发送成功")
                                        return True'''
    new_media_return = '''                                    if result.get('errcode') == 0:
                                        logging.info("图片报表发送成功")
                                        # 发送成功后删除临时图片文件
                                        self._cleanup_temp_image(image_path)
                                        return True'''
    
    if old_media_return in content:
        content = content.replace(old_media_return, new_media_return)
        print("  ✓ 已添加 media_id 发送后清理调用")
    else:
        print("  ⚠ media_id 发送代码可能已修改")
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {filepath} 修改完成")


def modify_web_server_py():
    """修改 web_server.py 文件"""
    filepath = 'web_server.py'
    print(f"\n📝 修改 {filepath}...")
    
    # 备份
    backup_file(filepath)
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改1: 添加必要的导入（如果还没有）
    import_section = '''import json
import socket'''
    
    new_imports = '''import json
import socket
import glob
import zipfile
from datetime import timedelta'''
    
    if import_section in content and 'import glob' not in content:
        content = content.replace(import_section, new_imports)
        print("  ✓ 已添加必要的导入")
    elif 'import glob' in content:
        print("  ⚠ 导入已存在")
    else:
        print("  ✗ 未找到导入位置")
    
    # 修改2: 添加工具函数（在 allowed_file 函数之后）
    utility_functions = '''
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
'''
    
    # 在 @app.route('/login') 之前插入工具函数
    login_route_marker = "@app.route('/login', methods=['GET', 'POST'])"
    if login_route_marker in content and 'def validate_zip_file' not in content:
        content = content.replace(login_route_marker, utility_functions + '\n' + login_route_marker)
        print("  ✓ 已添加工具函数")
    elif 'def validate_zip_file' in content:
        print("  ⚠ 工具函数已存在")
    else:
        print("  ✗ 未找到插入位置")
    
    # 修改3: 在文件上传时添加验证
    old_save_code = '''                # 保存文件
                file.save(filepath)
                logging.info(f"文件已保存: {filepath}")
                
                # 处理文件'''
    
    new_save_code = '''                # 保存文件
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
                
                # 处理文件'''
    
    if old_save_code in content:
        content = content.replace(old_save_code, new_save_code)
        print("  ✓ 已添加文件验证代码")
    else:
        print("  ⚠ 文件保存代码可能已修改")
    
    # 修改4: 在启动时添加清理
    old_main = '''if __name__ == '__main__':
    logging.info("启动Web服务器...")
    logging.info(f"数据库路径: {app.config['DATABASE_PATH']}")
    logging.info(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=False)'''
    
    new_main = '''if __name__ == '__main__':
    logging.info("启动Web服务器...")
    logging.info(f"数据库路径: {app.config['DATABASE_PATH']}")
    logging.info(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    
    # 清理旧的临时文件
    logging.info("清理旧的临时文件...")
    cleanup_old_files(app.config['UPLOAD_FOLDER'], days_to_keep=30)
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=False)'''
    
    if old_main in content:
        content = content.replace(old_main, new_main)
        print("  ✓ 已添加启动时清理代码")
    else:
        print("  ⚠ 主函数代码可能已修改")
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {filepath} 修改完成")


def main():
    """主函数"""
    print("=" * 60)
    print("   项目健壮性优化自动修改脚本")
    print("=" * 60)
    print("\n此脚本将自动应用以下优化：")
    print("  1. 日志文件轮转（限制大小）")
    print("  2. 临时图片文件自动清理")
    print("  3. ZIP 文件验证")
    print("  4. 启动时清理旧文件")
    print("\n文件将自动备份到 .backup 文件\n")
    
    try:
        # 切换到项目目录
        os.chdir('d:\\Documents\\G-ide\\wecom-bot')
        print(f"📂 当前目录: {os.getcwd()}\n")
        
        # 修改文件
        modify_main_py()
        modify_web_server_py()
        
        print("\n" + "=" * 60)
        print("✅ 所有修改完成！")
        print("=" * 60)
        print("\n⚠️  重要提示:")
        print("  1. 请检查修改是否正确")
        print("  2. 重启 web_server.py 以使更改生效")
        print("  3. 如有问题，可使用备份文件恢复")
        print("\n备份文件命名格式: filename.backup.YYYYMMDD_HHMMSS")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
