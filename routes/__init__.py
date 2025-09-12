# Routes package
# 路由模块包

from .page_routes import page_bp
from .professor_routes import professor_bp
from .email_routes import email_bp
from .record_routes import record_bp
from .user_routes import user_bp
from .file_routes import file_bp
from .import_routes import import_bp
from .settings_routes import settings_bp

# 导出所有蓝图
__all__ = [
    'page_bp',
    'professor_bp', 
    'email_bp',
    'record_bp',
    'user_bp',
    'file_bp',
    'import_bp',
    'settings_bp'
]