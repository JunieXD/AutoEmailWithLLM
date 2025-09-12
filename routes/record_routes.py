from flask import Blueprint, request, jsonify
from backend.database import db, Professor, EmailRecord
from datetime import datetime, timedelta
import logging
import pytz

logger = logging.getLogger(__name__)

# 创建邮件记录管理蓝图
record_bp = Blueprint('record', __name__, url_prefix='/api')

# 统一的时间序列化函数
def _serialize_datetime(dt):
    """将datetime对象序列化为UTC时间字符串"""
    if not dt:
        return None
    try:
        # 如果是naive时间，由于get_shanghai_utcnow()返回的就是UTC时间（只是没有时区信息）
        # 所以直接序列化即可
        if dt.tzinfo is None:
            return dt.isoformat()
        # 有tz信息则统一转为UTC-naive
        return dt.astimezone(pytz.UTC).replace(tzinfo=None).isoformat()
    except Exception:
        return dt.isoformat()


@record_bp.route('/email-records', methods=['GET'])
def email_records():
    """获取邮件发送记录（支持分页和筛选）"""
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 获取筛选参数
        sender_name = request.args.get('sender_name', '').strip()
        university = request.args.get('university', '').strip()
        department = request.args.get('department', '').strip()
        professor_name = request.args.get('professor_name', '').strip()
        status = request.args.get('status', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        content_keyword = request.args.get('content_keyword', '').strip()
        
        # 构建查询
        query = EmailRecord.query.join(Professor)
        
        # 应用筛选条件
        if sender_name:
            query = query.filter(EmailRecord.sender_name.ilike(f'%{sender_name}%'))
        if university:
            query = query.filter(Professor.university.ilike(f'%{university}%'))
        if department:
            query = query.filter(Professor.department.ilike(f'%{department}%'))
        if professor_name:
            query = query.filter(Professor.name.ilike(f'%{professor_name}%'))
        if status:
            query = query.filter(EmailRecord.status == status)
        if content_keyword:
            query = query.filter(EmailRecord.content.ilike(f'%{content_keyword}%'))
        
        # 日期筛选
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(EmailRecord.created_at >= date_from_obj)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                # 包含整天，所以加上23:59:59
                date_to_obj = date_to_obj + timedelta(days=1) - timedelta(seconds=1)
                query = query.filter(EmailRecord.created_at <= date_to_obj)
            except ValueError:
                pass
        
        # 按创建时间降序排列
        query = query.order_by(EmailRecord.created_at.desc())
        
        # 执行分页查询
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        records = pagination.items
        
        return jsonify({
            'records': [{
                'id': r.id,
                'professor_name': r.professor.name,
                'professor_email': r.professor.email,
                'professor_university': r.professor.university,
                'professor_department': r.professor.department,
                'subject': r.subject,
                'content': r.content,
                'status': r.status,
                'sender_name': r.sender_name,
                'sender_email': r.sender_email,
                'created_at': _serialize_datetime(r.created_at),
                'sent_at': _serialize_datetime(r.sent_at)
            } for r in records],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"获取邮件记录失败: {e}")
        return jsonify({'error': str(e)}), 500


@record_bp.route('/email-records/all', methods=['GET'])
def email_records_all():
    """获取所有邮件记录（用于筛选选项）"""
    try:
        records = EmailRecord.query.join(Professor).order_by(EmailRecord.created_at.desc()).all()
        return jsonify([{
            'id': r.id,
            'professor_name': r.professor.name,
            'professor_email': r.professor.email,
            'professor_university': r.professor.university,
            'professor_department': r.professor.department,
            'subject': r.subject,
            'content': r.content,
            'status': r.status,
            'sender_name': r.sender_name,
            'sender_email': r.sender_email,
            'created_at': _serialize_datetime(r.created_at),
            'sent_at': _serialize_datetime(r.sent_at)
        } for r in records])
    except Exception as e:
        logger.error(f"获取所有邮件记录失败: {e}")
        return jsonify({'error': str(e)}), 500


@record_bp.route('/email-records/<int:record_id>', methods=['GET'])
def email_record_detail(record_id):
    """获取单个邮件记录详情"""
    try:
        record = EmailRecord.query.get_or_404(record_id)
        return jsonify({
            'id': record.id,
            'professor_name': record.professor.name,
            'professor_email': record.professor.email,
            'professor_university': record.professor.university,
            'professor_department': record.professor.department,
            'subject': record.subject,
            'content': record.content,
            'status': record.status,
            'sender_name': record.sender_name,
            'sender_email': record.sender_email,
            'recipient_email': record.professor.email,
            'send_time': _serialize_datetime(record.sent_at) if record.sent_at else _serialize_datetime(record.created_at),
            'created_at': _serialize_datetime(record.created_at),
            'sent_at': _serialize_datetime(record.sent_at)
        })
    except Exception as e:
        logger.error(f"获取邮件记录详情失败: {str(e)}")
        return jsonify({'error': str(e)}), 500