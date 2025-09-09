#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 添加email_records表的sender_name和sender_email字段
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    db_path = 'instance/auto_email.db'  # 根据config.py中的配置，实际在instance目录下
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(email_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"当前email_records表的字段: {columns}")
        
        # 添加sender_name字段（如果不存在）
        if 'sender_name' not in columns:
            print("添加sender_name字段...")
            cursor.execute("ALTER TABLE email_records ADD COLUMN sender_name VARCHAR(100)")
            print("sender_name字段添加成功")
        else:
            print("sender_name字段已存在")
        
        # 添加sender_email字段（如果不存在）
        if 'sender_email' not in columns:
            print("添加sender_email字段...")
            cursor.execute("ALTER TABLE email_records ADD COLUMN sender_email VARCHAR(255)")
            print("sender_email字段添加成功")
        else:
            print("sender_email字段已存在")
        
        # 提交更改
        conn.commit()
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(email_records)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"更新后email_records表的字段: {updated_columns}")
        
        conn.close()
        print("数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"数据库迁移失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    print("开始数据库迁移...")
    print(f"时间: {datetime.now()}")
    
    success = migrate_database()
    
    if success:
        print("\n迁移成功！现在可以重启应用程序。")
    else:
        print("\n迁移失败！请检查错误信息。")