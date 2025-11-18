import csv
import zipfile
import os
import chardet
from datetime import datetime

def test_mapping():
    print("=== 测试团队映射匹配 ===")
    
    # 1. 读取团队映射
    file_dir = 'file'
    team_mapping = {}
    
    try:
        mapping_file = os.path.join(file_dir, 'team_mapping.csv')
        with open(mapping_file, 'rb') as f:
            raw_data = f.read()
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result['encoding'] or 'gbk'
            print(f"团队映射文件编码: {encoding}")
            
        with open(mapping_file, 'r', encoding=encoding) as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # 跳过标题行
            for row in reader:
                if len(row) >= 2:
                    team_name, account_id = row[0].strip(), row[1].strip()
                    team_mapping[account_id] = team_name
                    
        print(f"团队映射: {team_mapping}")
        
    except Exception as e:
        print(f"读取团队映射失败: {e}")
        return
    
    # 2. 读取今天的日志数据
    today = datetime.now().strftime('%Y%m%d')
    today_files = []
    
    for filename in os.listdir(file_dir):
        if filename.endswith('.zip') and today in filename:
            today_files.append(filename)
    
    if not today_files:
        print("没有找到今天的文件")
        return
    
    filename = today_files[0]
    zip_path = os.path.join(file_dir, filename)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            csv_filename = csv_files[0]
            
            with zip_ref.open(csv_filename, 'r') as csvfile:
                raw_data = csvfile.read()
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result['encoding'] or 'gbk'
                
                # 尝试多种编码解码
                content = None
                encodings_to_try = [encoding, 'gbk', 'utf-8', 'gb2312', 'big5']
                
                for enc in encodings_to_try:
                    try:
                        content = raw_data.decode(enc)
                        print(f"成功使用编码: {enc}")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    content = raw_data.decode('gbk', errors='ignore')
                    print("使用忽略错误的方式解码")
                lines = content.splitlines()
                reader = csv.reader(lines)
                header = next(reader, None)
                
                print(f"\nCSV标题: {header}")
                
                # 统计账号出现次数
                account_stats = {}
                matched_accounts = set()
                
                for row_num, row in enumerate(reader, start=2):
                    if len(row) < 6:
                        continue
                        
                    account = row[1].strip()  # 帐号在第2列
                    name = row[2].strip()     # 姓名在第3列
                    
                    if account not in account_stats:
                        account_stats[account] = {'name': name, 'count': 0}
                    account_stats[account]['count'] += 1
                    
                    if account in team_mapping:
                        matched_accounts.add(account)
                
                print(f"\n总共有 {len(account_stats)} 个不同的账号")
                print(f"匹配到团队的账号: {len(matched_accounts)}")
                
                print(f"\n所有账号统计:")
                for account, info in sorted(account_stats.items()):
                    team = team_mapping.get(account, "未匹配")
                    match_status = "[MATCH]" if account in team_mapping else "[NO MATCH]"
                    print(f"  {match_status} {account} ({info['name']}): {info['count']}次 -> {team}")
                
                print(f"\n匹配的账号详情:")
                for account in matched_accounts:
                    info = account_stats[account]
                    team = team_mapping[account]
                    print(f"  {account} ({info['name']}): {info['count']}次 -> {team}")
    
    except Exception as e:
        print(f"处理日志文件失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mapping()