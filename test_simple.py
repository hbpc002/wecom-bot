import os
import zipfile
from datetime import datetime

def test():
    print("=== Simple Test ===")
    
    # 检查文件
    file_dir = 'file'
    today = datetime.now().strftime('%Y%m%d')
    
    print(f"Today: {today}")
    print(f"Files in {file_dir}:")
    
    for filename in os.listdir(file_dir):
        print(f"  {filename}")
        if filename.endswith('.zip') and today in filename:
            print(f"    -> Found today's file!")
            
            # 尝试处理
            try:
                zip_path = os.path.join(file_dir, filename)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    print(f"    Zip files: {zip_ref.namelist()}")
                    
                    for csv_name in zip_ref.namelist():
                        if csv_name.endswith('.csv'):
                            with zip_ref.open(csv_name) as csv_file:
                                content = csv_file.read().decode('utf-8')
                                print(f"    CSV content: {content[:100]}...")
                                
            except Exception as e:
                print(f"    Error: {e}")

if __name__ == "__main__":
    test()