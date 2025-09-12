from flask import Blueprint, render_template

# 创建页面路由蓝图
page_bp = Blueprint('page', __name__)


@page_bp.route('/')
def index():
    """主页"""
    return render_template('index.html')


@page_bp.route('/favicon.ico')
def favicon():
    """避免浏览器请求favicon导致404噪声"""
    return '', 204


@page_bp.route('/@vite/client')
def vite_client():
    """某些开发扩展或缓存可能会请求该路径，这里直接静默处理"""
    return '', 204


@page_bp.route('/users')
def users_page():
    """用户管理页面"""
    return render_template('user_management.html')


@page_bp.route('/settings')
def settings():
    """设置页面"""
    return render_template('settings.html')


@page_bp.route('/records')
def records():
    """发送记录页面"""
    return render_template('records.html')


@page_bp.route('/professors')
def professors_page():
    """教授管理页面"""
    return render_template('professors.html')


@page_bp.route('/email-generator')
def email_generator():
    """邮件生成页面"""
    return render_template('email_generator.html')