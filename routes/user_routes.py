from flask import Blueprint, request, jsonify
from backend.user_service import UserService
from backend.models.user_file import UserFile
import logging
import os

logger = logging.getLogger(__name__)

# 创建用户管理蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api')

# 初始化服务
user_service = UserService()


@user_bp.route('/users', methods=['GET', 'POST'])
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


@user_bp.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
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


@user_bp.route('/users/<int:user_id>/documents', methods=['GET'])
def get_user_documents(user_id):
    """获取用户已上传的文档信息"""
    try:
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


@user_bp.route('/users/<int:user_id>/files', methods=['GET'])
def get_user_files(user_id):
    """获取用户文件列表"""
    try:
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


@user_bp.route('/users/<int:user_id>/files/<int:file_id>', methods=['DELETE'])
def delete_user_file(user_id, file_id):
    """删除用户文件"""
    try:
        from backend.database import db
        
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
        from backend.database import db
        db.session.rollback()
        return jsonify({'error': str(e)}), 500