from datetime import datetime
from backend.database import db
from backend.utils.timezone_utils import get_shanghai_utcnow

class UserProfile(db.Model):
    """用户个人信息模型"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='姓名')
    email = db.Column(db.String(255), nullable=False, comment='邮箱')
    email_password = db.Column(db.String(255), nullable=False, comment='邮箱授权码')
    smtp_server = db.Column(db.String(255), nullable=True, comment='SMTP服务器')
    smtp_port = db.Column(db.Integer, nullable=True, comment='SMTP端口')
    
    # 文件路径
    cover_letter_path = db.Column(db.String(500), nullable=True, comment='套磁信docx文件路径')
    resume_path = db.Column(db.String(500), nullable=True, comment='简历pdf文件路径')
    
    # 其他信息
    description = db.Column(db.Text, nullable=True, comment='个人描述')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_shanghai_utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_shanghai_utcnow, onupdate=get_shanghai_utcnow, comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'cover_letter_path': self.cover_letter_path,
            'resume_path': self.resume_path,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_email_config(self):
        """获取邮件配置"""
        return {
            'name': self.name,
            'email': self.email,
            'password': self.email_password,
            'smtp_server': self.smtp_server or 'smtp.gmail.com',
            'smtp_port': self.smtp_port or 587
        }
    

    
    def __repr__(self):
        return f'<UserProfile {self.name} ({self.email})>'