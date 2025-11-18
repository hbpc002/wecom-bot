import os
import zipfile
from datetime import datetime

def debug():
    print("=== Debug Info ===")
    
    # 检查文件目录
    file_dir = 'file'
    print(f"File directory exists: {os.path.exists(file_dir)}")
    
    if os.path.exists(file_dir):
        files = os.listdir(file_dir)
        print(f"Files in directory: {files}")
        
        # 检查今天的文件
        today = datetime.now().strftime('%Y%m%d')
        print(f"Today string: {today}")
        
        today_files = []
        for filename in files:
            print(f"Checking file: {filename}")
            if filename.endswith('.zip'):
                print(f"  - Ends with .zip: True")
                if today in filename:
                    print(f"  - Contains today's date: True")
                    today_files.append(filename)
                else:
                    print(f"  - Contains today's date: False")
            else:
                print(f"  - Ends with .zip: False")
                
        print(f"Today files: {today_files}")
        
        # 测试处理文件
        if today_files:
            filename = today_files[0]
            print(f"\nTesting file processing: {filename}")
            zip_path = os.path.join(file_dir, filename)
            print(f"Zip path: {zip_path}")
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                    print(f"CSV files in zip: {csv_files}")
                    
                    if csv_files:
                        csv_filename = csv_files[0]
                        print(f"Reading CSV: {csv_filename}")
                        
                        with zip_ref.open(csv_filename, 'r') as csvfile:
                            content = csvfile.read()
                            print(f"CSV content (first 100 bytes): {content[:100]}")
                    else:
                        print("No CSV files found in zip")
                        
            except Exception as e:
                print(f"Error processing zip: {e}")

if __name__ == "__main__":
    debug()