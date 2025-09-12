from flask import Flask, g
from flask_cors import CORS
import logging
import uuid
from werkzeug.exceptions import HTTPException
from flask import request, jsonify

# 导入配置和数据库
from backend.config import Config
from backend.database import db

# 导入所有路由蓝图
from routes import (
    page_bp, professor_bp, email_bp, record_bp, 
    user_bp, file_bp, import_bp, settings_bp
)

# 移除原本的 basicConfig，统一使用 Config.init_app 进行日志初始化
logger = logging.getLogger(__name__)


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__, 
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # 加载配置
    app.config.from_object(Config)

    # 初始化日志系统（可轮转文件、错误日志分离、请求上下文字段）
    Config.init_app(app)
    
    # 启用CORS
    CORS(app)
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 注册请求处理钩子
    _register_request_handlers(app)
    
    # 注册错误处理器
    _register_error_handlers(app)
    
    # 注册所有蓝图
    _register_blueprints(app)
    
    return app


def _register_request_handlers(app):
    """注册请求处理钩子"""
    
    @app.before_request
    def _before_request_logging():
        """请求开始：生成请求ID并记录开始日志"""
        g.request_id = str(uuid.uuid4())
        try:
            remote = request.headers.get('X-Forwarded-For', request.remote_addr)
        except Exception:
            remote = '-'
        logging.getLogger('request').info(f"Request start | {request.method} {request.path} | from {remote}")
    
    @app.after_request
    def _after_request_logging(response):
        """请求结束：记录结束日志"""
        logging.getLogger('request').info(f"Request end   | {request.method} {request.path} | status {response.status_code}")
        return response


def _register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(HTTPException)
    def _handle_http_exception(e):
        """全局HTTP异常处理：记录堆栈，返回JSON错误"""
        logger_app = logging.getLogger('app')
        path = request.path
        # 对常见的无害 404 路径直接安静处理，避免噪声
        if e.code == 404 and path in ('/favicon.ico', '/@vite/client'):
            return '', 204
        # 404 记录为 INFO，避免在 WARNING 级别下刷屏
        if e.code == 404:
            logger_app.info(f"HTTPException {e.code} on {request.method} {path}: {e.description}")
        elif e.code >= 500:
            logger_app.error(f"HTTPException {e.code} on {request.method} {path}: {e.description}")
        else:
            logger_app.warning(f"HTTPException {e.code} on {request.method} {path}: {e.description}")
        return jsonify({'error': e.name, 'message': e.description}), e.code

    @app.errorhandler(Exception)
    def _handle_exception(e):
        """全局异常处理"""
        logging.getLogger('app').exception(f"Unhandled exception: {str(e)}")
        return jsonify({'error': '服务器内部错误', 'message': str(e)}), 500


def _register_blueprints(app):
    """注册所有蓝图"""
    # 注册页面路由蓝图（无前缀）
    app.register_blueprint(page_bp)
    
    # 注册API路由蓝图
    app.register_blueprint(professor_bp)
    app.register_blueprint(email_bp)
    app.register_blueprint(record_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(settings_bp)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)