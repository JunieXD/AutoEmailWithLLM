from flask import Blueprint, request, jsonify
from backend.database import db, Professor, EmailRecord
from backend.email_service import EmailService
from backend.document_service import DocumentService
from backend.models.user_profile import UserProfile
from backend.models.user_file import UserFile
from backend.utils.timezone_utils import get_shanghai_utcnow
from datetime import datetime
import logging
import os
import time

logger = logging.getLogger(__name__)

# 创建邮件管理蓝图
email_bp = Blueprint('email', __name__, url_prefix='/api')

# 初始化服务
email_service = EmailService()
document_service = DocumentService()

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
        import pytz
        return dt.astimezone(pytz.UTC).replace(tzinfo=None).isoformat()
    except Exception:
        return dt.isoformat()


@email_bp.route('/send-email', methods=['POST'])
def send_email():
    """发送单封邮件（支持指定 sender_id，缺省回退默认用户；兼容 content/email_content 字段；支持 recipient_email 回退定位教授）"""
    try:
        data = request.get_json()
        # 主题校验
        subject = data.get('subject')
        if not subject:
            return jsonify({'error': '请输入邮件主题'}), 400
        
        # 优先使用前端传入的 sender_id
        sender_id = data.get('sender_id')
        if sender_id:
            sender_user = UserProfile.query.filter_by(id=sender_id, is_active=True).first()
            if not sender_user:
                return jsonify({'error': '选择的发送用户不存在或未激活'}), 400
        else:
            # 如果没有指定发送用户，选择第一个可用用户
            sender_user = UserProfile.query.filter_by(is_active=True).first()
            if not sender_user:
                return jsonify({'error': '请先创建用户'}), 400
        
        # 获取邮件内容
        content_source = data.get('content_source', 'generated')
        if content_source == 'docx':
            docx_file_id = data.get('docx_file_id')
            if not docx_file_id:
                return jsonify({'error': '请选择docx文件'}), 400
            
            # 获取docx文件内容（HTML格式）
            content, error = document_service.get_file_content(docx_file_id, 'html')
            if error:
                return jsonify({'error': f'获取文件内容失败: {error}'}), 400
            email_content = content
        else:
            email_content = data.get('email_content') or data.get('content')
            if not email_content:
                return jsonify({'error': '请输入邮件内容'}), 400
        
        # 确定教授
        professor = None
        professor_id = data.get('professor_id')
        if professor_id:
            professor = db.session.get(Professor, professor_id)
        else:
            recipient_email = data.get('recipient_email')
            if recipient_email:
                professor = Professor.query.filter_by(email=recipient_email).first()
        if not professor:
            return jsonify({'error': '教授信息不存在，请先在教授列表中添加该教授'}), 404
        
        # 构造发件人配置（基于所选用户）
        sender_config = {
            'email': sender_user.email,
            'password': sender_user.email_password,
            'smtp_server': sender_user.smtp_server,
            'smtp_port': sender_user.smtp_port,
            'name': sender_user.name
        }
        
        # 处理附件
        attachment_file_ids = data.get('attachment_file_ids', [])
        attachments = []
        if attachment_file_ids:
            for file_id in attachment_file_ids:
                user_file = UserFile.query.filter_by(id=file_id, is_active=True).first()
                if user_file and os.path.exists(user_file.file_path):
                    # 生成显示名称
                    display_name = user_file.file_name
                    if user_file.file_type == 'resume':
                        # 简历类型自动重命名
                        ext_part = os.path.splitext(user_file.file_name)[1]
                        display_name = f"简历-{sender_user.name}{ext_part}"
                    
                    attachments.append({
                        'file_path': user_file.file_path,
                        'display_name': display_name
                    })
        
        # 邮件格式
        content_type = 'html'
        email_format = data.get('format') or data.get('format_type')
        if email_format == 'text':
            content_type = 'plain'
        elif content_source == 'docx':
            content_type = 'html'
        
        success = email_service.send_email(
            recipient_email=professor.email,
            recipient_name=professor.name,
            subject=subject,
            content=email_content,
            sender_config=sender_config,
            attachments=attachments,
            content_type=content_type
        )
        
        # 记录发送结果
        email_record = EmailRecord(
            professor_id=professor.id,
            subject=subject,
            content=email_content,
            status='sent' if success else 'failed',
            sender_name=sender_user.name,
            sender_email=sender_user.email,
            sent_at=get_shanghai_utcnow() if success else None
        )
        db.session.add(email_record)
        db.session.commit()
        
        if success:
            return jsonify({'message': '邮件发送成功', 'success': True})
        else:
            return jsonify({'error': '邮件发送失败', 'success': False}), 500

    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@email_bp.route('/generate-document-email', methods=['POST'])
def generate_document_email():
    """基于文档生成邮件预览"""
    try:
        data = request.get_json()
        sender_id = data.get('sender_id')
        selected_documents = data.get('selected_documents', [])
        selected_professors = data.get('selected_professors', [])
        school = data.get('school', '')
        college = data.get('college', '')
        custom_subject = data.get('custom_subject', '')
        batch_mode = data.get('batch_mode', False)
        
        if not sender_id:
            return jsonify({'success': False, 'message': '请选择发送人'}), 400
        
        if not selected_documents:
            return jsonify({'success': False, 'message': '请选择至少一个文档'}), 400
            
        if not selected_professors:
            return jsonify({'success': False, 'message': '请选择至少一个教授或学院'}), 400
        
        # 获取发送人信息
        sender = UserProfile.query.filter_by(id=sender_id, is_active=True).first()
        if not sender:
            return jsonify({'success': False, 'message': '发送人信息不存在'}), 404
        
        # 获取文档内容（套磁信模板）
        template_content = None
        template_filename = None
        for doc_id in selected_documents:
            user_file = UserFile.query.filter_by(id=doc_id, is_active=True).first()
            if user_file:
                content, error = document_service.get_file_content(doc_id, 'html')
                if content:
                    template_content = content
                    template_filename = user_file.file_name
                    break  # 只使用第一个文档作为模板
        
        # 获取教授信息
        professors = []
        if batch_mode:
            # 批量模式：可能传递学院名称或教授ID
            for item in selected_professors:
                # 尝试作为教授ID查询
                try:
                    prof_id = int(item)
                    professor = db.session.get(Professor, prof_id)
                    if professor:
                        professors.append({
                            'name': professor.name,
                            'university': professor.university,
                            'department': professor.department,
                            'research_area': professor.research_area
                        })
                except (ValueError, TypeError):
                    # 如果不是数字，则作为学院名称查询
                    dept_professors = Professor.query.filter_by(department=item).all()
                    for professor in dept_professors:
                        professors.append({
                            'name': professor.name,
                            'university': professor.university,
                            'department': professor.department,
                            'research_area': professor.research_area
                        })
        else:
            # 单个模式：根据教授ID查询
            for prof_id in selected_professors:
                professor = db.session.get(Professor, prof_id)
                if professor:
                    professors.append({
                        'name': professor.name,
                        'university': professor.university,
                        'department': professor.department,
                        'research_area': professor.research_area
                    })
        
        # 检查是否有模板内容
        if not template_content:
            return jsonify({'success': False, 'message': '无法读取套磁信文档内容'}), 400
        
        # 生成邮件预览（为每个教授生成）
        email_previews = []
        
        # 获取当前日期
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        for professor in professors:
            # 准备替换字典
            replacements = {
                '{{name}}': professor['name'],
                '{{professor_name}}': professor['name'],
                '{{university}}': professor['university'] or '',
                '{{department}}': professor['department'] or '',
                '{{research_area}}': professor['research_area'] or '',
                '{{research_direction}}': professor['research_area'] or '',
                '{{date}}': current_date,
                '{{sender_name}}': sender.name,
                '{{sender_email}}': sender.email,
                '{{school}}': school,
                '{{college}}': college
            }
            
            # 执行模板替换
            email_content = template_content
            for placeholder, replacement in replacements.items():
                email_content = email_content.replace(placeholder, replacement)
            
            # 生成邮件主题（也支持关键词替换）
            if custom_subject:
                subject = custom_subject
                # 对自定义主题也进行关键词替换
                for placeholder, replacement in replacements.items():
                    subject = subject.replace(placeholder, replacement)
            else:
                subject = f"{sender.name}"
            
            email_previews.append({
                'professor_name': professor['name'],
                'professor_university': professor['university'],
                'subject': subject,
                'content': email_content
            })
        
        return jsonify({
            'success': True,
            'email_previews': email_previews,
            'template_filename': template_filename,
            'sender': {
                'name': sender.name,
                'email': sender.email
            },
            'total_professors': len(professors),
            'message': '邮件预览生成成功'
        })
        
    except Exception as e:
        logger.error(f"生成文档邮件预览失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@email_bp.route('/send-batch-emails', methods=['POST'])
def send_batch_emails():
    """批量发送纯文本邮件（支持指定 sender_id，缺省回退默认用户）"""
    try:
        data = request.get_json()
        professors = data.get('professors', [])
        subject = data.get('subject', '')
        content = data.get('content', '')
        send_interval = int(data.get('send_interval', 5) or 0)
        personalize = bool(data.get('personalize', False))
        sender_id = data.get('sender_id')

        if not professors:
            return jsonify({'error': '请选择至少一个教授'}), 400
        if not subject:
            return jsonify({'error': '请输入邮件主题'}), 400
        if not content:
            return jsonify({'error': '请输入邮件内容'}), 400

        # 确定发送用户
        if sender_id:
            sender_user = UserProfile.query.filter_by(id=sender_id, is_active=True).first()
            if not sender_user:
                return jsonify({'error': '选择的发送用户不存在或未激活'}), 400
        else:
            # 如果没有指定发送用户，选择第一个可用用户
            sender_user = UserProfile.query.filter_by(is_active=True).first()
            if not sender_user:
                return jsonify({'error': '请先创建用户'}), 400

        current_date = datetime.now().strftime('%Y年%m月%d日')

        success_count = 0
        failed_count = 0
        failed_emails = []

        for idx, professor_data in enumerate(professors):
            try:
                professor_id = professor_data.get('id')
                professor = db.session.get(Professor, professor_id) if professor_id else None
                if not professor:
                    failed_count += 1
                    failed_emails.append({
                        'professor_id': professor_id,
                        'professor_name': professor_data.get('name', f'ID:{professor_id}'),
                        'email': professor_data.get('email', 'unknown'),
                        'error': '教授信息不存在'
                    })
                    continue

                # 个性化替换
                replacements = {
                    '{{name}}': professor.name or '',
                    '{{date}}': current_date,
                    '{{university}}': professor.university or '',
                    '{{department}}': professor.department or '',
                    '{{research_direction}}': professor.research_area or ''
                }
                personalized_subject = subject
                personalized_content = content
                if personalize:
                    for placeholder, value in replacements.items():
                        personalized_subject = personalized_subject.replace(placeholder, value)
                        personalized_content = personalized_content.replace(placeholder, value)

                # 处理附件（支持 attachment_file_ids 或 attachments 为ID列表）
                attachment_ids = data.get('attachment_file_ids') or data.get('attachments') or []
                attachments = []
                if isinstance(attachment_ids, list) and attachment_ids:
                    for file_id in attachment_ids:
                        try:
                            # 仅处理整数ID
                            file_id_int = int(file_id)
                        except Exception:
                            continue
                        user_file = UserFile.query.filter_by(id=file_id_int, is_active=True).first()
                        if user_file and os.path.exists(user_file.file_path):
                            display_name = user_file.file_name
                            if user_file.file_type == 'resume':
                                ext_part = os.path.splitext(user_file.file_name)[1]
                                display_name = f"简历-{sender_user.name}{ext_part}"
                            attachments.append({
                                'file_path': user_file.file_path,
                                'display_name': display_name
                            })

                # 发送邮件
                sender_config = {
                    'email': sender_user.email,
                    'name': sender_user.name,
                    'password': sender_user.email_password,
                    'smtp_server': sender_user.smtp_server,
                    'smtp_port': sender_user.smtp_port
                }

                success = email_service.send_email(
                    recipient_email=professor.email,
                    recipient_name=professor.name,
                    subject=personalized_subject,
                    content=personalized_content,
                    sender_config=sender_config,
                    attachments=attachments,
                    content_type='plain'
                )

                # 记录发送结果
                email_record = EmailRecord(
                    professor_id=professor.id,
                    subject=personalized_subject,
                    content=personalized_content,
                    status='sent' if success else 'failed',
                    sender_name=sender_user.name,
                    sender_email=sender_user.email,
                    sent_at=get_shanghai_utcnow() if success else None
                )
                db.session.add(email_record)

                if success:
                    success_count += 1
                    logger.info(f'批量纯文本邮件发送成功: {professor.name} <{professor.email}>')
                else:
                    failed_count += 1
                    failed_emails.append({
                        'professor_id': professor.id,
                        'professor_name': professor.name,
                        'email': professor.email,
                        'error': '邮件发送失败'
                    })

                # 发送间隔
                if idx < len(professors) - 1 and send_interval > 0:
                    time.sleep(send_interval)

            except Exception as e:
                failed_count += 1
                failed_emails.append({
                    'professor_id': professor_data.get('id', 'unknown'),
                    'professor_name': professor_data.get('name', 'unknown'),
                    'email': professor_data.get('email', 'unknown'),
                    'error': str(e)
                })
                logger.error(f'批量发送纯文本邮件出错: {str(e)}')
        
        # 提交
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'邮件发送完成！成功: {success_count}，失败: {failed_count}',
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_emails': failed_emails
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'批量发送纯文本邮件失败: {str(e)}')
        return jsonify({'error': f'发送失败: {str(e)}'}), 500


@email_bp.route('/send-document-email', methods=['POST'])
def send_document_email():
    """批量发送文档邮件"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        professors = data.get('professors', [])
        documents = data.get('documents', [])
        subject = data.get('subject', '')
        send_interval = data.get('send_interval', 5)
        attachment_ids = data.get('attachments', [])
        sender_id = data.get('sender_id')
        
        if not professors:
            return jsonify({'error': '请选择至少一个教授'}), 400
        
        if not documents:
            return jsonify({'error': '请选择至少一个文档'}), 400
            
        if not subject:
            return jsonify({'error': '请输入邮件主题'}), 400
        
        # 确定发送用户：优先使用前端选择的sender_id，缺省则回退到默认用户
        if sender_id:
            sender_profile = UserProfile.query.filter_by(id=sender_id, is_active=True).first()
            if not sender_profile:
                return jsonify({'error': '选择的发送用户不存在或未激活'}), 400
        else:
            # 如果没有指定发送用户，选择第一个可用用户
            sender_profile = UserProfile.query.filter_by(is_active=True).first()
            if not sender_profile:
                return jsonify({'error': '请先创建用户'}), 400
        
        # 获取文档内容（HTML格式）
        document_id = documents[0]['id']  # 使用第一个文档
        html_content, error = document_service.get_file_content(document_id, 'html')
        if error:
            return jsonify({'error': f'获取文档内容失败: {error}'}), 400
        
        # 获取当前日期
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        success_count = 0
        failed_count = 0
        failed_emails = []
        
        for professor_data in professors:
            try:
                professor_id = professor_data['id']
                professor = db.session.get(Professor, professor_id)
                if not professor:
                    failed_count += 1
                    failed_emails.append({
                        'professor_id': professor_id,
                        'professor_name': professor_data.get('name', f'ID:{professor_id}'),
                        'email': professor_data.get('email', 'unknown'),
                        'error': '教授信息不存在'
                    })
                    continue
                
                # 准备替换字典
                replacements = {
                    '{{name}}': professor.name,
                    '{{date}}': current_date,
                    '{{university}}': professor.university or '',
                    '{{department}}': professor.department or '',
                    '{{research_direction}}': professor.research_area or ''
                }
                
                # 替换邮件主题中的关键词
                personalized_subject = subject
                for placeholder, value in replacements.items():
                    personalized_subject = personalized_subject.replace(placeholder, value)
                
                # 替换邮件内容中的关键词
                personalized_content = html_content
                for placeholder, value in replacements.items():
                    personalized_content = personalized_content.replace(placeholder, value)
                
                # 已在函数开始处确定sender_profile，无需在循环内再次获取
                sender_user = sender_profile
                
                # 处理附件
                attachments = []
                if attachment_ids:
                    for file_id in attachment_ids:
                        user_file = UserFile.query.filter_by(id=file_id, is_active=True).first()
                        if user_file and os.path.exists(user_file.file_path):
                            # 生成显示名称
                            display_name = user_file.file_name
                            if user_file.file_type == 'resume':
                                # 简历类型自动重命名
                                ext_part = os.path.splitext(user_file.file_name)[1]
                                display_name = f"简历-{sender_user.name}{ext_part}"
                            
                            attachments.append({
                                'file_path': user_file.file_path,
                                'display_name': display_name
                            })
                
                # 发送邮件（使用所选发送用户的配置）
                sender_config = {
                    'email': sender_user.email,
                    'name': sender_user.name,
                    'password': sender_user.email_password,
                    'smtp_server': sender_user.smtp_server,
                    'smtp_port': sender_user.smtp_port
                }
                
                success = email_service.send_email(
                    recipient_email=professor.email,
                    recipient_name=professor.name,
                    subject=personalized_subject,
                    content=personalized_content,
                    sender_config=sender_config,
                    content_type='html',
                    attachments=attachments
                )
                
                # 记录发送结果
                email_record = EmailRecord(
                    professor_id=professor_id,
                    subject=personalized_subject,
                    content=personalized_content,
                    status='sent' if success else 'failed',
                    sender_name=sender_user.name,
                    sender_email=sender_user.email,
                    sent_at=get_shanghai_utcnow() if success else None
                )
                db.session.add(email_record)
                
                if success:
                    success_count += 1
                    logger.info(f'文档邮件发送成功: {professor.name} <{professor.email}>')
                else:
                    failed_count += 1
                    failed_emails.append({
                        'professor_id': professor_id,
                        'professor_name': professor.name,
                        'email': professor.email,
                        'error': '邮件发送失败'
                    })
                
                # 如果不是最后一个教授，等待指定间隔
                if professor_data != professors[-1] and send_interval > 0:
                    time.sleep(send_interval)
                    
            except Exception as e:
                failed_count += 1
                failed_emails.append({
                    'professor_id': professor_data.get('id', 'unknown'),
                    'professor_name': professor_data.get('name', 'unknown'),
                    'email': professor_data.get('email', 'unknown'),
                    'error': str(e)
                })
                logger.error(f'发送文档邮件时出错: {str(e)}')
        
        # 提交数据库事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'邮件发送完成！成功: {success_count}，失败: {failed_count}',
            'success_count': success_count,
            'failed_count': failed_count,
            'failed_emails': failed_emails
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'批量发送文档邮件失败: {str(e)}')
        return jsonify({'error': f'发送失败: {str(e)}'}), 500