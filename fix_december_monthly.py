#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复12月的月累计数据问题
手动触发月汇总更新
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import Database
from datetime import date

def fix_december_monthly():
    """修复12月的月累计数据"""
    print("=" * 60)
    print("修复12月月累计数据")
    print("=" * 60)
    
    db = Database(db_path='data/wecom_bot.db')
    
    try:
        year_month = '2025-12'
        
        # 先查看更新前的数据
        print(f"\n更新前 - 查询杨晨浩的月累计数据:")
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT year_month, account, name, team, total_count
            FROM monthly_summary
            WHERE account = 'KF77130230' AND year_month = ?
        ''', (year_month,))
        
        before = cursor.fetchone()
        if before:
            print(f"  账号: {before['account']}, 姓名: {before['name']}, 月累计: {before['total_count']}")
        else:
            print("  未找到数据")
        
        # 执行更新
        print(f"\n正在更新 {year_month} 的月汇总数据...")
        success = db.update_monthly_summary(year_month)
        
        if success:
            print("✓ 月汇总更新成功！")
            
            # 查看更新后的数据
            print(f"\n更新后 - 查询杨晨浩的月累计数据:")
            cursor.execute('''
                SELECT year_month, account, name, team, total_count
                FROM monthly_summary
                WHERE account = 'KF77130230' AND year_month = ?
            ''', (year_month,))
            
            after = cursor.fetchone()
            if after:
                print(f"  账号: {after['account']}, 姓名: {after['name']}, 月累计: {after['total_count']}")
                
                # 验证是否正确
                cursor.execute('''
                    SELECT SUM(count) as expected_total
                    FROM daily_summary
                    WHERE account = 'KF77130230' AND strftime('%Y-%m', date) = ?
                ''', (year_month,))
                
                expected = cursor.fetchone()
                if expected and after['total_count'] == expected['expected_total']:
                    print(f"  ✓ 验证成功：月累计 {after['total_count']} = 预期值 {expected['expected_total']}")
                else:
                    print(f"  ✗ 验证失败：月累计 {after['total_count']} != 预期值 {expected['expected_total']}")
            else:
                print("  ✗ 更新后仍未找到数据")
                
            # 显示所有12月的月累计数据统计
            print(f"\n12月月累计数据统计:")
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM monthly_summary
                WHERE year_month = ?
            ''', (year_month,))
            
            count = cursor.fetchone()
            print(f"  总记录数: {count['count']}")
            
        else:
            print("✗ 月汇总更新失败")
            
    except Exception as e:
        print(f"✗ 修复过程出错: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("修复完成")
    print("=" * 60)

if __name__ == '__main__':
    fix_december_monthly()
