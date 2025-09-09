#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

from app import create_app
from backend.database import db

def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 创建应用实例
    app = create_app()
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建完成！")
        
        # 检查表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"已创建的表: {tables}")
        
        # 检查email_records表的字段
        if 'email_records' in tables:
            columns = inspector.get_columns('email_records')
            column_names = [col['name'] for col in columns]
            print(f"email_records表的字段: {column_names}")
            
            if 'sender_name' in column_names and 'sender_email' in column_names:
                print("sender_name和sender_email字段已存在")
            else:
                print("需要添加sender_name和sender_email字段")
        
    print("数据库初始化完成！")

if __name__ == '__main__':
    init_database()