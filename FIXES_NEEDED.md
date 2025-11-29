# 需要修复的问题

## 问题1: 重复上传同一天的数据不会自动去重

### 当前问题
在 `database.py` 的 `insert_batch_records` 方法中，没有检查重复记录，导致重复上传同一天的数据时会产生重复记录。

### 解决方案
在 `database.py` 第116-156行的 `insert_batch_records` 方法中添加去重逻辑：

```python
def insert_batch_records(self, records: List[Dict]) -> int:
    """批量插入听录音记录（自动去重）"""
    success_count = 0
    duplicate_count = 0
    try:
        cursor = self.conn.cursor()
        
        for record in records:
            try:
                operation_time = record['operation_time']
                if isinstance(operation_time, str):
                    operation_time = datetime.strptime(operation_time, '%Y-%m-%d %H:%M:%S')
                
                record_date = operation_time.date()
                
                # 检查是否已存在相同的记录（基于 account, operation_time）
                cursor.execute('''
                    SELECT COUNT(*) FROM listening_records 
                    WHERE account = ? AND operation_time = ?
                ''', (record['account'], operation_time))
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    duplicate_count += 1
                    logging.debug(f"跳过重复记录: {record['account']} - {operation_time}")
                    continue
                
                # 插入新记录
                cursor.execute('''
                    INSERT INTO listening_records (account, name, team, operation_time, date, source_file)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (record['account'], record['name'], record['team'], 
                      operation_time, record_date, record['source_file']))
                
                success_count += 1
                
            except Exception as e:
                logging.warning(f"插入单条记录失败: {e}, 记录: {record}")
                continue
        
        self.conn.commit()
        logging.info(f"批量插入完成，成功: {success_count}/{len(records)}，跳过重复: {duplicate_count}")
        return success_count
        
    except Exception as e:
        logging.error(f"批量插入失败: {e}")
        self.conn.rollback()
        return success_count
```

---

## 问题2: 企业微信推送的报表数据没有月累计列

### 当前问题
报表生成器 `report_generator.py` 中的表格只显示当日数据，没有显示月累计数据。

### 解决方案

#### 步骤1: 修改 `report_generator.py` 的 `generate_report` 方法签名（第14行）
添加 `monthly_data` 参数：
```python
def generate_report(report_data, report_date, total_operations, filename, file_dir, output_format='both', monthly_data=None):
```

#### 步骤2: 在 `report_generator.py` 第40-60行，修改数据处理逻辑
```python
# 新增代码：将所有团队成员数据合并到一个列表中
all_members = []
for team, members in team_data.items():
    for member in members:
        # 获取月累计数据
        monthly_count = 0
        if monthly_data and member['account'] in monthly_data:
            monthly_count = monthly_data[member['account']]
        
        all_members.append({
            'team': team,
            'name': member['name'],
            'account': member['account'],
            'count': member['count'],
            'monthly_count': monthly_count
        })
```

#### 步骤3: 在 `report_generator.py` 第88-94行，修改表格头和数据行
```python
# 添加表格头（包含月累计列）
if monthly_data:
    table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 当日次数 | 月累计 |")
else:
    table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 听录音次数 |")

# 添加表格数据
for i, member in enumerate(all_members_sorted, start=1):
    if monthly_data:
        table_lines.append(f"| {i} | {member['team']} | {member['name']} | {member['account']} | {member['count']} | {member['monthly_count']} |")
    else:
        table_lines.append(f"| {i} | {member['team']} | {member['name']} | {member['account']} | {member['count']} |")
```

#### 步骤4: 在 `report_generator.py` 第139行，修改图片生成调用
```python
ReportGenerator._generate_image_report(full_image_lines, image_path, has_monthly=bool(monthly_data))
```

#### 步骤5: 在 `report_generator.py` 第149行，修改 `_generate_image_report` 方法签名
```python
def _generate_image_report(report_lines, output_path, has_monthly=False):
```

#### 步骤6: 在 `report_generator.py` 第302-329行，修改表格列宽设置
```python
# 绘制表头文字
x_pos = x_margin + 10
if has_monthly:
    col_widths = [0.08, 0.12, 0.2, 0.18, 0.2, 0.22]  # 排名、团队、姓名、账号、当日次数、月累计
else:
    col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数
```

#### 步骤7: 在 `main.py` 第230-244行，修改报表生成调用
在调用 `ReportGenerator.generate_report` 之前，获取月累计数据：
```python
# 保存到数据库
if hasattr(self, 'db') and self.db and db_records:
    try:
        logging.info(f"正在将 {len(db_records)} 条记录写入数据库...")
        self.db.insert_batch_records(db_records)
        
        # 更新汇总数据
        if report_date:
            self.db.update_daily_summary(report_date)
            self.db.update_monthly_summary(report_date.strftime('%Y-%m'))
            logging.info(f"数据库汇总已更新: {report_date}")
    except Exception as e:
        logging.error(f"写入数据库失败: {e}")

# 获取月累计数据
monthly_data = None
if hasattr(self, 'db') and self.db and report_date:
    try:
        year_month = report_date.strftime('%Y-%m')
        monthly_summary = self.db.get_monthly_summary(year_month)
        # 转换为字典格式 {account: total_count}
        monthly_data = {item['account']: item['total_count'] for item in monthly_summary}
    except Exception as e:
        logging.error(f"获取月累计数据失败: {e}")
        
return ReportGenerator.generate_report(report_data, report_date, total_operations, zip_filename, self.file_dir, 'both', monthly_data)
```

#### 步骤8: 在 `web_server.py` 第327-332行，修改手动发送报表的逻辑
```python
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
```

---

## 问题3: 需要增加已上传文件删除功能

### 解决方案

#### 步骤1: 在 `web_server.py` 添加删除文件的API（在第291行之后添加）
```python
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
```

#### 步骤2: 在前端 `templates/index.html` 的文件列表中添加删除按钮
在文件列表的每一行添加删除按钮，并绑定删除事件。

---

## 实施步骤

1. 首先修复问题1（数据去重）- 修改 `database.py`
2. 然后修复问题3（文件删除功能）- 修改 `web_server.py`
3. 最后修复问题2（月累计列）- 需要修改多个文件，按照上面的步骤顺序进行

## 测试建议

1. 测试数据去重：上传同一个文件两次，检查数据库中是否有重复记录
2. 测试文件删除：在Web界面删除一个已上传的文件
3. 测试月累计显示：上传多天的数据后，查看报表是否正确显示月累计列
