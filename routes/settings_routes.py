from flask import Blueprint, request, jsonify
from backend.config import Config
import logging
import os
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

# 创建设置管理蓝图
settings_bp = Blueprint('settings', __name__, url_prefix='/api/settings')


@settings_bp.route('/upload', methods=['GET'])
def get_upload_settings():
    """获取文件上传设置"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'max_file_size': 16,  # MB
                'allowed_extensions': '.docx,.pdf,.doc,.txt,.jpg,.jpeg,.png',
                'upload_folder': 'uploads/'
            }
        })
    except Exception as e:
        logger.error(f"获取文件上传设置失败: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/log', methods=['GET'])
def get_log_settings():
    """获取日志设置"""
    try:
        from flask import current_app
        # 从 app.config 读取当前设置
        log_level = current_app.config.get('LOG_LEVEL', 'INFO')
        log_file = current_app.config.get('LOG_FILE', 'app.log')
        console_output = current_app.config.get('CONSOLE_OUTPUT', True)
        return jsonify({
            'success': True,
            'data': {
                'log_level': str(log_level).upper(),
                'log_file': log_file,
                'console_output': bool(console_output)
            }
        })
    except Exception as e:
        logger.exception(f"获取日志设置失败: {e}")
        return jsonify({'error': str(e)}), 500


@settings_bp.route('/log', methods=['POST'])
def update_log_settings():
    """更新日志设置：日志级别/文件/控制台输出"""
    try:
        from flask import current_app
        
        data = request.get_json(silent=True) or {}
        new_level = str(data.get('log_level', current_app.config.get('LOG_LEVEL', 'INFO'))).upper()
        new_file = data.get('log_file', current_app.config.get('LOG_FILE', 'app.log'))
        new_console = bool(data.get('console_log', data.get('console_output', current_app.config.get('CONSOLE_OUTPUT', True))))

        # 校验级别
        valid = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if new_level not in valid:
            return jsonify({'success': False, 'message': '无效的日志级别'}), 400

        root_logger = logging.getLogger()
        # 更新根日志级别
        root_logger.setLevel(getattr(logging, new_level, logging.INFO))

        handlers = current_app.config.get('LOG_HANDLERS', {})
        file_handler = handlers.get('file')
        error_handler = handlers.get('error')
        console_handler = handlers.get('console')

        # 统一获取 formatter 与 filters
        def _get_formatter_and_filters(src_handler):
            if src_handler is None:
                # 兜底定义一个与 Config.init_app 一致的格式
                fmt = logging.Formatter(
                    fmt='%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(method)s %(path)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                return fmt, []
            return src_handler.formatter, list(getattr(src_handler, 'filters', []))

        formatter, filters = _get_formatter_and_filters(file_handler or error_handler)

        # 替换文件处理器（如文件名变化）
        safe_name = os.path.basename(new_file) if new_file else 'app.log'
        new_path = os.path.join(Config.LOG_DIR, safe_name)
        if file_handler:
            try:
                root_logger.removeHandler(file_handler)
                file_handler.close()
            except Exception:
                pass
        new_file_handler = RotatingFileHandler(
            new_path, 
            maxBytes=Config.LOG_MAX_BYTES, 
            backupCount=Config.LOG_BACKUP_COUNT, 
            encoding='utf-8'
        )
        new_file_handler.setLevel(getattr(logging, new_level, logging.INFO))
        if formatter:
            new_file_handler.setFormatter(formatter)
        for flt in filters:
            new_file_handler.addFilter(flt)
        root_logger.addHandler(new_file_handler)
        handlers['file'] = new_file_handler

        # 控制台开关
        if new_console and not console_handler:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, new_level, logging.INFO))
            if formatter:
                console_handler.setFormatter(formatter)
            for flt in filters:
                console_handler.addFilter(flt)
            root_logger.addHandler(console_handler)
            handlers['console'] = console_handler
        elif (not new_console) and console_handler:
            try:
                root_logger.removeHandler(console_handler)
                console_handler.close()
            except Exception:
                pass
            handlers['console'] = None

        # 错误处理器级别保持 ERROR，不动
        if error_handler:
            error_handler.setLevel(logging.ERROR)

        # 回写 app.config
        current_app.config['LOG_HANDLERS'] = handlers
        current_app.config['LOG_LEVEL'] = new_level
        current_app.config['LOG_FILE'] = safe_name
        current_app.config['CONSOLE_OUTPUT'] = new_console

        # 保存设置到配置文件
        log_settings = {
            'log_settings': {
                'log_level': new_level,
                'log_file': safe_name,
                'console_output': new_console
            }
        }
        Config.save_settings(log_settings)

        return jsonify({'success': True})
    except Exception as e:
        logger.exception(f"更新日志设置失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@settings_bp.route('/database', methods=['GET'])
def get_database_settings():
    """获取数据库信息"""
    try:
        from flask import current_app
        from backend.database import db
        
        # 检查数据库连接状态
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_status = '已连接'
        except Exception:
            db_status = '连接失败'
        
        # 从配置中获取实际的数据库文件名
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_file = db_uri.replace('sqlite:///', '')
        else:
            db_file = 'unknown'
        
        return jsonify({
            'success': True,
            'data': {
                'db_type': 'SQLite',
                'db_file': db_file,
                'connection_status': db_status
            }
        })
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return jsonify({'error': str(e)}), 500