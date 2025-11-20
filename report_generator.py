import os
import logging

# 尝试导入PIL库，如果不存在则使用替代方案
try:
    from PIL import Image, ImageDraw, ImageFont
    import textwrap
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ReportGenerator:
    @staticmethod
    def generate_report(report_data, report_date, total_operations, filename, file_dir, output_format='both'):
        """生成报表
        
        Args:
            report_data: 报表数据
            report_date: 报表日期
            total_operations: 总操作次数
            filename: 文件名
            file_dir: 文件目录
            output_format: 输出格式，可选 'text', 'image', 'both'
        """
        if not report_data:
            return None
            
        # 检查是否请求图片输出但PIL不可用
        if output_format in ['image', 'both'] and not PIL_AVAILABLE:
            logging.warning("PIL库未安装，无法生成图片格式报表。将只生成文本格式报表。")
            if output_format == 'image':
                output_format = 'text'
            else:  # 'both'
                output_format = 'text'
            
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
            
        # 生成汇总信息文本（使用正确的markdown格式）
        summary_lines = []
        summary_lines.append("📊 听录音统计报表")
        summary_lines.append(f"📅 日期: {report_date}")
        # summary_lines.append(f"📁 文件: {filename}")
        summary_lines.append("")  # 空行

        # 添加汇总信息（使用markdown格式）
        summary_lines.append("## 📈 汇总信息")
        summary_lines.append(f"- **总操作次数**: {total_operations}")
        summary_lines.append(f"- **参与人数**: {len(report_data)}")
        if len(report_data) > 0:
            summary_lines.append(f"- **平均每人操作次数**: {total_operations/len(report_data):.1f}")
        summary_lines.append("")  # 空行
        
        # 添加调试日志
        logging.info(f"生成的汇总信息文本: {summary_lines}")
        
        # 生成表格数据
        table_lines = []
        table_lines.append("## 📋 详细数据")
        table_lines.append("")  # 空行
        
        # 添加表格头
        table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 操作次数 |")
        table_lines.append("|------|------|------|------|----------|")
        
        # 添加表格数据
        for i, member in enumerate(all_members_sorted, start=1):
            table_lines.append(f"| {i} | {member['team']} | {member['name']} | {member['account']} | {member['count']} |")
        
        # 合并汇总信息和表格信息
        all_lines = summary_lines + table_lines
        report_text = "\n".join(all_lines)
        
        result = {
            'text': "\n".join(summary_lines),  # 只包含汇总信息
            'date': report_date,
            'total_operations': total_operations,
            'teams': len(team_data),
            'people': len(report_data),
            'filename': None
        }
        
        # 根据输出格式生成文件
        if output_format in ['text', 'both']:
            # 保存文本报表（只包含汇总信息）
            text_filename = f"summary_{report_date.strftime('%Y%m%d')}.txt"
            text_path = os.path.join(file_dir, text_filename)
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(summary_lines))
                
            logging.info(f"汇总信息已保存到: {text_path}")
            result['filename'] = text_filename
        
        if output_format in ['image', 'both'] and PIL_AVAILABLE:
            # 生成图片报表（包含标题和表格）
            image_filename = f"table_{report_date.strftime('%Y%m%d')}.png"
            image_path = os.path.join(file_dir, image_filename)
            
            # 创建包含标题和表格的完整图片内容
            full_image_lines = []
            full_image_lines.append(f"📊 {report_date.strftime('%Y年%m月%d日')}听录音统计报表")
            full_image_lines.append("")  # 空行
            full_image_lines.append("## 📈 汇总信息")
            full_image_lines.append(f"- **总操作次数**: {total_operations}")
            full_image_lines.append(f"- **参与人数**: {len(report_data)}")
            if len(report_data) > 0:
                full_image_lines.append(f"- **平均每人操作次数**: {total_operations/len(report_data):.1f}")
            full_image_lines.append("")  # 空行
            full_image_lines.extend(table_lines)  # 添加表格内容
            
            ReportGenerator._generate_image_report(full_image_lines, image_path)
            logging.info(f"表格图片已保存到: {image_path}")
            
            if output_format == 'image':
                result['filename'] = image_filename
            elif output_format == 'both':
                result['image_filename'] = image_filename
        
        return result
    
    @staticmethod
    def _generate_image_report(report_lines, output_path):
        """生成图片格式的报表"""
        if not PIL_AVAILABLE:
            logging.error("PIL库未安装，无法生成图片格式报表")
            return
            
        # 图片设置 - 调整尺寸以符合企业微信要求
        img_width = 800  # 增加宽度以提供更好的表格布局
        img_height = 800  # 初始高度，会根据内容动态调整
        background_color = (255, 255, 255)  # 白色背景
        text_color = (33, 33, 33)  # 深灰色文字，更柔和
        header_color = (41, 98, 255)  # 现代蓝色标题
        table_header_color = (41, 98, 255)  # 蓝色表头背景
        table_row_color1 = (248, 250, 252)  # 淡灰色行背景
        table_row_color2 = (255, 255, 255)  # 白色行背景
        highlight_color = (255, 243, 224)  # 淡橙色高亮
        border_color = (229, 231, 235)  # 浅灰色边框
        table_text_color = (64, 64, 64)  # 表格文字颜色
        
        # 创建图片
        img = Image.new('RGB', (img_width, img_height), background_color)
        draw = ImageDraw.Draw(img)
        
        try:
            # 尝试使用中文字体
            font_path = "C:/Windows/Fonts/simhei.ttf"  # Windows系统黑体
            if os.path.exists(font_path):
                title_font = ImageFont.truetype(font_path, 24)  # 增大标题字体
                header_font = ImageFont.truetype(font_path, 18)
                normal_font = ImageFont.truetype(font_path, 16)
                table_font = ImageFont.truetype(font_path, 14)
            else:
                # 如果找不到中文字体，使用默认字体
                title_font = ImageFont.load_default()
                header_font = ImageFont.load_default()
                normal_font = ImageFont.load_default()
                table_font = ImageFont.load_default()
        except:
            # 字体加载失败，使用默认字体
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            normal_font = ImageFont.load_default()
            table_font = ImageFont.load_default()
        
        # 计算行高 - 增加行高以提高可读性
        title_height = 40
        header_height = 30
        normal_height = 25
        table_height = 25
        
        # 初始位置 - 增加边距以提供更好的布局
        x_margin = 40
        y_pos = 30
        
        # 绘制标题
        table_row_count = 0  # 用于计算表格行数，以便交替着色
        
        # 创建表格数据
        table_data = []
        in_table = False
        
        for line in report_lines:
            if line.startswith("📊"):
                # 主标题 - 添加背景色和圆角
                draw.rectangle([x_margin-10, y_pos-5, img_width-x_margin+10, y_pos+title_height],
                               fill=(240, 248, 255))
                draw.text((x_margin, y_pos), line, fill=header_color, font=title_font)
                y_pos += title_height + 10
            elif line.startswith("📅") or line.startswith("📁"):
                # 副标题
                draw.text((x_margin, y_pos), line, fill=text_color, font=header_font)
                y_pos += header_height
            elif line == "":
                # 空行
                y_pos += normal_height // 2
            elif line.startswith("## 📈"):
                # 汇总信息标题 - 添加背景色和圆角
                draw.rectangle([x_margin-5, y_pos-3, img_width-x_margin+5, y_pos+header_height+5],
                               fill=(241, 245, 249))
                draw.text((x_margin, y_pos), line.replace("## ", ""), fill=header_color, font=header_font)
                y_pos += header_height + 5
            elif line.startswith("- **总操作次数**") or line.startswith("- **参与人数**") or line.startswith("- **平均每人操作次数**"):
                # 汇总信息内容 - 去除markdown格式
                clean_line = line.replace("- **", "").replace("**:", ":")
                draw.text((x_margin, y_pos), clean_line, fill=text_color, font=normal_font)
                y_pos += normal_height
            elif line.startswith("## 📋"):
                # 表格标题 - 添加背景色和圆角
                draw.rectangle([x_margin-5, y_pos-3, img_width-x_margin+5, y_pos+header_height+5],
                               fill=(241, 245, 249))
                draw.text((x_margin, y_pos), line.replace("## ", ""), fill=header_color, font=header_font)
                y_pos += header_height + 10
                in_table = True
            elif in_table and line.startswith("| 排名"):
                # 表头
                table_data.append(('header', line))
            elif in_table and line.startswith("|"):
                # 表格数据行
                if not line.startswith("|------"):  # 跳过分隔线
                    table_data.append(('data', line))
        
        # 绘制表格
        if table_data:
            # 计算表格列宽
            table_width = img_width - 2 * x_margin
            col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数
            
            # 绘制表头
            header_line = table_data[0][1]
            header_cells = [cell.strip() for cell in header_line.split('|')[1:-1]]
            
            # 绘制表头背景
            draw.rectangle([x_margin, y_pos, img_width - x_margin, y_pos + table_height + 5],
                           fill=table_header_color)
            
            # 绘制表头文字
            x_pos = x_margin + 10
            for i, cell in enumerate(header_cells):
                if i < len(col_widths):
                    draw.text((x_pos, y_pos + 5), cell, fill=(255, 255, 255), font=table_font)
                    x_pos += int(table_width * col_widths[i])
            
            y_pos += table_height + 5
            
            # 绘制表格数据行
            for i in range(1, len(table_data)):
                row_type, line = table_data[i]
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                
                # 交替行背景色
                if i % 2 == 0:
                    row_color = table_row_color1
                else:
                    row_color = table_row_color2
                
                # 绘制行背景
                draw.rectangle([x_margin, y_pos, img_width - x_margin, y_pos + table_height],
                               fill=row_color)
                
                # 绘制行边框
                draw.rectangle([x_margin, y_pos, img_width - x_margin, y_pos + table_height],
                               outline=border_color, width=1)
                
                # 绘制单元格分隔线
                x_pos = x_margin
                for j in range(len(col_widths) - 1):
                    x_pos += int(table_width * col_widths[j])
                    draw.line([(x_pos, y_pos), (x_pos, y_pos + table_height)], fill=border_color, width=1)
                
                # 绘制单元格文字
                x_pos = x_margin + 10
                for j, cell in enumerate(cells):
                    if j < len(col_widths):
                        # 第一行（排名1）使用高亮色
                        if i == 1 and j == 0 and cell == "1":
                            draw.rectangle([x_margin, y_pos, img_width - x_margin, y_pos + table_height],
                                           fill=highlight_color)
                            draw.rectangle([x_margin, y_pos, img_width - x_margin, y_pos + table_height],
                                           outline=border_color, width=1)
                            draw.text((x_pos, y_pos + 5), cell, fill=(255, 87, 34), font=table_font)
                        else:
                            draw.text((x_pos, y_pos + 5), cell, fill=table_text_color, font=table_font)
                        x_pos += int(table_width * col_widths[j])
                
                y_pos += table_height
        
        # 如果内容超出初始高度，调整图片大小
        if y_pos + 50 > img_height:
            new_height = y_pos + 100
            # 限制最大高度，避免图片过大
            if new_height > 1500:  # 进一步限制最大高度
                new_height = 1500
            new_img = Image.new('RGB', (img_width, new_height), background_color)
            new_draw = ImageDraw.Draw(new_img)
            new_img.paste(img)
            img = new_img
            draw = new_draw
        
        # 确保图片尺寸符合企业微信要求
        # 企业微信要求图片尺寸不超过 900x900 像素
        if img.width > 900 or img.height > 900:
            # 计算缩放比例
            scale = min(900 / img.width, 900 / img.height)
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 保存图片 - 使用PNG格式以保持清晰度
        img.save(output_path, 'PNG')
        
        # 同时保存一个JPEG版本用于发送
        if output_path.endswith('.png'):
            jpeg_path = output_path[:-4] + '.jpg'
            img.save(jpeg_path, 'JPEG', quality=95)