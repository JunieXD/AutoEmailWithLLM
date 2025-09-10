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
        
    print("数据库初始化完成！")

if __name__ == '__main__':
    init_database()