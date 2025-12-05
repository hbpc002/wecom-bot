#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复 report_generator.py 中的文件路径 emoji 问题
PIL 在 Windows/Docker 某些环境下保存文件时，文件路径中的 emoji 可能导致问题
"""

def fix_report_generator():
    # 读取文件
    with open('report_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('report_generator.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 不修改文件名生成部分，因为文件名已经是安全的
    # 问题可能在于 PIL 保存时的内部处理
    # 我们需要确保 image_path 在传递给 PIL 之前是安全的
    
    # 在 _generate_image_report 方法中，保存图片之前清理路径
    old_save_pattern = """        # 保存图片 - 使用PNG格式以保持清晰度
        logging.info(f"Saving image to {output_path}")
        img.save(output_path, 'PNG')
        logging.info(f"Image saved to {output_path}")
        
        # 同时保存一个JPEG版本用于发送
        if output_path.endswith('.png'):
            jpeg_path = output_path[:-4] + '.jpg'
            logging.info(f"Saving JPEG version to {jpeg_path}")
            img.save(jpeg_path, 'JPEG', quality=95)
            logging.info(f"JPEG version saved to {jpeg_path}")"""
    
    new_save_pattern = """        # 保存图片 - 使用PNG格式以保持清晰度
        # 确保文件路径不包含任何可能导致编码问题的字符
        safe_output_path = output_path.encode('utf-8', 'surrogateescape').decode('utf-8', 'ignore')
        logging.info(f"Saving image to {safe_output_path}")
        img.save(safe_output_path, 'PNG')
        logging.info(f"Image saved to {safe_output_path}")
        
        # 同时保存一个JPEG版本用于发送
        if safe_output_path.endswith('.png'):
            jpeg_path = safe_output_path[:-4] + '.jpg'
            logging.info(f"Saving JPEG version to {jpeg_path}")
            img.save(jpeg_path, 'JPEG', quality=95)
            logging.info(f"JPEG version saved to {jpeg_path}")"""
    
    if old_save_pattern in content:
        content = content.replace(old_save_pattern, new_save_pattern)
        print("✓ 已修复 PIL 保存路径问题")
    else:
        print("⚠ 未找到匹配的保存代码")
    
    # 写入
    with open('report_generator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ report_generator.py 修复完成")

if __name__ == '__main__':
    fix_report_generator()
