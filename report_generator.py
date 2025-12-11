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
    def generate_report(report_data, report_date, total_operations, filename, file_dir, output_format='both', monthly_data=None):
        logging.info("generate_report function called")
        logging.info(f"report_data: {report_data}")
        logging.info(f"report_date: {report_date}")
        logging.info(f"total_operations: {total_operations}")
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
        summary_lines.append(f"- **总听录音次数**: {total_operations}")
        summary_lines.append(f"- **参与人数**: {len(report_data)}")
        if len(report_data) > 0:
            summary_lines.append(f"- **人均次数**: {total_operations/len(report_data):.1f}")
        summary_lines.append("")  # 空行
        
        # 添加调试日志
        # 添加调试日志（避免emoji导致编码错误）
        # logging.info(f"生成报表 - 日期: {report_date}, 总次数: {total_operations}, 参与人数: {len(report_data)}")
        
        # 生成表格数据
        table_lines = []
        table_lines.append("## 📋 详细数据")
        # table_lines.append("")  # 空行
        
        # 添加表格头（包含月累计列）
        if monthly_data:
            table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 当日听录音次数 | 月累计 |")
        else:
            table_lines.append("| 排名 | 团队 | 姓名 | 账号 | 听录音次数 |")
        # table_lines.append("|------|------|------|------|----------|")
        
        # 添加表格数据
        for i, member in enumerate(all_members_sorted, start=1):
            if monthly_data:
                table_lines.append(f"| {i} | {member['team']} | {member['name']} | {member['account']} | {member['count']} | {member['monthly_count']} |")
            else:
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
            # 生成图片报表（包含标题和表格）
            image_filename = f"table_{report_date.strftime('%Y%m%d')}.png"
            
            image_path = os.path.join(file_dir, image_filename)
            
            # 创建包含标题和表格的完整图片内容
            full_image_lines = []
            full_image_lines.append(f"📊 {report_date.year}年{report_date.month}月{report_date.day}日 听录音统计报表")
            full_image_lines.append("")  # 空行
            full_image_lines.append("## 📈 汇总信息")
            full_image_lines.append(f"- **总听录音次数**: {total_operations}")
            full_image_lines.append(f"- **参与人数**: {len(report_data)}")
            if len(report_data) > 0:
                full_image_lines.append(f"- **人均次数**: {total_operations/len(report_data):.1f}")
            full_image_lines.append("")  # 空行
            
            full_image_lines.extend(table_lines)  # 添加表格内容
            
            ReportGenerator._generate_image_report(full_image_lines, image_path, has_monthly=bool(monthly_data))
            logging.info(f"表格图片已保存到: {image_path}")
            
            if output_format == 'image':
                result['filename'] = image_filename
            elif output_format == 'both':
                result['image_filename'] = image_filename
        
        return result
    
    @staticmethod
    def _generate_image_report(report_lines, output_path, has_monthly=False):
        """生成图片格式的报表"""
        logging.info("Generating image report...")
        if not PIL_AVAILABLE:
            logging.error("PIL库未安装，无法生成图片格式报表")
            return
        logging.info("PIL is available.")
        
        # 图片设置 - 调整尺寸以符合企业微信要求
        img_width = 800  # 增加宽度以提供更好的表格布局
        background_color = (255, 255, 255)  # 白色背景
        text_color = (33, 33, 33)  # 深灰色文字，更柔和
        header_color = (41, 98, 255)  # 现代蓝色标题
        table_header_color = (41, 98, 255)  # 蓝色表头背景
        table_row_color1 = (248, 250, 252)  # 淡灰色行背景
        table_row_color2 = (255, 255, 255)  # 白色行背景
        highlight_color = (255, 243, 224)  # 淡橙色高亮
        border_color = (229, 231, 235)  # 浅灰色边框
        table_text_color = (64, 64, 64)  # 表格文字颜色
        
        # 字体设置 - 支持 Windows 和 Linux 环境
        import platform
        system = platform.system()
        
        def find_font_file(font_name, search_dirs=['/usr/share/fonts', '/usr/local/share/fonts']):
            """在指定目录中递归查找字体文件"""
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file.lower() == font_name.lower():
                            return os.path.join(root, file)
            return None

        def load_font(path, size):
            try:
                if os.path.exists(path):
                    logging.info(f"加载字体: {path}")
                    return ImageFont.truetype(path, size)
                else:
                    logging.warning(f"字体文件不存在: {path}")
            except Exception as e:
                logging.error(f"加载字体失败: {path}, 错误: {e}")
            
            # 尝试fallback字体
            fallback_fonts = []
            if system == "Windows":
                fallback_fonts = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc"]
            else:
                # 尝试动态查找 Symbola.ttf
                symbola_path = find_font_file("Symbola.ttf")
                if symbola_path:
                    logging.info(f"动态找到 Symbola 字体: {symbola_path}")
                    fallback_fonts.append(symbola_path)
                
                # 尝试动态查找 NotoColorEmoji.ttf
                noto_emoji_path = find_font_file("NotoColorEmoji.ttf")
                if noto_emoji_path:
                     fallback_fonts.append(noto_emoji_path)

                fallback_fonts.extend([
                    "/usr/share/fonts/truetype/ttf-ancient-fonts/Symbola.ttf",  # Debian 11+
                    "/usr/share/fonts/truetype/ancient-scripts/Symbola.ttf",
                    "/usr/share/fonts/truetype/symbola/Symbola.ttf",
                    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
                ])
            
            for fallback in fallback_fonts:
                try:
                    if os.path.exists(fallback):
                        logging.info(f"使用fallback字体: {fallback}")
                        return ImageFont.truetype(fallback, size)
                except:
                    continue
            
            logging.warning(f"所有字体加载失败: {path}")
            return None

        def get_font(path, size, fallback_font=None):
            font = load_font(path, size)
            if font:
                return font
            if fallback_font:
                logging.info(f"使用fallback字体对象替代: {path}")
                return fallback_font
            logging.warning("使用系统默认字体作为最终后备")
            return ImageFont.load_default()

        # 加载字体
        title_size = 24
        header_size = 18
        normal_size = 16
        table_size = 14
        
        # 设置字体路径
        if system == "Windows":
            standard_font_path = "C:/Windows/Fonts/simhei.ttf"
            emoji_font_path = "C:/Windows/Fonts/seguiemj.ttf"
        else:  # Linux/Unix (Docker环境)
            # 使用Dockerfile中安装的Noto字体
            standard_font_path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
            # Symbola 字体路径因系统版本不同可能在不同位置
            # 尝试多个可能的路径
            possible_emoji_paths = [
                "/usr/share/fonts/truetype/ttf-ancient-fonts/Symbola.ttf",  # Debian 11+
                "/usr/share/fonts/truetype/symbola/Symbola.ttf",  # 某些系统
                "/usr/share/fonts/truetype/ancient-scripts/Symbola.ttf",  # 旧版本
            ]
            emoji_font_path = None
            for path in possible_emoji_paths:
                if os.path.exists(path):
                    emoji_font_path = path
                    logging.info(f"找到Emoji字体: {path}")
                    break
            if not emoji_font_path:
                # 动态搜索
                found_symbola = find_font_file("Symbola.ttf")
                if found_symbola:
                    emoji_font_path = found_symbola
                    logging.info(f"动态找到Symbola字体: {found_symbola}")
                else:
                    found_noto = find_font_file("NotoColorEmoji.ttf")
                    if found_noto:
                        emoji_font_path = found_noto
                        logging.info(f"动态找到NotoColorEmoji字体: {found_noto}")
                    else:
                        # 使用默认路径（可能会fallback到标准字体）
                        emoji_font_path = "/usr/share/fonts/truetype/ttf-ancient-fonts/Symbola.ttf"
                        logging.warning(f"未找到Emoji字体，将使用标准字体作为fallback")
        
        # 先加载标准字体
        title_std = get_font(standard_font_path, title_size)
        header_std = get_font(standard_font_path, header_size)
        normal_std = get_font(standard_font_path, normal_size)
        table_std = get_font(standard_font_path, table_size)
        
        fonts = {
            'title': {
                'standard': title_std,
                'emoji': get_font(emoji_font_path, title_size, title_std)
            },
            'header': {
                'standard': header_std,
                'emoji': get_font(emoji_font_path, header_size, header_std)
            },
            'normal': {
                'standard': normal_std,
                'emoji': get_font(emoji_font_path, normal_size, normal_std)
            },
            'table': {
                'standard': table_std,
                'emoji': get_font(emoji_font_path, table_size, table_std)
            }
        }
        
        # 计算行高 - 增加行高以提高可读性
        title_height = 40
        header_height = 30
        normal_height = 25
        table_height = 25
        
        # 初始位置 - 增加边距以提供更好的布局
        x_margin = 40
        y_pos = 30  # Initial y position
        
        # 创建一个足够大的图片，之后再resize
        img_height = 1000  # 预估高度
        img = Image.new('RGB', (img_width, img_height), background_color)
        draw = ImageDraw.Draw(img)
        
        def is_emoji(char):
            # 简单的Emoji判断范围，可能不完全覆盖所有Emoji
            code = ord(char)
            return (0x1F300 <= code <= 0x1F5FF or  # Misc Symbols and Pictographs
                    0x1F900 <= code <= 0x1F9FF or  # Supplemental Symbols and Pictographs
                    0x1F600 <= code <= 0x1F64F or  # Emoticons
                    0x1F680 <= code <= 0x1F6FF or  # Transport and Map Symbols
                    0x2600 <= code <= 0x26FF or    # Misc Symbols
                    0x2700 <= code <= 0x27BF or    # Dingbats
                    0xFE00 <= code <= 0xFE0F or    # Variation Selectors
                    0x1F1E6 <= code <= 0x1F1FF)    # Flags

        def draw_text_mixed(draw, xy, text, fill, font_type):
            x, y = xy
            current_fonts = fonts[font_type]
            
            for char in text:
                font = current_fonts['standard']
                if is_emoji(char):
                    font = current_fonts['emoji']
                
                # 获取字符宽度，增加异常处理
                try:
                    char_width = draw.textlength(char, font=font)
                except Exception as e:
                    # 如果当前字体失败（如默认字体不支持中文/Emoji），尝试使用标准字体
                    if font != current_fonts['standard']:
                        font = current_fonts['standard']
                        try:
                            char_width = draw.textlength(char, font=font)
                        except:
                            char_width = 14 # 最后的保底宽度
                    else:
                        char_width = 14 # 最后的保底宽度
                
                # 绘制字符，增加异常处理
                try:
                    draw.text((x, y), char, fill=fill, font=font)
                except Exception as e:
                    logging.error(f"绘制字符失败: {char}, 错误: {e}")
                
                # 更新x坐标
                x += char_width

        # 绘制文本
        y_pos = 30  # Initial y position
        table_row_count = 0
        in_table = False
        for line in report_lines:
            if "听录音统计报表" in line and not line.startswith("##"):
                # 主标题 - 添加背景色和圆角
                draw.rectangle([x_margin - 10, y_pos - 5, img_width - x_margin + 10, y_pos + title_height],
                                fill=(240, 248, 255))
                draw_text_mixed(draw, (x_margin, y_pos), line, fill=header_color, font_type='title')
                y_pos += title_height + 10
            elif line.startswith("📅") or line.startswith("📁"):
                # 副标题
                draw_text_mixed(draw, (x_margin, y_pos), line, fill=text_color, font_type='header')
                y_pos += header_height
            elif line == "":
                # 空行
                y_pos += normal_height // 2
            elif line.startswith("## 📈 汇总信息") or line.startswith("## 汇总信息"):
                # 汇总信息标题 - 添加背景色和圆角
                draw.rectangle([x_margin-5, y_pos-3, img_width-x_margin+5, y_pos+header_height+5],
                                fill=(241, 245, 249))
                draw_text_mixed(draw, (x_margin, y_pos), line.replace("## ", ""), fill=header_color, font_type='header')
                y_pos += header_height + 5
            elif line.startswith("- **总") or line.startswith("- **参") or line.startswith("- **人"):
                # 汇总信息内容 - 去除markdown格式
                clean_line = line.replace("- **", "").replace("**:", ":")
                draw_text_mixed(draw, (x_margin, y_pos), clean_line, fill=text_color, font_type='normal')
                y_pos += normal_height
            elif line.startswith("## 📋 详细数据") or line.startswith("## 详细数据"):
                # 表格标题 - 添加背景色和圆角
                draw.rectangle([x_margin-5, y_pos-3, img_width-x_margin+5, y_pos+header_height+5],
                                fill=(241, 245, 249))
                draw_text_mixed(draw, (x_margin, y_pos), line.replace("## ", ""), fill=header_color, font_type='header')
                y_pos += header_height + 10
                in_table = True
            elif in_table and line.startswith("| 排名"):
                # 表头
                table_header = line
                header_cells = [cell.strip() for cell in table_header.split('|')[1:-1]]
                
                # 绘制表头背景
                draw.rectangle([x_margin, y_pos, img_width - x_margin, y_pos + table_height + 5],
                                fill=table_header_color)
                
                # 绘制表头文字
                x_pos = x_margin + 10
                if has_monthly:
                    col_widths = [0.08, 0.12, 0.2, 0.18, 0.2, 0.22]  # 排名、团队、姓名、账号、当日听录音次数、月累计
                else:
                    col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数
                table_width = img_width - 2 * x_margin
                for i, cell in enumerate(header_cells):
                    if i < len(col_widths):
                        draw_text_mixed(draw, (x_pos, y_pos + 5), cell, fill=(255, 255, 255), font_type='table')
                        x_pos += int(table_width * col_widths[i])
                y_pos += table_height + 5
            elif in_table and line.startswith("|"):
                # 表格数据行
                cells = [cell.strip() for cell in line.split('|')[1:-1]]
                
                # 绘制行背景
                if table_row_count % 2 == 0:
                    row_color = table_row_color1
                else:
                    row_color = table_row_color2
                draw.rectangle([x_margin, y_pos, img_width - x_margin, y_pos + table_height],
                                fill=row_color)
                
                # 绘制单元格文字
                x_pos = x_margin + 10
                if has_monthly:
                    col_widths = [0.08, 0.12, 0.2, 0.18, 0.2, 0.22]  # 排名、团队、姓名、账号、当日听录音次数、月累计
                else:
                    col_widths = [0.1, 0.15, 0.25, 0.2, 0.3]  # 排名、团队、姓名、账号、操作次数
                table_width = img_width - 2 * x_margin
                for i, cell in enumerate(cells):
                    if i < len(col_widths):
                        draw_text_mixed(draw, (x_pos, y_pos + 5), cell, fill=table_text_color, font_type='table')
                        x_pos += int(table_width * col_widths[i])
                y_pos += table_height
                table_row_count += 1
            elif in_table and not line.startswith("|"):
                in_table = False
                
        # 裁剪图片 - 使用最终的y_pos计算图片高度
        img_height = y_pos + 50
        img = img.crop((0, 0, img_width, img_height))
        
        # 确保图片尺寸符合企业微信要求
        img_width, img_height = img.size
        if img_width > 900 or img_height > 900:
            # 计算缩放比例
            scale = min(900 / img_width, 900 / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 保存图片 - 使用PNG格式以保持清晰度
        logging.info(f"Saving image to {output_path}")
        img.save(output_path, 'PNG')
        logging.info(f"Image saved to {output_path}")
        
        # 同时保存一个JPEG版本用于发送
        if output_path.endswith('.png'):
            jpeg_path = output_path[:-4] + '.jpg'
            logging.info(f"Saving JPEG version to {jpeg_path}")
            img.save(jpeg_path, 'JPEG', quality=95)
            logging.info(f"JPEG version saved to {jpeg_path}")
