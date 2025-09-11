import os
from datetime import timedelta
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging
from logging.handlers import RotatingFileHandler
import sys
import re

class Config:
    """应用配置类"""
    
    # Flask基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///auto_email.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 邮件配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.163.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'
    CONSOLE_OUTPUT = os.environ.get('CONSOLE_OUTPUT', 'true').lower() in ['true', 'on', '1']
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES') or 5 * 1024 * 1024)
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT') or 5)

    @staticmethod
    def init_app(app):
        """初始化应用配置与日志系统"""
        # 确保上传目录与日志目录存在
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.LOG_DIR, exist_ok=True)

        # 计算日志级别
        level_name = app.config.get('LOG_LEVEL', Config.LOG_LEVEL)
        level = getattr(logging, str(level_name).upper(), logging.INFO)
        log_file_name = app.config.get('LOG_FILE', Config.LOG_FILE)
        console_output = app.config.get('CONSOLE_OUTPUT', Config.CONSOLE_OUTPUT)

        # 清理根日志器已有的处理器，避免重复日志
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass
        root_logger.setLevel(level)

        # 捕获 Python warnings 到 logging
        logging.captureWarnings(True)

        # 定义请求上下文过滤器
        class RequestContextFilter(logging.Filter):
            def filter(self, record):
                try:
                    from flask import has_request_context, request, g
                    if has_request_context():
                        record.request_id = getattr(g, 'request_id', '-')
                        record.method = request.method
                        record.path = request.path
                        record.remote_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
                    else:
                        record.request_id = '-'
                        record.method = '-'
                        record.path = '-'
                        record.remote_addr = '-'
                except Exception:
                    record.request_id = '-'
                    record.method = '-'
                    record.path = '-'
                    record.remote_addr = '-'
                return True

        # 敏感信息脱敏过滤器
        class RedactFilter(logging.Filter):
            SENSITIVE_KEYS = ['password', 'email_password', 'authorization', 'api_key', 'token', 'secret']
            def filter(self, record):
                try:
                    msg = record.getMessage()
                    # key:value 或 key="value" 的常见形式脱敏
                    for key in self.SENSITIVE_KEYS:
                        # JSON风格
                        msg = re.sub(rf'(\"?{key}\"?\s*:\s*\")(.*?)(\")', rf'"{key}":"***"', msg, flags=re.IGNORECASE)
                        # k=v 或 k: v
                        msg = re.sub(rf'({key}\s*[:=]\s*)([^\s,;]+)', rf'\1***', msg, flags=re.IGNORECASE)
                    record.msg = msg
                    record.args = ()
                except Exception:
                    pass
                return True

        context_filter = RequestContextFilter()
        redact_filter = RedactFilter()

        # 定义统一的格式
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(method)s %(path)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 普通日志文件（可轮转）
        app_log_path = os.path.join(Config.LOG_DIR, log_file_name)
        file_handler = RotatingFileHandler(app_log_path, maxBytes=Config.LOG_MAX_BYTES, backupCount=Config.LOG_BACKUP_COUNT, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        file_handler.addFilter(redact_filter)
        root_logger.addHandler(file_handler)

        # 错误日志单独文件（可轮转）
        error_log_path = os.path.join(Config.LOG_DIR, 'error.log')
        error_handler = RotatingFileHandler(error_log_path, maxBytes=Config.LOG_MAX_BYTES, backupCount=Config.LOG_BACKUP_COUNT, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(context_filter)
        error_handler.addFilter(redact_filter)
        root_logger.addHandler(error_handler)

        # 控制台输出
        console_handler = None
        if console_output:
            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            console_handler.addFilter(context_filter)
            console_handler.addFilter(redact_filter)
            root_logger.addHandler(console_handler)

        # 将处理器保存到 app.config 便于后续动态调整
        app.config['LOG_HANDLERS'] = {
            'file': file_handler,
            'error': error_handler,
            'console': console_handler
        }

    @staticmethod
    def _get_encryption_key():
        """获取加密密钥"""
        password = Config.SECRET_KEY.encode()
        salt = b'auto_email_salt'  # 固定盐值，实际应用中应该使用随机盐值
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///auto_email_dev.db'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///auto_email_prod.db'

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}