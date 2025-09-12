from flask import Blueprint, request, jsonify
from backend.document_service import DocumentService
from backend.user_service import UserService
from backend.models.user_file import UserFile
import logging
import os

logger = logging.getLogger(__name__)

# 创建文件管理蓝图
file_bp = Blueprint('file', __name__, url_prefix='/api')

# 初始化服务
document_service = DocumentService()
user_service = UserService()


@file_bp.route('/users/<int:user_id>/files/<int:file_id>/content', methods=['GET'])
def get_file_content(user_id, file_id):
    """获取文件内容"""
    try:
        # 验证用户是否存在
        user = user_service.get_user(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        # 验证文件是否属于该用户
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


@file_bp.route('/files/<int:file_id>/preview', methods=['GET'])
def get_file_preview(file_id):
    """获取文件预览"""
    try:
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


@file_bp.route('/users/<int:user_id>/documents/<doc_type>/convert', methods=['POST'])
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


@file_bp.route('/convert-document', methods=['POST'])
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