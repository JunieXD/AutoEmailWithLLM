#!/usr/bin/env python3
"""
数据库迁移脚本：添加LLM配置表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from backend.database import db, LLMConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_llm_configs():
    """添加LLM配置表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 检查表是否已存在
            inspector = db.inspect(db.engine)
            if 'llm_configs' in inspector.get_table_names():
                logger.info("LLM配置表已存在，跳过创建")
                return
            
            # 创建LLM配置表
            logger.info("开始创建LLM配置表...")
            db.create_all()
            logger.info("LLM配置表创建成功")
            
        except Exception as e:
            logger.error(f"迁移失败: {e}")
            raise

if __name__ == '__main__':
    migrate_llm_configs()
    print("LLM配置表迁移完成")