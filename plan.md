# 报表格式化优化计划

## 目标
将现有的文本格式报表优化为结构化表格，包含以下列：排名、班组、姓名、工号、操作次数、占比，并按操作次数降序排列。表格顶部添加汇总信息栏显示总操作次数、参与人数、平均次数等统计数据。

## 需要修改的文件
`main.py` 中的 `generate_report` 函数

## 详细修改步骤

### 1. 数据准备与排序
在 `generate_report` 函数中，当前代码已经将数据按团队分组存储在 `team_data` 字典中。我们需要将这些数据转换为一个统一的列表，以便进行排序和计算。

```python
# 原有代码
team_data = {}
for (team, name, account), count in report_data.items():
    if team not in team_data:
        team_data[team] = []
    team_data[team].append({
        'name': name,
        'account': account,
        'count': count
    })

# 新增代码：将所有团队成员数据合并到一个列表中
all_members = []
for team, members in team_data.items():
    for member in members:
        all_members.append({
            'team': team,
            'name': member['name'],
            'account': member['account'],
            'count': member['count']
        })

# 按操作次数降序排序
all_members_sorted = sorted(all_members, key=lambda x: x['count'], reverse=True)
```

### 2. 生成 Markdown 表格
我们将使用 Markdown 格式来创建表格。表格将包含以下列：排名、班组、姓名、工号、操作次数、占比。

```python
# 生成报表文本
report_lines = []
report_lines.append(f"📊 听录音统计报表")
report_lines.append(f"📅 日期: {report_date}")
report_lines.append(f"📁 文件: {filename}")
report_lines.append("")  # 空行

# 添加汇总信息
report_lines.append("## 📈 汇总信息")
report_lines.append(f"- **总操作次数**: {total_operations}")
report_lines.append(f"- **参与人数**: {len(report_data)}")
if len(report_data) > 0:
    report_lines.append(f"- **平均每人操作次数**: {total_operations/len(report_data):.1f}")
report_lines.append("")  # 空行

# 添加表格标题
report_lines.append("## 📋 详细数据")
report_lines.append("")  # 空行

# 添加表格表头
report_lines.append("| 排名 | 班组 | 姓名 | 工号 | 操作次数 | 占比 |")
report_lines.append("|------|------|------|------|----------|------|")

# 添加表格数据行
for rank, member in enumerate(all_members_sorted, start=1):
    percentage = (member['count'] / total_operations) * 100 if total_operations > 0 else 0
    report_lines.append(f"| {rank} | {member['team']} | {member['name']} | {member['account']} | {member['count']} | {percentage:.1f}% |")

report_text = "\n".join(report_lines)
```

### 3. 保存报表文件
保存报表文件的代码保持不变，因为文件内容已经被更新为新的 Markdown 格式。

```python
# 保存报表到文件
report_filename = f"report_{report_date.strftime('%Y%m%d')}.txt"
report_path = os.path.join(self.file_dir, report_filename)

with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_text)
```

### 4. 返回报表数据
返回报表数据的代码也保持不变，因为返回的数据结构没有改变。

```python
return {
    'text': report_text,
    'date': report_date,
    'total_operations': total_operations,
    'teams': len(team_data),
    'people': len(report_data),
    'filename': report_filename
}
```

## 预期输出效果
修改后的报表将以 Markdown 格式呈现，包含一个汇总信息部分和一个结构化的数据表格。表格将清晰地展示每个员工的排名、班组、姓名、工号、操作次数及其占总操作次数的百分比。

## 注意事项
- 确保在计算百分比时处理 `total_operations` 为 0 的情况，以避免除以零的错误。
- 排名从 1 开始，按操作次数降序排列。
- 报表文件扩展名保持为 `.txt`，但内容为 Markdown 格式，这在大多数现代文本查看器中都能正确渲染。