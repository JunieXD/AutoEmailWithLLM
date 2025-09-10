from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import logging

# 导入自定义模块
from backend.email_service import EmailService
from backend.llm_service import LLMService
from backend.database import db, Professor, EmailRecord
from backend.config import Config
from backend.import_service import ImportService
from backend.user_service import UserService

from backend.document_service import DocumentService
from backend.models.user_profile import UserProfile
from backend.models.user_file import UserFile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__, 
                static_folder='frontend/static',
                template_folder='frontend/templates')
    
    # 加载配置
    app.config.from_object(Config)
    
    # 启用CORS
    CORS(app)
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    # 初始化服务
    email_service = EmailService()
    llm_service = LLMService()
    import_service = ImportService()
    user_service = UserService()
    
    document_service = DocumentService()
    
    @app.route('/')
    def index():
        """主页"""
        return render_template('index.html')
    
    @app.route('/users')
    def users_page():
        """用户管理页面"""
        return render_template('user_management.html')
    
    @app.route('/settings')
    def settings():
        """设置页面"""
        return render_template('settings.html')
    
    @app.route('/records')
    def records():
        """发送记录页面"""
        return render_template('records.html')
    
    @app.route('/professors')
    def professors_page():
        """教授管理页面"""
        return render_template('professors.html')
    
    @app.route('/email-generator')
    def email_generator():
        """邮件生成页面"""
        return render_template('email_generator.html')
    
    @app.route('/api/professors', methods=['GET', 'POST'])
    def professors():
        """教授信息管理"""
        if request.method == 'GET':
            professors = Professor.query.all()
            return jsonify([{
                'id': p.id,
                'name': p.name,
                'email': p.email,
                'university': p.university,
                'department': p.department,
                'research_area': p.research_area,
                'introduction': p.introduction,
                'created_at': p.created_at.isoformat()
            } for p in professors])
        
        elif request.method == 'POST':
            try:
                data = request.get_json()
                professor = Professor(
                    name=data['name'],
                    email=data['email'],
                    university=data['university'],
                    department=data.get('department', ''),
                    research_area=data.get('research_area', ''),
                    introduction=data.get('introduction', '')
                )
                db.session.add(professor)
                db.session.commit()
                return jsonify({'message': '教授信息添加成功', 'id': professor.id})
            except Exception as e:
                db.session.rollback()
                if 'UNIQUE constraint failed: professors.email' in str(e):
                    return jsonify({'error': '该邮箱地址已存在，请使用其他邮箱'}), 400
                else:
                    logger.error(f'添加教授失败: {str(e)}')
                    return jsonify({'error': '添加教授失败，请稍后重试'}), 500
    
    @app.route('/api/professors/<int:professor_id>', methods=['GET', 'PUT', 'DELETE'])
    def professor_detail(professor_id):
        """单个教授信息管理"""
        professor = Professor.query.get_or_404(professor_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': professor.id,
                'name': professor.name,
                'email': professor.email,
                'university': professor.university,
                'department': professor.department,
                'research_area': professor.research_area,
                'introduction': professor.introduction,
                'created_at': professor.created_at.isoformat()
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            professor.name = data.get('name', professor.name)
            professor.email = data.get('email', professor.email)
            professor.university = data.get('university', professor.university)
            professor.department = data.get('department', professor.department)
            professor.research_area = data.get('research_areas', professor.research_area)  # 注意字段名映射
            professor.introduction = data.get('introduction', professor.introduction)
            
            db.session.commit()
            return jsonify({'success': True, 'message': '教授信息更新成功'})
        
        elif request.method == 'DELETE':
            db.session.delete(professor)
            db.session.commit()
            return jsonify({'message': '教授信息删除成功'})
    
    @app.route('/api/generate-email', methods=['POST'])
    def generate_email():
        """生成个性化套磁信"""
        try:
            data = request.get_json()
            
            # 支持新的AI表单格式
            professor_ids = data.get('professor_ids', [])
            professor_id = data.get('professor_id')
            sender_user_id = data.get('sender_user_id')
            
            # 兼容旧格式：如果没有professor_ids但有professor_id，转换为列表
            if not professor_ids and professor_id:
                professor_ids = [professor_id]
            elif not professor_ids:
                return jsonify({'error': '请选择至少一个教授'}), 400
            
            # 目前只处理第一个教授（后续可扩展为批量处理）
            target_professor_id = professor_ids[0]
            
            self_introduction_doc_id = data.get('self_introduction_doc_id')
            self_introduction = data.get('self_introduction', '')  # 兼容旧版本
            llm_config = data.get('llm_config', {})
            custom_subject = data.get('custom_subject', '')
            additional_requirements = data.get('additional_requirements', '')
            
            professor = db.session.get(Professor, target_professor_id)
            if not professor:
                return jsonify({'error': '教授信息不存在'}), 404
            
            # 检查教授是否有研究方向信息
            if not professor.research_area or professor.research_area.strip() == '':
                return jsonify({'error': '该教授缺少研究方向信息，无法生成个性化邮件'}), 400
            
            # 获取自荐信内容
            if self_introduction_doc_id:
                # 从文档获取自荐信内容
                content, error = document_service.get_file_content(self_introduction_doc_id, 'text')
                if error:
                    return jsonify({'error': f'获取自荐信内容失败: {error}'}), 400
                self_introduction = content
            elif not self_introduction:
                return jsonify({'error': '请提供自荐信内容或选择自荐信文档'}), 400
            
            # 获取LLM提示词配置
            from backend.database import LLMPromptConfig
            prompt_config = LLMPromptConfig.query.filter_by(is_default=True).first()
            
            # 创建LLM服务实例（使用前端配置）
            generate_llm_service = LLMService(
                api_key=llm_config.get('apiKey'),
                api_base=llm_config.get('apiBase'),
                model=llm_config.get('model'),
                provider=llm_config.get('provider', 'openai')
            )
            
            # 使用LLM生成个性化邮件内容（纯文本格式）
            email_content = generate_llm_service.generate_email(
                professor_info={
                    'name': professor.name,
                    'university': professor.university,
                    'department': professor.department,
                    'research_area': professor.research_area,
                    'introduction': professor.introduction
                },
                self_introduction=self_introduction,
                additional_requirements=additional_requirements,
                prompt_config=prompt_config,
                format_type='text'  # 指定生成纯文本格式
            )
            
            # 获取发送用户信息（用于邮件主题）
            applicant_name = '申请者'  # 默认值
            if sender_user_id:
                from backend.models.user_profile import UserProfile
                sender_user = UserProfile.query.filter_by(id=sender_user_id, is_active=True).first()
                if sender_user:
                    applicant_name = sender_user.name or sender_user.email.split('@')[0]
            
            # 生成邮件主题
            if custom_subject:
                email_subject = custom_subject
            else:
                # 使用LLM生成默认主题
                email_subject = generate_llm_service.generate_subject(
                    professor_info={
                        'name': professor.name,
                        'university': professor.university,
                        'research_area': professor.research_area
                    },
                    applicant_name=applicant_name
                )
            
            return jsonify({
                'subject': email_subject,
                'content': email_content,
                'professor_name': professor.name,
                'format': 'text'  # 标识返回的是纯文本格式
            })
            
        except Exception as e:
            logger.error(f"生成邮件内容失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/send-email', methods=['POST'])
    def send_email():
        """发送邮件"""
        try:
            data = request.get_json()
            professor_id = data['professor_id']
            subject = data['subject']
            
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
                email_content = data['email_content']
            
            professor = db.session.get(Professor, professor_id)
            if not professor:
                return jsonify({'error': '教授信息不存在'}), 404
            
            # 获取默认用户的邮件配置
            default_user = user_service.get_default_user()
            if not default_user:
                return jsonify({'error': '请先设置默认用户'}), 400
            
            sender_config = {
                'email': default_user.email,
                'password': default_user.email_password,
                'smtp_server': default_user.smtp_server,
                'smtp_port': default_user.smtp_port,
                'name': default_user.name
            }
            
            # 处理附件
            attachment_file_ids = data.get('attachment_file_ids', [])
            attachments = []
            if attachment_file_ids:
                from backend.models.user_file import UserFile
                for file_id in attachment_file_ids:
                    user_file = UserFile.query.filter_by(id=file_id, is_active=True).first()
                    if user_file and os.path.exists(user_file.file_path):
                        attachments.append(user_file.file_path)
            
            # 发送邮件
            # 根据内容来源和格式确定邮件格式
            content_type = 'html'  # 默认使用HTML格式
            
            # 检查是否为AI生成的纯文本格式邮件
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
                professor_id=professor_id,
                subject=subject,
                content=email_content,
                status='sent' if success else 'failed',
                sender_name=default_user.name,
                sender_email=default_user.email,
                sent_at=datetime.now() if success else None
            )
            db.session.add(email_record)
            db.session.commit()
            
            if success:
                return jsonify({'message': '邮件发送成功'})
            else:
                return jsonify({'error': '邮件发送失败'}), 500
                
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/generate-document-email', methods=['POST'])
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
            
            if not sender_id:
                return jsonify({'success': False, 'message': '请选择发送人'}), 400
            
            if not selected_documents:
                return jsonify({'success': False, 'message': '请选择至少一个文档'}), 400
                
            if not selected_professors:
                return jsonify({'success': False, 'message': '请选择至少一个教授'}), 400
            
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
            for prof_id in selected_professors:
                professor = Professor.query.get(prof_id)
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
    
    @app.route('/api/send-batch-emails', methods=['POST'])
    def send_batch_emails():
        """批量发送邮件"""
        try:
            data = request.get_json()
            professor_ids = data['professor_ids']
            self_introduction = data['self_introduction']
            sender_config = data['sender_config']
            llm_config = data.get('llm_config', {})
            
            # 创建LLM服务实例（使用前端配置）
            batch_llm_service = LLMService(
                api_key=llm_config.get('apiKey'),
                api_base=llm_config.get('apiBase'),
                model=llm_config.get('model'),
                provider=llm_config.get('provider', 'openai')
            )
            
            success_count = 0
            failed_count = 0
            failed_emails = []
            
            for professor_id in professor_ids:
                try:
                    # 获取教授信息
                    professor = db.session.get(Professor, professor_id)
                    if not professor:
                        failed_count += 1
                        failed_emails.append({
                            'professor_id': professor_id,
                            'professor_name': f'ID:{professor_id}',
                            'email': 'unknown',
                            'error': '教授信息不存在'
                        })
                        continue
                    
                    # 使用LLM生成个性化邮件内容
                    email_content = batch_llm_service.generate_email(
                        professor_info={
                            'name': professor.name,
                            'university': professor.university,
                            'department': professor.department,
                            'research_area': professor.research_area,
                            'introduction': professor.introduction
                        },
                        self_introduction=self_introduction
                    )
                    
                    if not email_content:
                        failed_count += 1
                        failed_emails.append({
                            'professor_id': professor.id,
                            'professor_name': professor.name,
                            'email': professor.email,
                            'error': '邮件内容生成失败'
                        })
                        continue
                    
                    # 发送邮件
                    subject = f'Academic Collaboration Inquiry - {professor.research_area}'
                    success = email_service.send_email(
                        recipient_email=professor.email,
                        recipient_name=professor.name,
                        subject=subject,
                        content=email_content,
                        sender_config=sender_config
                    )
                    
                    # 记录发送结果
                    email_record = EmailRecord(
                        professor_id=professor.id,
                        subject=subject,
                        content=email_content,
                        status='sent' if success else 'failed',
                        sender_name=sender_config['name'],
                        sender_email=sender_config['email'],
                        sent_at=datetime.now() if success else None
                    )
                    db.session.add(email_record)
                    
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_emails.append({
                            'professor_id': professor.id,
                            'professor_name': professor.name,
                            'email': professor.email,
                            'error': '邮件发送失败'
                        })
                        
                except Exception as e:
                    failed_count += 1
                    professor_name = professor.name if 'professor' in locals() and professor else f'ID:{professor_id}'
                    professor_email = professor.email if 'professor' in locals() and professor else 'unknown'
                    failed_emails.append({
                        'professor_id': professor_id,
                        'professor_name': professor_name,
                        'email': professor_email,
                        'error': str(e)
                    })
                    logger.error(f"批量发送邮件时出错 (教授ID: {professor_id}): {str(e)}")
            
            # 提交数据库更改
            db.session.commit()
            
            return jsonify({
                'success_count': success_count,
                'failed_count': failed_count,
                'failed_emails': failed_emails,
                'message': f'批量发送完成: 成功 {success_count} 封, 失败 {failed_count} 封'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"批量发送邮件时出错: {str(e)}")
            return jsonify({'error': f'批量发送邮件时出错: {str(e)}'}), 500
    
    @app.route('/api/email-records', methods=['GET'])
    def email_records():
        """获取邮件发送记录"""
        records = EmailRecord.query.order_by(EmailRecord.created_at.desc()).all()
        return jsonify([{
            'id': r.id,
            'professor_name': r.professor.name,
            'professor_email': r.professor.email,
            'professor_university': r.professor.university,
            'subject': r.subject,
            'content': r.content,
            'status': r.status,
            'sender_name': r.sender_name,
            'sender_email': r.sender_email,
            'created_at': r.created_at.isoformat(),
            'sent_at': r.sent_at.isoformat() if r.sent_at else None
        } for r in records])
    
    @app.route('/api/email-records/<int:record_id>', methods=['GET'])
    def email_record_detail(record_id):
        """获取单个邮件记录详情"""
        try:
            record = EmailRecord.query.get_or_404(record_id)
            return jsonify({
                'id': record.id,
                'professor_name': record.professor.name,
                'professor_email': record.professor.email,
                'professor_university': record.professor.university,
                'subject': record.subject,
                'content': record.content,
                'status': record.status,
                'sender_name': record.sender_name,
                'sender_email': record.sender_email,
                'recipient_email': record.professor.email,
                'send_time': record.sent_at.isoformat() if record.sent_at else record.created_at.isoformat(),
                'created_at': record.created_at.isoformat(),
                'sent_at': record.sent_at.isoformat() if record.sent_at else None
            })
        except Exception as e:
            logger.error(f"获取邮件记录详情失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # CSV导入相关API
    @app.route('/api/import/template', methods=['GET'])
    def download_csv_template():
        """下载CSV模板"""
        try:
            template_path = import_service.generate_csv_template()
            return send_from_directory(os.path.dirname(template_path), os.path.basename(template_path), as_attachment=True, download_name='professor_template.csv')
        except Exception as e:
            logger.error(f"下载CSV模板失败: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/import/preview', methods=['POST'])
    def preview_csv():
        """预览CSV文件"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': '没有上传文件'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '没有选择文件'}), 400
            
            # 验证文件
            is_valid, message = import_service.validate_csv_file(file)
            if not is_valid:
                return jsonify({'error': message}), 400
            
            # 预览数据
            preview_data = import_service.preview_csv_data(file)
            return jsonify(preview_data)
            
        except Exception as e:
            logger.error(f"预览CSV失败: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/import/professors', methods=['POST'])
    def import_professors():
        """导入教授信息"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': '没有上传文件'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '没有选择文件'}), 400
            
            # 获取导入选项
            skip_duplicates = request.form.get('skip_duplicates', 'true').lower() == 'true'
            
            # 导入数据
            result = import_service.import_professors_from_csv(file, skip_duplicates)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"导入教授信息失败: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/export/professors', methods=['GET'])
    def export_professors():
        """导出教授信息"""
        try:
            # 获取筛选参数
            university = request.args.get('university')
            
            # 查询教授
            query = Professor.query
            if university:
                query = query.filter(Professor.university.like(f'%{university}%'))
            
            professors = query.all()
            
            # 生成CSV内容
            csv_content = import_service.export_professors_to_csv_content(professors)
            
            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'professors_export_{timestamp}.csv'
            
            # 直接返回CSV内容
            from flask import Response
            return Response(
                csv_content,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'text/csv; charset=utf-8'
                }
            )
            
        except Exception as e:
            logger.error(f"导出教授信息失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # 用户管理API
    @app.route('/api/users', methods=['GET', 'POST'])
    def users():
        """用户管理"""
        try:
            if request.method == 'GET':
                users = user_service.get_all_users()
                return jsonify([user.to_dict() for user in users])
            
            elif request.method == 'POST':
                # 验证数据
                data = request.form.to_dict()
                errors = user_service.validate_user_data(data)
                if errors:
                    return jsonify({'errors': errors}), 400
                
                # 获取文件
                cover_letter_file = request.files.get('cover_letter')
                resume_file = request.files.get('resume')
                
                # 获取多文件上传
                files = request.files.getlist('files')
                file_types = request.form.getlist('file_types')
                
                user, error = user_service.create_user(
                    data, cover_letter_file, resume_file, files, file_types
                )
                
                if error:
                    return jsonify({'error': error}), 400
                
                return jsonify({
                    'message': '用户创建成功',
                    'user': user.to_dict()
                })
                
        except Exception as e:
            logger.error(f"用户管理失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
    def user_detail(user_id):
        """用户详情管理"""
        try:
            if request.method == 'GET':
                user = user_service.get_user(user_id)
                if user:
                    return jsonify(user.to_dict())
                else:
                    return jsonify({'error': '用户不存在'}), 404
            
            elif request.method == 'PUT':
                # 验证数据
                data = request.form.to_dict()
                errors = user_service.validate_user_data(data, is_edit=True)  # 编辑模式
                if errors:
                    return jsonify({'errors': errors}), 400
                
                # 获取文件
                cover_letter_file = request.files.get('cover_letter')
                resume_file = request.files.get('resume')
                
                # 获取多文件上传
                files = request.files.getlist('files')
                file_types = request.form.getlist('file_types')
                
                user, error = user_service.update_user(
                    user_id, data, cover_letter_file, resume_file, files, file_types
                )
                
                if error:
                    return jsonify({'error': error}), 400
                
                return jsonify({
                    'message': '用户更新成功',
                    'user': user.to_dict()
                })
            
            elif request.method == 'DELETE':
                success, error = user_service.delete_user(user_id)
                if error:
                    return jsonify({'error': error}), 400
                
                return jsonify({'message': '用户删除成功'})
                
        except Exception as e:
            logger.error(f"用户详情管理失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<int:user_id>/set-default', methods=['POST'])
    def set_default_user(user_id):
        """设置默认用户"""
        try:
            success, error = user_service.set_default_user(user_id)
            if error:
                return jsonify({'error': error}), 400
            
            return jsonify({'message': '默认用户设置成功'})
            
        except Exception as e:
            logger.error(f"设置默认用户失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/default', methods=['GET'])
    def get_default_user():
        """获取默认用户"""
        try:
            user = user_service.get_default_user()
            if user:
                return jsonify(user.to_dict())
            else:
                return jsonify({'message': '未设置默认用户'}), 404
                
        except Exception as e:
            logger.error(f"获取默认用户失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<int:user_id>/documents', methods=['GET'])
    def get_user_documents(user_id):
        """获取用户已上传的文档信息"""
        try:
            from backend.models.user_file import UserFile
            
            user = user_service.get_user(user_id)
            if not user:
                return jsonify({'error': '用户不存在'}), 404
            
            # 获取用户的所有文件
            user_files = UserFile.query.filter_by(user_id=user_id).all()
            
            documents = {
                'cover_letter': None,
                'resume': None,
                'files': []
            }
            
            # 处理新的文件系统
            for file in user_files:
                file_info = {
                    'id': file.id,
                    'filename': file.file_name,
                    'file_type': file.file_type,
                    'file_size': file.file_size,
                    'upload_time': file.created_at.isoformat() if file.created_at else None
                }
                documents['files'].append(file_info)
                
                # 为了兼容旧的前端代码，也设置cover_letter和resume字段
                if file.file_type == 'cover_letter':
                    documents['cover_letter'] = file.file_name
                elif file.file_type == 'resume':
                    documents['resume'] = file.file_name
            
            # 兼容旧的文件系统
            if user.cover_letter_path and os.path.exists(user.cover_letter_path) and not documents['cover_letter']:
                documents['cover_letter'] = os.path.basename(user.cover_letter_path)
            
            if user.resume_path and os.path.exists(user.resume_path) and not documents['resume']:
                documents['resume'] = os.path.basename(user.resume_path)
            
            return jsonify({
                'user_id': user_id,
                'user_name': user.name,
                'documents': documents
            })
            
        except Exception as e:
            logger.error(f"获取用户文档失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<int:user_id>/files', methods=['GET'])
    def get_user_files(user_id):
        """获取用户文件列表"""
        try:
            from backend.models.user_file import UserFile
            
            user = user_service.get_user(user_id)
            if not user:
                return jsonify({'error': '用户不存在'}), 404
            
            files = UserFile.query.filter_by(user_id=user_id).all()
            
            return jsonify([
                {
                    'id': file.id,
                    'filename': file.file_name,  # 修复字段名映射
                    'file_type': file.file_type,
                    'file_size': file.file_size,
                    'upload_time': file.created_at.isoformat() if file.created_at else None  # 修复字段名映射
                }
                for file in files
            ])
            
        except Exception as e:
            logger.error(f"获取用户文件失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<int:user_id>/files/<int:file_id>', methods=['DELETE'])
    def delete_user_file(user_id, file_id):
        """删除用户文件"""
        try:
            from backend.models.user_file import UserFile
            
            user = user_service.get_user(user_id)
            if not user:
                return jsonify({'error': '用户不存在'}), 404
            
            file = UserFile.query.filter_by(id=file_id, user_id=user_id).first()
            if not file:
                return jsonify({'error': '文件不存在'}), 404
            
            # 删除物理文件
            if file.file_path and os.path.exists(file.file_path):
                os.remove(file.file_path)
            
            # 删除数据库记录
            db.session.delete(file)
            db.session.commit()
            
            return jsonify({'message': '文件删除成功'})
            
        except Exception as e:
            logger.error(f"删除用户文件失败: {str(e)}")
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/users/<int:user_id>/files/<int:file_id>/content', methods=['GET'])
    def get_file_content(user_id, file_id):
        """获取文件内容"""
        try:
            # 验证用户是否存在
            user = user_service.get_user(user_id)
            if not user:
                return jsonify({'error': '用户不存在'}), 404
            
            # 验证文件是否属于该用户
            from backend.models.user_file import UserFile
            user_file = UserFile.query.filter_by(id=file_id, user_id=user_id, is_active=True).first()
            if not user_file:
                return jsonify({'error': '文件不存在或不属于该用户'}), 404
            
            output_format = request.args.get('output_format', 'text')  # 支持 'text' 或 'html'
            content, error = document_service.get_file_content(file_id, output_format)
            if error:
                return jsonify({'error': error}), 400
            return jsonify({'content': content, 'format': output_format})
        except Exception as e:
            logger.error(f'获取文件内容失败: {str(e)}')
            return jsonify({'error': '获取文件内容失败'}), 500
    
    @app.route('/api/files/<int:file_id>/preview', methods=['GET'])
    def get_file_preview(file_id):
        """获取文件预览"""
        try:
            from backend.models.user_file import UserFile
            
            # 获取文件信息
            user_file = UserFile.query.get(file_id)
            if not user_file:
                return jsonify({'error': '文件不存在'}), 404
            
            # 获取文件路径
            file_path = user_file.file_path
            if not file_path or not os.path.exists(file_path):
                return jsonify({'error': '文件路径不存在'}), 404
            
            # 获取文件预览内容
            if file_path.lower().endswith('.docx'):
                # 对于docx文件，获取预览文本
                preview_content = document_service.get_document_preview(file_path)
                return jsonify({'content': preview_content, 'type': 'text'})
            elif file_path.lower().endswith(('.txt', '.md')):
                # 对于文本文件，直接读取内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 限制预览长度
                    if len(content) > 1000:
                        content = content[:1000] + '...（更多内容）'
                    return jsonify({'content': content, 'type': 'text'})
            else:
                return jsonify({'error': '不支持预览此文件类型'}), 400
                
        except Exception as e:
            logger.error(f'获取文件预览失败: {str(e)}')
            return jsonify({'error': '获取文件预览失败'}), 500
    
    @app.route('/api/users/<int:user_id>/documents/<doc_type>/convert', methods=['POST'])
    def convert_user_document(user_id, doc_type):
        """转换用户已上传的文档为HTML"""
        try:
            if doc_type not in ['cover_letter', 'resume']:
                return jsonify({'error': '无效的文档类型'}), 400
            
            user = user_service.get_user(user_id)
            if not user:
                return jsonify({'error': '用户不存在'}), 404
            
            # 获取文档路径
            doc_path = user.cover_letter_path if doc_type == 'cover_letter' else user.resume_path
            if not doc_path or not os.path.exists(doc_path):
                return jsonify({'error': f'{doc_type}文档不存在'}), 404
            
            # 只转换docx文件
            if not doc_path.lower().endswith('.docx'):
                return jsonify({'error': '只支持转换.docx格式文档'}), 400
            
            # 转换文档
            result = document_service.docx_to_html(doc_path)
            
            return jsonify({
                'success': True,
                'html_content': result['html_content'],
                'attachments': result['attachments'],
                'original_filename': result['original_filename'],
                'document_type': doc_type
            })
            
        except Exception as e:
            logger.error(f"转换用户文档失败: {str(e)}")
            return jsonify({'error': str(e)}), 500
    

    
    # 文档转换API
    @app.route('/api/convert-document', methods=['POST'])
    def convert_document():
        """转换docx文档为HTML格式"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': '未选择文件'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '未选择文件'}), 400
            
            # 保存上传的文件
            upload_dir = os.path.join(os.getcwd(), 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, file.filename)
            file.save(file_path)
            
            try:
                # 验证文档
                validation = document_service.validate_document(file_path)
                if not validation['valid']:
                    return jsonify({'error': validation['message']}), 400
                
                # 转换文档
                result = document_service.docx_to_html(file_path)
                
                # 获取预览
                preview = document_service.get_document_preview(file_path)
                
                return jsonify({
                    'success': True,
                    'html_content': result['html_content'],
                    'attachments': result['attachments'],
                    'original_filename': result['original_filename'],
                    'preview': preview,
                    'file_info': {
                        'size': validation['file_size'],
                        'format': validation['format']
                    }
                })
                
            finally:
                # 清理临时文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
        except Exception as e:
            return jsonify({'error': f'文档转换失败: {str(e)}'}), 500
    
    @app.route('/api/send-document-email', methods=['POST'])
    def send_document_email():
        """批量发送文档邮件"""
        try:
            data = request.get_json()
            
            # 验证必需参数
            professors = data.get('professors', [])
            documents = data.get('documents', [])
            subject = data.get('subject', '')
            send_interval = data.get('send_interval', 5)
            
            if not professors:
                return jsonify({'error': '请选择至少一个教授'}), 400
            
            if not documents:
                return jsonify({'error': '请选择至少一个文档'}), 400
                
            if not subject:
                return jsonify({'error': '请输入邮件主题'}), 400
            
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
                    
                    # 获取默认发送人信息
                    default_user = user_service.get_default_user()
                    if not default_user:
                        failed_count += 1
                        failed_emails.append({
                            'professor_id': professor_id,
                            'professor_name': professor.name,
                            'email': professor.email,
                            'error': '请先设置默认用户'
                        })
                        continue
                    
                    # 发送邮件
                    sender_config = {
                        'email': default_user.email,
                        'name': default_user.name,
                        'password': default_user.email_password
                    }
                    
                    success = email_service.send_email(
                        recipient_email=professor.email,
                        recipient_name=professor.name,
                        subject=personalized_subject,
                        content=personalized_content,
                        sender_config=sender_config,
                        content_type='html'
                    )
                    
                    # 记录发送结果
                    email_record = EmailRecord(
                        professor_id=professor_id,
                        subject=personalized_subject,
                        content=personalized_content,
                        status='sent' if success else 'failed',
                        sender_name=default_user.name,
                        sender_email=default_user.email,
                        sent_at=datetime.now() if success else None
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
                        import time
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
    
    @app.route('/api/test-llm-config', methods=['POST'])
    def test_llm_config():
        """测试LLM配置"""
        try:
            data = request.get_json()
            api_key = data.get('apiKey')
            api_base = data.get('apiBase')
            model = data.get('model')
            provider = data.get('provider', 'openai')
            
            if not api_key:
                return jsonify({'error': 'API Key不能为空'}), 400
            
            # 创建临时LLM服务实例进行测试
            test_llm_service = LLMService(
                api_key=api_key,
                api_base=api_base,
                model=model,
                provider=provider
            )
            
            # 测试连接
            success = test_llm_service.check_api_status()
            
            if success:
                return jsonify({'message': 'LLM配置测试成功'})
            else:
                return jsonify({'error': 'LLM配置测试失败'}), 400
                
        except Exception as e:
            logger.error(f"LLM配置测试失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/optimize-email', methods=['POST'])
    def optimize_email():
        """优化邮件内容"""
        try:
            data = request.get_json()
            original_content = data.get('original_content')
            optimization_request = data.get('optimization_request')
            llm_config = data.get('llm_config', {})
            
            if not original_content or not optimization_request:
                return jsonify({'error': '原始内容和优化要求不能为空'}), 400
            
            # 创建LLM服务实例（使用前端配置）
            optimize_llm_service = LLMService(
                api_key=llm_config.get('apiKey'),
                api_base=llm_config.get('apiBase'),
                model=llm_config.get('model'),
                provider=llm_config.get('provider', 'openai')
            )
            
            # 优化邮件内容
            optimized_content = optimize_llm_service.optimize_email_content(
                original_content=original_content,
                optimization_request=optimization_request
            )
            
            return jsonify({
                'optimized_content': optimized_content
            })
            
        except Exception as e:
            logger.error(f"优化邮件内容失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    # 设置相关API
    @app.route('/api/settings/upload', methods=['GET'])
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
    
    @app.route('/api/settings/log', methods=['GET'])
    def get_log_settings():
        """获取日志设置"""
        try:
            return jsonify({
                'success': True,
                'data': {
                    'log_level': 'INFO',
                    'log_file': 'app.log',
                    'console_output': True
                }
            })
        except Exception as e:
            logger.error(f"获取日志设置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/settings/database', methods=['GET'])
    def get_database_settings():
        """获取数据库信息"""
        try:
            # 检查数据库连接状态
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                db_status = '已连接'
            except Exception:
                db_status = '连接失败'
            
            # 从配置中获取实际的数据库文件名
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
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

    # LLM配置管理API
    @app.route('/api/llm-configs', methods=['GET'])
    def get_llm_configs():
        """获取所有LLM配置"""
        try:
            from backend.database import LLMConfig
            configs = LLMConfig.query.order_by(LLMConfig.created_at.desc()).all()
            return jsonify({
                'configs': [config.to_dict() for config in configs]
            })
        except Exception as e:
            logger.error(f"获取LLM配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-configs/<int:config_id>', methods=['GET'])
    def get_llm_config(config_id):
        """获取单个LLM配置"""
        try:
            from backend.database import LLMConfig
            config = LLMConfig.query.get_or_404(config_id)
            return jsonify({
                'success': True,
                'config': config.to_dict(include_api_key=True)
            })
        except Exception as e:
            logger.error(f"获取LLM配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-configs/<int:config_id>', methods=['DELETE'])
    def delete_llm_config(config_id):
        """删除LLM配置"""
        try:
            from backend.database import LLMConfig
            config = LLMConfig.query.get_or_404(config_id)
            
            db.session.delete(config)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '配置删除成功'
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除LLM配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-configs', methods=['POST'])
    def save_llm_config():
        """保存LLM配置"""
        try:
            from backend.database import LLMConfig
            from backend.config import Config
            
            data = request.get_json()
            name = data.get('name')
            provider = data.get('provider')
            api_key = data.get('api_key')
            api_base = data.get('base_url')
            model = data.get('model')
            is_default = data.get('is_default', False)
            
            if not name or not provider or not api_key or not model:
                return jsonify({'error': '配置名称、提供商、API密钥和模型不能为空'}), 400
            
            # 检查配置名称是否已存在
            existing_config = LLMConfig.query.filter_by(name=name).first()
            if existing_config:
                return jsonify({'error': '配置名称已存在'}), 400
            
            # 如果设置为默认配置，取消其他默认配置
            if is_default:
                LLMConfig.query.filter_by(is_default=True).update({'is_default': False})
            
            # 加密API密钥
            encrypted_api_key = Config.encrypt_api_key(api_key)
            
            # 创建新配置
            new_config = LLMConfig(
                name=name,
                provider=provider,
                api_key_encrypted=encrypted_api_key,
                api_base=api_base,
                model=model,
                is_default=is_default
            )
            
            db.session.add(new_config)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '配置保存成功',
                'config': new_config.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存LLM配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-configs/<int:config_id>/use', methods=['POST'])
    def use_llm_config(config_id):
        """使用指定的LLM配置"""
        try:
            from backend.database import LLMConfig
            
            config = LLMConfig.query.get_or_404(config_id)
            config_dict = config.to_dict(include_api_key=True)
            
            return jsonify({
                'message': '配置加载成功',
                'config': config_dict
            })
            
        except Exception as e:
            logger.error(f"加载LLM配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-configs/<int:config_id>/set-default', methods=['POST'])
    def set_default_llm_config(config_id):
        """设置默认LLM配置"""
        try:
            from backend.database import LLMConfig
            
            # 取消所有默认配置
            LLMConfig.query.filter_by(is_default=True).update({'is_default': False})
            
            # 设置新的默认配置
            config = LLMConfig.query.get_or_404(config_id)
            config.is_default = True
            
            db.session.commit()
            
            return jsonify({'message': '默认配置设置成功'})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"设置默认LLM配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-configs/default', methods=['GET'])
    def get_default_llm_config():
        """获取默认LLM配置"""
        try:
            from backend.database import LLMConfig
            
            config = LLMConfig.query.filter_by(is_default=True).first()
            if config:
                return jsonify({
                    'success': True,
                    'config': config.to_dict(include_api_key=True)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '未找到默认配置'
                })
                
        except Exception as e:
            logger.error(f"获取默认LLM配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    # LLM提示词配置API
    @app.route('/api/llm-prompt-configs', methods=['GET'])
    def get_llm_prompt_configs():
        """获取所有LLM提示词配置"""
        try:
            from backend.database import LLMPromptConfig
            
            configs = LLMPromptConfig.query.all()
            return jsonify({
                'success': True,
                'configs': [config.to_dict() for config in configs]
            })
            
        except Exception as e:
            logger.error(f"获取LLM提示词配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-prompt-configs', methods=['POST'])
    def save_llm_prompt_config():
        """保存LLM提示词配置"""
        try:
            from backend.database import LLMPromptConfig
            
            data = request.get_json()
            name = data.get('name')
            system_prompt = data.get('system_prompt')
            user_prompt_template = data.get('user_prompt_template')
            is_default = data.get('is_default', False)
            
            if not name or not system_prompt or not user_prompt_template:
                return jsonify({'error': '请填写完整的提示词配置信息'}), 400
            
            # 如果设置为默认，取消其他默认配置
            if is_default:
                LLMPromptConfig.query.filter_by(is_default=True).update({'is_default': False})
            
            # 创建新配置
            new_config = LLMPromptConfig(
                name=name,
                system_prompt=system_prompt,
                user_prompt_template=user_prompt_template,
                is_default=is_default
            )
            
            db.session.add(new_config)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '提示词配置保存成功',
                'config': new_config.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存LLM提示词配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-prompt-configs/<int:config_id>', methods=['GET'])
    def get_llm_prompt_config(config_id):
        """获取指定的LLM提示词配置"""
        try:
            from backend.database import LLMPromptConfig
            
            config = LLMPromptConfig.query.get_or_404(config_id)
            return jsonify({
                'success': True,
                'config': config.to_dict()
            })
            
        except Exception as e:
            logger.error(f"获取LLM提示词配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-prompt-configs/<int:config_id>', methods=['DELETE'])
    def delete_llm_prompt_config(config_id):
        """删除LLM提示词配置"""
        try:
            from backend.database import LLMPromptConfig
            
            config = LLMPromptConfig.query.get_or_404(config_id)
            db.session.delete(config)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '提示词配置删除成功'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除LLM提示词配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/llm-prompt-configs/default', methods=['GET'])
    def get_default_llm_prompt_config():
        """获取默认LLM提示词配置"""
        try:
            from backend.database import LLMPromptConfig
            
            config = LLMPromptConfig.query.filter_by(is_default=True).first()
            if config:
                return jsonify({
                    'success': True,
                    'config': config.to_dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '未找到默认提示词配置'
                })
                
        except Exception as e:
            logger.error(f"获取默认LLM提示词配置失败: {e}")
            return jsonify({'error': str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)