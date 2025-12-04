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
            
            # 创建团队组长映射表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS team_leaders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_name TEXT NOT NULL,
                    account_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_name ON team_leaders(team_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_account_id ON team_leaders(account_id)')
            
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
        """获取指定日期的汇总数据（只显示当前存在的组长）
        
        Args:
            target_date: 目标日期
            
        Returns:
            List[Dict]: 汇总数据列表
        """
        try:
            cursor = self.conn.cursor()
            # 只返回在 team_leaders 表中存在的组长数据，并使用 team_leaders 表中的最新团队名称和姓名
            cursor.execute('''
                SELECT t.account_id as account, t.name, t.team_name as team, d.count
                FROM daily_summary d
                INNER JOIN team_leaders t ON d.account = t.account_id
                WHERE d.date = ?
                ORDER BY d.count DESC
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
        """获取指定月份的汇总数据（只显示当前存在的组长）
        
        Args:
            year_month: 年月，格式如 "2025-11"
            
        Returns:
            List[Dict]: 汇总数据列表
        """
        try:
            cursor = self.conn.cursor()
            # 只返回在 team_leaders 表中存在的组长数据，并使用 team_leaders 表中的最新团队名称和姓名
            cursor.execute('''
                SELECT t.account_id as account, t.name, t.team_name as team, m.total_count
                FROM monthly_summary m
                INNER JOIN team_leaders t ON m.account = t.account_id
                WHERE m.year_month = ?
                ORDER BY m.total_count DESC
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
        """获取指定日期的数据，同时包含当月累计（只显示当前存在的组长）
        
        Args:
            target_date: 目标日期
            
        Returns:
            List[Dict]: 包含日数据和月累计的列表
        """
        try:
            cursor = self.conn.cursor()
            year_month = target_date.strftime('%Y-%m')
            
            # 只返回在 team_leaders 表中存在的组长数据，并使用 team_leaders 表中的最新团队名称和姓名
            cursor.execute('''
                SELECT 
                    t.account_id as account, 
                    t.name, 
                    t.team_name as team, 
                    d.count as daily_count,
                    COALESCE(m.total_count, 0) as monthly_count
                FROM daily_summary d
                INNER JOIN team_leaders t ON d.account = t.account_id
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
    
    def get_all_team_leaders(self) -> List[Dict]:
        """获取所有团队组长映射
        
        Returns:
            List[Dict]: 团队组长列表
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, team_name, account_id, name, created_at, updated_at
                FROM team_leaders
                ORDER BY team_name, name
            ''')
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'team_name': row['team_name'],
                    'account_id': row['account_id'],
                    'name': row['name'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return results
            
        except Exception as e:
            logging.error(f"获取团队组长列表失败: {e}")
            return []
    
    def get_team_leader_by_id(self, leader_id: int) -> Optional[Dict]:
        """根据ID获取团队组长
        
        Args:
            leader_id: 组长ID
            
        Returns:
            Optional[Dict]: 组长信息，不存在则返回None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, team_name, account_id, name, created_at, updated_at
                FROM team_leaders
                WHERE id = ?
            ''', (leader_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'team_name': row['team_name'],
                    'account_id': row['account_id'],
                    'name': row['name'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
            
        except Exception as e:
            logging.error(f"获取团队组长失败: {e}")
            return None
    
    def add_team_leader(self, team_name: str, account_id: str, name: str) -> bool:
        """添加团队组长映射
        
        Args:
            team_name: 团队名称
            account_id: 账号ID
            name: 姓名
            
        Returns:
            bool: 是否添加成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO team_leaders (team_name, account_id, name)
                VALUES (?, ?, ?)
            ''', (team_name, account_id, name))
            
            self.conn.commit()
            logging.info(f"添加团队组长成功: {team_name} - {name} ({account_id})")
            return True
            
        except Exception as e:
            logging.error(f"添加团队组长失败: {e}")
            self.conn.rollback()
            return False
    
    def update_team_leader(self, leader_id: int, team_name: str, account_id: str, name: str) -> bool:
        """更新团队组长映射
        
        Args:
            leader_id: 组长ID
            team_name: 团队名称
            account_id: 账号ID
            name: 姓名
            
        Returns:
            bool: 是否更新成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE team_leaders
                SET team_name = ?, account_id = ?, name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (team_name, account_id, name, leader_id))
            
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logging.info(f"更新团队组长成功: ID={leader_id}")
                return True
            else:
                logging.warning(f"团队组长不存在: ID={leader_id}")
                return False
            
        except Exception as e:
            logging.error(f"更新团队组长失败: {e}")
            self.conn.rollback()
            return False
    
    def delete_team_leader(self, leader_id: int) -> bool:
        """删除团队组长映射
        
        Args:
            leader_id: 组长ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM team_leaders WHERE id = ?', (leader_id,))
            
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logging.info(f"删除团队组长成功: ID={leader_id}")
                return True
            else:
                logging.warning(f"团队组长不存在: ID={leader_id}")
                return False
            
        except Exception as e:
            logging.error(f"删除团队组长失败: {e}")
            self.conn.rollback()
            return False
    
    def get_team_mapping_dict(self) -> Dict[str, str]:
        """获取团队映射字典（账号 -> 团队名称）
        
        用于向后兼容，返回与原CSV格式相同的字典
        
        Returns:
            Dict[str, str]: {account_id: team_name}
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT account_id, team_name FROM team_leaders')
            
            mapping = {}
            for row in cursor.fetchall():
                mapping[row['account_id']] = row['team_name']
            
            return mapping
            
        except Exception as e:
            logging.error(f"获取团队映射字典失败: {e}")
            return {}
    
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
