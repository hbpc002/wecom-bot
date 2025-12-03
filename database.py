import sqlite3
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import os

class Database:
    """数据库管理类，处理听录音记录的存储和查询"""
    
    def __init__(self, db_path='wecom_bot.db'):
        """初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """初始化数据库，创建必要的表"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 允许通过列名访问
            cursor = self.conn.cursor()
            
            # 创建听录音记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listening_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account TEXT NOT NULL,
                    name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    operation_time TIMESTAMP NOT NULL,
                    date DATE NOT NULL,
                    source_file TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_account ON listening_records(account)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON listening_records(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_team ON listening_records(team)')
            
            # 创建日汇总表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    account TEXT NOT NULL,
                    name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, account)
                )
            ''')
            
            # 创建月汇总表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS monthly_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year_month TEXT NOT NULL,
                    account TEXT NOT NULL,
                    name TEXT NOT NULL,
                    team TEXT NOT NULL,
                    total_count INTEGER NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(year_month, account)
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_summary(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_monthly_year_month ON monthly_summary(year_month)')
            
            self.conn.commit()
            logging.info(f"数据库初始化成功: {self.db_path}")
            
        except Exception as e:
            logging.error(f"数据库初始化失败: {e}")
            raise
    
    def insert_listening_record(self, account: str, name: str, team: str, 
                               operation_time: datetime, source_file: str) -> bool:
        """插入单条听录音记录
        
        Args:
            account: 账号
            name: 姓名
            team: 团队名称
            operation_time: 操作时间
            source_file: 来源文件名
            
        Returns:
            bool: 是否插入成功
        """
        try:
            cursor = self.conn.cursor()
            record_date = operation_time.date()
            
            cursor.execute('''
                INSERT INTO listening_records (account, name, team, operation_time, date, source_file)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (account, name, team, operation_time, record_date, source_file))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"插入听录音记录失败: {e}")
            self.conn.rollback()
            return False
    
    def insert_batch_records(self, records: List[Dict]) -> int:
        """批量插入听录音记录（自动去重）
        
        Args:
            records: 记录列表，每条记录包含 account, name, team, operation_time, source_file
            
        Returns:
            int: 成功插入的记录数
        """
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
    
    def update_daily_summary(self, target_date: date) -> bool:
        """更新指定日期的日汇总数据
        
        Args:
            target_date: 目标日期
            
        Returns:
            bool: 是否更新成功
        """
        try:
            cursor = self.conn.cursor()
            
            # 删除旧的汇总数据
            cursor.execute('DELETE FROM daily_summary WHERE date = ?', (target_date,))
            
            # 重新计算汇总数据
            cursor.execute('''
                INSERT INTO daily_summary (date, account, name, team, count)
                SELECT date, account, name, team, COUNT(*) as count
                FROM listening_records
                WHERE date = ?
                GROUP BY date, account, name, team
            ''', (target_date,))
            
            self.conn.commit()
            logging.info(f"日汇总更新成功: {target_date}")
            return True
            
        except Exception as e:
            logging.error(f"更新日汇总失败: {e}")
            self.conn.rollback()
            return False
    
    def update_monthly_summary(self, year_month: str) -> bool:
        """更新指定月份的月汇总数据
        
        Args:
            year_month: 年月，格式如 "2025-11"
            
        Returns:
            bool: 是否更新成功
        """
        try:
            cursor = self.conn.cursor()
            
            # 删除旧的汇总数据
            cursor.execute('DELETE FROM monthly_summary WHERE year_month = ?', (year_month,))
            
            # 重新计算汇总数据
            cursor.execute('''
                INSERT INTO monthly_summary (year_month, account, name, team, total_count, updated_at)
                SELECT ?, account, name, team, SUM(count) as total_count, CURRENT_TIMESTAMP
                FROM daily_summary
                WHERE strftime('%Y-%m', date) = ?
                GROUP BY account, name, team
            ''', (year_month, year_month))
            
            self.conn.commit()
            logging.info(f"月汇总更新成功: {year_month}")
            return True
            
        except Exception as e:
            logging.error(f"更新月汇总失败: {e}")
            self.conn.rollback()
            return False
    
    def get_daily_summary(self, target_date: date) -> List[Dict]:
        """获取指定日期的汇总数据
        
        Args:
            target_date: 目标日期
            
        Returns:
            List[Dict]: 汇总数据列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT account, name, team, count
                FROM daily_summary
                WHERE date = ?
                ORDER BY count DESC
            ''', (target_date,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'account': row['account'],
                    'name': row['name'],
                    'team': row['team'],
                    'count': row['count']
                })
            
            return results
            
        except Exception as e:
            logging.error(f"获取日汇总失败: {e}")
            return []
    
    def get_monthly_summary(self, year_month: str) -> List[Dict]:
        """获取指定月份的汇总数据
        
        Args:
            year_month: 年月，格式如 "2025-11"
            
        Returns:
            List[Dict]: 汇总数据列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT account, name, team, total_count
                FROM monthly_summary
                WHERE year_month = ?
                ORDER BY total_count DESC
            ''', (year_month,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'account': row['account'],
                    'name': row['name'],
                    'team': row['team'],
                    'total_count': row['total_count']
                })
            
            return results
            
        except Exception as e:
            logging.error(f"获取月汇总失败: {e}")
            return []
    
    def get_daily_with_monthly(self, target_date: date) -> List[Dict]:
        """获取指定日期的数据，同时包含当月累计
        
        Args:
            target_date: 目标日期
            
        Returns:
            List[Dict]: 包含日数据和月累计的列表
        """
        try:
            cursor = self.conn.cursor()
            year_month = target_date.strftime('%Y-%m')
            
            cursor.execute('''
                SELECT 
                    d.account, 
                    d.name, 
                    d.team, 
                    d.count as daily_count,
                    COALESCE(m.total_count, 0) as monthly_count
                FROM daily_summary d
                LEFT JOIN monthly_summary m 
                    ON d.account = m.account AND m.year_month = ?
                WHERE d.date = ?
                ORDER BY d.count DESC
            ''', (year_month, target_date))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'account': row['account'],
                    'name': row['name'],
                    'team': row['team'],
                    'daily_count': row['daily_count'],
                    'monthly_count': row['monthly_count']
                })
            
            return results
            
        except Exception as e:
            logging.error(f"获取日数据（含月累计）失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logging.info("数据库连接已关闭")
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器"""
        self.close()
