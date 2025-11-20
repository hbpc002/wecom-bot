import csv
import zipfile
import os
import chardet
from datetime import datetime

def test_detailed():
    print("=== 详细测试 ===")
    
    file_dir = 'file'
    today = datetime.now().strftime('%Y%m%d')
    
    # 找到今天的文件
    today_files = []
    for filename in os.listdir(file_dir):
        if filename.endswith('.zip') and today in filename:
            today_files.append(filename)
    
    if not today_files:
        print("没有找到今天的文件")
        return
    
    filename = today_files[0]
    print(f"处理文件: {filename}")
    
    zip_path = os.path.join(file_dir, filename)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            print(f"CSV文件: {csv_files}")
            
            if not csv_files:
                print("没有找到CSV文件")
                return
            
            csv_filename = csv_files[0]
            print(f"读取CSV: {csv_filename}")
            
            # 读取文件内容
            with zip_ref.open(csv_filename, 'r') as csvfile:
                raw_data = csvfile.read()
                print(f"文件大小: {len(raw_data)} 字节")
                
                # 检测编码
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result['encoding'] or 'gbk'
                print(f"检测到编码: {encoding}")
                
                # 尝试解码
                content = None
                encodings_to_try = [encoding, 'gbk', 'utf-8', 'gb2312', 'big5']
                
                for enc in encodings_to_try:
                    try:
                        content = raw_data.decode(enc)
                        print(f"成功使用编码: {enc}")
                        break
                    except UnicodeDecodeError:
                        print(f"编码 {enc} 失败")
                        continue
                
                if content is None:
                    content = raw_data.decode('gbk', errors='ignore')
                    print("使用忽略错误的方式解码")
                
                lines = content.splitlines()
                print(f"总行数: {len(lines)}")
                
                # 解析CSV
                reader = csv.reader(lines)
                header = next(reader, None)
                print(f"标题: {header}")
                
                if not header:
                    print("没有标题行")
                    return
                
                # 读取前几行数据
                row_count = 0
                for row_num, row in enumerate(reader, start=2):
                    if row_count >= 5:  # 只显示前5行
                        break
                    
                    print(f"第{row_num}行: {row}")
                    row_count += 1
                    
                    if len(row) < 6:
                        print(f"  行数据不足6列，跳过")
                        continue
                    
                    account = row[1].strip()  # 帐号在第2列
                    name = row[2].strip()     # 姓名在第3列
                    operation_time = row[5].strip()  # 操作时间在第6列
                    
                    print(f"  账号: {account}, 姓名: {name}, 时间: {operation_time}")
                
                print(f"总共处理了 {row_count} 行示例数据")
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import main
    main.main()
    test_detailed()

    # 测试报表生成
    from report_generator import ReportGenerator

    # 构造测试数据
    test_data = {
        ('Team1', 'Name1', 'Account1'): 10,
        ('Team2', 'Name2', 'Account2'): 5,
        ('Team1', 'Name3', 'Account3'): 12,
    }
    
    # 生成报表
    report_date = datetime.now()
    total_operations = sum(test_data.values())
    ReportGenerator.generate_report(test_data, report_date, total_operations, 'test_detailed.py', 'file', output_format='both')