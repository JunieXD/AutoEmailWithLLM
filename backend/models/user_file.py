from datetime import datetime
from backend.database import db
from backend.utils.timezone_utils import get_shanghai_utcnow

class UserFile(db.Model):
    """用户文件模型"""
    __tablename__ = 'user_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False, comment='用户ID')
    file_name = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_path = db.Column(db.String(500), nullable=False, comment='文件存储路径')
    file_type = db.Column(db.String(50), nullable=False, comment='文件类型：cover_letter, resume, transcript, other')
    file_extension = db.Column(db.String(10), nullable=False, comment='文件扩展名')
    file_size = db.Column(db.Integer, nullable=True, comment='文件大小（字节）')
    description = db.Column(db.String(255), nullable=True, comment='文件描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_shanghai_utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_shanghai_utcnow, onupdate=get_shanghai_utcnow, comment='更新时间')
    
    # 建立与用户的关系
    user = db.relationship('UserProfile', backref=db.backref('files', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_extension': self.file_extension,
            'file_size': self.file_size,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_user_files(cls, user_id, file_type=None):
        """获取用户文件列表"""
        query = cls.query.filter_by(user_id=user_id)
        if file_type:
            query = query.filter_by(file_type=file_type)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_user_files_by_type(cls, user_id):
        """按类型分组获取用户文件"""
        files = cls.get_user_files(user_id)
        grouped = {
            'cover_letter': [],
            'resume': [],
            'transcript': [],
            'other': []
        }
        for file in files:
            if file.file_type in grouped:
                grouped[file.file_type].append(file.to_dict())
            else:
                grouped['other'].append(file.to_dict())
        return grouped
    
    def __repr__(self):
        return f'<UserFile {self.file_name} ({self.file_type})>'