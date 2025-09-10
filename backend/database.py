from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from backend.utils.timezone_utils import get_shanghai_utcnow

db = SQLAlchemy()

class Professor(db.Model):
    """教授信息模型"""
    __tablename__ = 'professors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='教授姓名')
    email = db.Column(db.String(200), nullable=False, unique=True, comment='邮箱地址')
    university = db.Column(db.String(200), nullable=False, comment='所在大学')
    department = db.Column(db.String(200), comment='所在院系')
    research_area = db.Column(db.Text, comment='研究领域')
    introduction = db.Column(db.Text, comment='教授介绍')
    website = db.Column(db.String(500), comment='个人网站')
    created_at = db.Column(db.DateTime, default=get_shanghai_utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_shanghai_utcnow, onupdate=get_shanghai_utcnow, comment='更新时间')
    
    # 关联邮件记录
    email_records = db.relationship('EmailRecord', backref='professor', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Professor {self.name} - {self.email}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'university': self.university,
            'department': self.department,
            'research_area': self.research_area,
            'introduction': self.introduction,
            'website': self.website,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class LLMConfig(db.Model):
    """LLM配置模型"""
    __tablename__ = 'llm_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='配置名称')
    provider = db.Column(db.String(50), nullable=False, comment='API提供商')
    api_key_encrypted = db.Column(db.Text, nullable=False, comment='加密的API密钥')
    api_base = db.Column(db.String(500), comment='API基础URL')
    model = db.Column(db.String(100), nullable=False, comment='模型名称或推理接入点ID')
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认配置')
    created_at = db.Column(db.DateTime, default=get_shanghai_utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_shanghai_utcnow, onupdate=get_shanghai_utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<LLMConfig {self.name} - {self.provider}>'
    
    def to_dict(self, include_api_key=False):
        """转换为字典格式"""
        result = {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'api_base': self.api_base,
            'model': self.model,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_api_key:
            # 只在需要时包含API密钥（已解密）
            from backend.config import Config
            result['api_key'] = Config.decrypt_api_key(self.api_key_encrypted)
        return result

class LLMPromptConfig(db.Model):
    """LLM提示词配置模型"""
    __tablename__ = 'llm_prompt_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='配置名称')
    system_prompt = db.Column(db.Text, nullable=False, comment='系统提示词')
    user_prompt_template = db.Column(db.Text, nullable=False, comment='用户提示词模板')
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认配置')
    created_at = db.Column(db.DateTime, default=get_shanghai_utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=get_shanghai_utcnow, onupdate=get_shanghai_utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<LLMPromptConfig {self.name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'system_prompt': self.system_prompt,
            'user_prompt_template': self.user_prompt_template,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class EmailRecord(db.Model):
    """邮件发送记录模型"""
    __tablename__ = 'email_records'
    
    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(db.Integer, db.ForeignKey('professors.id'), nullable=False, comment='教授ID')
    subject = db.Column(db.String(500), nullable=False, comment='邮件主题')
    content = db.Column(db.Text, nullable=False, comment='邮件内容')
    status = db.Column(db.String(20), nullable=False, default='pending', comment='发送状态: pending, sent, failed')
    error_message = db.Column(db.Text, comment='错误信息')
    sender_name = db.Column(db.String(100), comment='发送人姓名')
    sender_email = db.Column(db.String(255), comment='发送人邮箱')
    created_at = db.Column(db.DateTime, default=get_shanghai_utcnow, comment='创建时间')
    sent_at = db.Column(db.DateTime, comment='发送时间')
    
    def __repr__(self):
        return f'<EmailRecord {self.id} - {self.status}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'professor_id': self.professor_id,
            'professor_name': self.professor.name if self.professor else None,
            'professor_email': self.professor.email if self.professor else None,
            'subject': self.subject,
            'content': self.content,
            'status': self.status,
            'error_message': self.error_message,
            'sender_name': self.sender_name,
            'sender_email': self.sender_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }