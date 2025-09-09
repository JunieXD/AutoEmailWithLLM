#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户文件表迁移脚本
"""

from app import create_app
from backend.database import db
from backend.models.user_file import UserFile
from backend.models.user_profile import UserProfile
import os

def migrate_user_files():
    """迁移用户文件数据"""
    print("开始迁移用户文件数据...")
    
    # 创建应用实例
    app = create_app()
    
    with app.app_context():
        # 创建user_files表
        db.create_all()
        print("user_files表创建完成！")
        
        # 迁移现有的文件数据
        users = UserProfile.query.all()
        
        for user in users:
            # 迁移套磁信文件
            if user.cover_letter_path and os.path.exists(user.cover_letter_path):
                # 检查是否已经存在该文件记录
                existing_file = UserFile.query.filter_by(
                    user_id=user.id,
                    file_path=user.cover_letter_path
                ).first()
                
                if not existing_file:
                    file_name = os.path.basename(user.cover_letter_path)
                    file_extension = os.path.splitext(file_name)[1].lower()
                    
                    cover_letter_file = UserFile(
                        user_id=user.id,
                        file_name=file_name,
                        file_path=user.cover_letter_path,
                        file_type='cover_letter',
                        file_extension=file_extension,
                        description='套磁信文档'
                    )
                    
                    try:
                        file_size = os.path.getsize(user.cover_letter_path)
                        cover_letter_file.file_size = file_size
                    except:
                        pass
                    
                    db.session.add(cover_letter_file)
                    print(f"迁移用户 {user.name} 的套磁信文件: {file_name}")
            
            # 迁移简历文件
            if user.resume_path and os.path.exists(user.resume_path):
                # 检查是否已经存在该文件记录
                existing_file = UserFile.query.filter_by(
                    user_id=user.id,
                    file_path=user.resume_path
                ).first()
                
                if not existing_file:
                    file_name = os.path.basename(user.resume_path)
                    file_extension = os.path.splitext(file_name)[1].lower()
                    
                    resume_file = UserFile(
                        user_id=user.id,
                        file_name=file_name,
                        file_path=user.resume_path,
                        file_type='resume',
                        file_extension=file_extension,
                        description='个人简历'
                    )
                    
                    try:
                        file_size = os.path.getsize(user.resume_path)
                        resume_file.file_size = file_size
                    except:
                        pass
                    
                    db.session.add(resume_file)
                    print(f"迁移用户 {user.name} 的简历文件: {file_name}")
        
        # 提交所有更改
        try:
            db.session.commit()
            print("用户文件数据迁移完成！")
        except Exception as e:
            db.session.rollback()
            print(f"迁移失败: {e}")
            raise
        
        # 验证迁移结果
        total_files = UserFile.query.count()
        print(f"总共迁移了 {total_files} 个文件")
        
        # 按类型统计
        cover_letters = UserFile.query.filter_by(file_type='cover_letter').count()
        resumes = UserFile.query.filter_by(file_type='resume').count()
        print(f"套磁信文件: {cover_letters} 个")
        print(f"简历文件: {resumes} 个")

if __name__ == '__main__':
    migrate_user_files()