from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import logging

# 导入自定义模块
from backend.email_service import EmailService
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
            # 获取分页参数
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            search = request.args.get('search', '', type=str)
            university = request.args.get('university', '', type=str)
            department = request.args.get('department', '', type=str)
            
            # 限制每页最大数量
            per_page = min(per_page, 100)
            
            # 构建查询
            query = Professor.query
            
            # 添加搜索条件
            if search:
                query = query.filter(
                    Professor.name.contains(search) |
                    Professor.email.contains(search)
                )
            
            if university:
                query = query.filter(Professor.university == university)
                
            if department:
                query = query.filter(Professor.department == department)
            
            # 执行分页查询
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            professors = pagination.items
            
            return jsonify({
                'professors': [{
                    'id': p.id,
                    'name': p.name,
                    'email': p.email,
                    'university': p.university,
                    'department': p.department,
                    'research_area': p.research_area,
                    'introduction': p.introduction,
                    'created_at': p.created_at.isoformat()
                } for p in professors],
                'pagination': {
                    'page': pagination.page,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next,
                    'prev_num': pagination.prev_num,
                    'next_num': pagination.next_num
                }
            })
        
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
    
    @app.route('/api/professors/all', methods=['GET'])
    def professors_all():
        """获取所有教授信息（不分页）"""
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
    
    # AI生成邮件功能已移除，仅保留文档邮件发送功能
    
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
                        # 生成显示名称
                        display_name = user_file.file_name
                        if user_file.file_type == 'resume':
                            # 简历类型自动重命名为"简历-姓名"的格式
                            name_part = os.path.splitext(user_file.file_name)[0]
                            ext_part = os.path.splitext(user_file.file_name)[1]
                            display_name = f"简历-{default_user.name}{ext_part}"
                        
                        attachments.append({
                            'file_path': user_file.file_path,
                            'display_name': display_name
                        })
            
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
                        professor = Professor.query.get(prof_id)
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
    
    # 批量发送邮件API已移除（AI功能已删除）
    
    @app.route('/api/email-records', methods=['GET'])
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
                    from datetime import timedelta
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
                    'created_at': r.created_at.isoformat(),
                    'sent_at': r.sent_at.isoformat() if r.sent_at else None
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
    
    @app.route('/api/email-records/all', methods=['GET'])
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
                'created_at': r.created_at.isoformat(),
                'sent_at': r.sent_at.isoformat() if r.sent_at else None
            } for r in records])
        except Exception as e:
            logger.error(f"获取所有邮件记录失败: {e}")
            return jsonify({'error': str(e)}), 500
    
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
                'professor_department': record.professor.department,
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
            
            # 验证文件（预览阶段允许无数据行，但必须包含必需表头）
            is_valid, message = import_service.validate_csv_file(file, allow_empty=True)
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
            attachment_ids = data.get('attachments', [])
            
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
                    
                    # 处理附件
                    attachments = []
                    if attachment_ids:
                        from backend.models.user_file import UserFile
                        for file_id in attachment_ids:
                            user_file = UserFile.query.filter_by(id=file_id, is_active=True).first()
                            if user_file and os.path.exists(user_file.file_path):
                                # 生成显示名称
                                display_name = user_file.file_name
                                if user_file.file_type == 'resume':
                                    # 简历类型自动重命名为"简历-姓名"的格式
                                    name_part = os.path.splitext(user_file.file_name)[0]
                                    ext_part = os.path.splitext(user_file.file_name)[1]
                                    display_name = f"简历-{default_user.name}{ext_part}"
                                
                                attachments.append({
                                    'file_path': user_file.file_path,
                                    'display_name': display_name
                                })
                    
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
                        content_type='html',
                        attachments=attachments
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
    
    # LLM配置测试功能已移除
    
    # 邮件优化功能已移除
    
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

    # LLM配置管理API已移除
    
    # LLM提示词配置API已移除
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)