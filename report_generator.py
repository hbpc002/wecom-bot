import os
import logging

class ReportGenerator:
    @staticmethod
    def generate_report(report_data, report_date, total_operations, filename, file_dir):
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
        
        # 保存报表到文件
        report_filename = f"report_{report_date.strftime('%Y%m%d')}.txt"
        report_path = os.path.join(file_dir, report_filename)
        
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