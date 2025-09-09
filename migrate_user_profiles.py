#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加user_profiles表的email_password字段
"""

import sqlite3
import os
from datetime import datetime

def migrate_user_profiles():
    """执行user_profiles表迁移"""
    db_path = 'instance/auto_email.db'  # 根据config.py中的配置，实际在instance目录下
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查user_profiles表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
        if not cursor.fetchone():
            print("user_profiles表不存在，需要先初始化数据库")
            conn.close()
            return False
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(user_profiles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"当前user_profiles表的字段: {columns}")
        
        # 添加email_password字段（如果不存在）
        if 'email_password' not in columns:
            print("添加email_password字段...")
            cursor.execute("ALTER TABLE user_profiles ADD COLUMN email_password VARCHAR(255) NOT NULL DEFAULT ''")
            print("email_password字段添加成功")
        else:
            print("email_password字段已存在")
        
        # 提交更改
        conn.commit()
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(user_profiles)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"更新后user_profiles表的字段: {updated_columns}")
        
        conn.close()
        print("user_profiles表迁移完成！")
        return True
        
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    migrate_user_profiles()