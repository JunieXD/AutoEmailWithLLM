#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时区工具函数
"""

from datetime import datetime
import pytz

# 上海时区
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

def get_shanghai_now():
    """获取上海时区的当前时间"""
    return datetime.now(SHANGHAI_TZ)

def get_shanghai_utcnow():
    """获取上海时区的当前时间（用于数据库存储）"""
    # 获取上海时区的当前时间，然后转换为UTC存储
    shanghai_time = datetime.now(SHANGHAI_TZ)
    return shanghai_time.astimezone(pytz.UTC).replace(tzinfo=None)

def format_shanghai_time(dt):
    """将UTC时间格式化为上海时区显示"""
    if dt is None:
        return None
    
    # 如果是naive datetime，假设它是UTC时间
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # 转换为上海时区
    shanghai_time = dt.astimezone(SHANGHAI_TZ)
    return shanghai_time.strftime('%Y-%m-%d %H:%M:%S')

def to_shanghai_timezone(dt):
    """将UTC时间转换为上海时区"""
    if dt is None:
        return None
    
    # 如果是naive datetime，假设它是UTC时间
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    # 转换为上海时区
    return dt.astimezone(SHANGHAI_TZ)