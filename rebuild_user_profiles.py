#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重建user_profiles表以匹配当前模型定义
"""

import sqlite3
import os
from datetime import datetime

def rebuild_user_profiles():
    """重建user_profiles表"""
    db_path = 'instance/auto_email.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("备份现有数据...")
            # 备份现有数据
            cursor.execute("SELECT * FROM user_profiles")
            existing_data = cursor.fetchall()
            
            # 获取现有表结构
            cursor.execute("PRAGMA table_info(user_profiles)")
            old_columns = [col[1] for col in cursor.fetchall()]
            print(f"旧表字段: {old_columns}")
            
            # 删除旧表
            cursor.execute("DROP TABLE user_profiles")
            print("删除旧表完成")
        
        # 创建新表
        create_table_sql = """
        CREATE TABLE user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            email_password VARCHAR(255) NOT NULL,
            smtp_server VARCHAR(255),
            smtp_port INTEGER,
            cover_letter_path VARCHAR(500),
            resume_path VARCHAR(500),
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_default BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        cursor.execute(create_table_sql)
        print("新表创建完成")
        
        # 如果有旧数据，尝试迁移
        if table_exists and existing_data:
            print("迁移现有数据...")
            for row in existing_data:
                # 提取可用的字段
                old_id, name, email = row[0], row[1], row[2]
                
                # 插入基本数据，其他字段使用默认值
                cursor.execute("""
                    INSERT INTO user_profiles 
                    (id, name, email, email_password, is_active, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, '', 1, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (old_id, name, email))
            
            print(f"迁移了 {len(existing_data)} 条记录")
        
        # 提交更改
        conn.commit()
        
        # 验证新表结构
        cursor.execute("PRAGMA table_info(user_profiles)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"新表字段: {new_columns}")
        
        conn.close()
        print("user_profiles表重建完成！")
        print("注意：由于表结构变化，需要重新配置用户的邮箱授权码等信息")
        return True
        
    except Exception as e:
        print(f"重建表失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    rebuild_user_profiles()