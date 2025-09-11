import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from backend.database import db
from backend.models.user_profile import UserProfile
from backend.models.user_file import UserFile
from backend.utils.timezone_utils import get_shanghai_utcnow
import logging

logger = logging.getLogger(__name__)

class UserService:
    """用户管理服务"""
    
    def __init__(self):
        self.upload_folder = 'uploads/users'
        self.allowed_extensions = {
            'cover_letter': ['.docx', '.doc'],
            'resume': ['.pdf', '.docx', '.doc'],
            'transcript': ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.doc'],
            'other': ['.pdf', '.docx', '.doc', '.txt', '.jpg', '.jpeg', '.png']
        }
        
        # 确保上传目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def allowed_file(self, filename, file_type):
        """检查文件类型是否允许"""
        if '.' not in filename:
            return False
        
        ext = '.' + filename.rsplit('.', 1)[1].lower()
        return ext in self.allowed_extensions.get(file_type, [])
    
    def save_file(self, file, user_id, file_type):
        """保存用户文件"""
        try:
            if not file or not self.allowed_file(file.filename, file_type):
                return None, f'不支持的文件类型，仅支持 {self.allowed_extensions.get(file_type, [])}'
            
            # 创建用户专属目录
            user_folder = os.path.join(self.upload_folder, str(user_id))
            os.makedirs(user_folder, exist_ok=True)
            
            # 生成安全的文件名
            original_filename = file.filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 获取原始文件的扩展名
            _, ext = os.path.splitext(original_filename)
            
            # 使用secure_filename处理文件名，但如果结果为空，则使用file_type作为基础名
            secure_name = secure_filename(original_filename)
            if not secure_name or not secure_name.strip():
                # 如果secure_filename返回空字符串（通常是因为中文字符被移除），使用file_type
                new_filename = f'{file_type}_{timestamp}{ext}'
            else:
                # 如果secure_filename有效，使用处理后的名称
                name, _ = os.path.splitext(secure_name)
                new_filename = f'{file_type}_{timestamp}{ext}'
            
            file_path = os.path.join(user_folder, new_filename)
            file.save(file_path)
            
            return file_path, None
            
        except Exception as e:
            logger.error(f'保存文件失败: {str(e)}')
            return None, f'保存文件失败: {str(e)}'
    
    def save_multiple_files(self, files, file_types, user_id):
        """保存多个文件并创建UserFile记录"""
        saved_files = []
        try:
            for file, file_type in zip(files, file_types):
                if file and file.filename:
                    # 保存文件
                    file_path, error = self.save_file(file, user_id, file_type)
                    if error:
                        # 如果有错误，清理已保存的文件
                        for saved_file in saved_files:
                            self.delete_file(saved_file['file_path'])
                        return [], error
                    
                    # 获取文件大小
                    file.seek(0, 2)  # 移动到文件末尾
                    file_size = file.tell()
                    file.seek(0)  # 重置文件指针
                    
                    # 创建UserFile记录
                    file_extension = os.path.splitext(file.filename)[1].lower()
                    user_file = UserFile(
                        user_id=user_id,
                        file_name=file.filename,
                        file_path=file_path,
                        file_type=file_type,
                        file_extension=file_extension,
                        file_size=file_size
                    )
                    
                    db.session.add(user_file)
                    saved_files.append({
                        'file_path': file_path,
                        'user_file': user_file
                    })
            
            return saved_files, None
            
        except Exception as e:
            # 清理已保存的文件
            for saved_file in saved_files:
                self.delete_file(saved_file['file_path'])
            logger.error(f'保存多个文件失败: {str(e)}')
            return [], f'保存文件失败: {str(e)}'
    
    def delete_file(self, file_path):
        """删除文件"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            logger.error(f'删除文件失败: {str(e)}')
        return False
    
    def create_user(self, data, cover_letter_file=None, resume_file=None, files=None, file_types=None):
        """创建用户"""
        try:
            # 检查邮箱是否已存在
            existing_user = UserProfile.query.filter_by(email=data['email']).first()
            if existing_user:
                return None, '该邮箱已被使用'
            
            # 创建用户
            user = UserProfile(
                name=data['name'],
                email=data['email'],
                email_password=data['email_password'],
                smtp_server=data.get('smtp_server'),
                smtp_port=data.get('smtp_port'),
                description=data.get('description')
            )
            
            db.session.add(user)
            db.session.flush()  # 获取用户ID
            
            # 保存文件（兼容旧版本）
            if cover_letter_file:
                file_path, error = self.save_file(cover_letter_file, user.id, 'cover_letter')
                if error:
                    db.session.rollback()
                    return None, error
                user.cover_letter_path = file_path
            
            if resume_file:
                file_path, error = self.save_file(resume_file, user.id, 'resume')
                if error:
                    db.session.rollback()
                    return None, error
                user.resume_path = file_path
            
            # 保存多个文件
            if files and file_types:
                saved_files, error = self.save_multiple_files(files, file_types, user.id)
                if error:
                    db.session.rollback()
                    return None, error
            
            # 如果是第一个用户，设为默认用户
            if UserProfile.query.count() == 1:
                user.is_default = True
            
            db.session.commit()
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'创建用户失败: {str(e)}')
            return None, f'创建用户失败: {str(e)}'
    
    def update_user(self, user_id, data, cover_letter_file=None, resume_file=None, files=None, file_types=None):
        """更新用户信息"""
        try:
            user = db.session.get(UserProfile, user_id)
            if not user:
                return None, '用户不存在'
            
            # 检查邮箱是否被其他用户使用
            if data.get('email') and data['email'] != user.email:
                existing_user = UserProfile.query.filter_by(email=data['email']).first()
                if existing_user:
                    return None, '该邮箱已被其他用户使用'
            
            # 更新基本信息
            for field in ['name', 'email', 'email_password', 'smtp_server', 'smtp_port', 'description']:
                if field in data:
                    # 如果是邮箱授权码且为空，则不更新
                    if field == 'email_password' and not data[field]:
                        continue
                    setattr(user, field, data[field])
            
            # 更新文件（兼容旧版本）
            if cover_letter_file:
                # 删除旧文件
                if user.cover_letter_path:
                    self.delete_file(user.cover_letter_path)
                
                # 保存新文件
                file_path, error = self.save_file(cover_letter_file, user.id, 'cover_letter')
                if error:
                    return None, error
                user.cover_letter_path = file_path
            
            if resume_file:
                # 删除旧文件
                if user.resume_path:
                    self.delete_file(user.resume_path)
                
                # 保存新文件
                file_path, error = self.save_file(resume_file, user.id, 'resume')
                if error:
                    return None, error
                user.resume_path = file_path
            
            # 保存多个新文件
            if files and file_types:
                saved_files, error = self.save_multiple_files(files, file_types, user.id)
                if error:
                    return None, error
            
            user.updated_at = get_shanghai_utcnow()
            db.session.commit()
            return user, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'更新用户失败: {str(e)}')
            return None, f'更新用户失败: {str(e)}'
    
    def delete_user(self, user_id):
        """删除用户"""
        try:
            user = db.session.get(UserProfile, user_id)
            if not user:
                return False, '用户不存在'
            
            # 如果是默认用户，需要先设置其他用户为默认
            if user.is_default:
                other_user = UserProfile.query.filter(
                    UserProfile.id != user_id,
                    UserProfile.is_active == True
                ).first()
                if other_user:
                    other_user.is_default = True
            
            # 删除用户文件
            if user.cover_letter_path:
                self.delete_file(user.cover_letter_path)
            if user.resume_path:
                self.delete_file(user.resume_path)
            
            # 删除用户目录
            user_folder = os.path.join(self.upload_folder, str(user_id))
            if os.path.exists(user_folder):
                shutil.rmtree(user_folder)
            
            db.session.delete(user)
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'删除用户失败: {str(e)}')
            return False, f'删除用户失败: {str(e)}'
    
    def get_user(self, user_id):
        """获取用户信息"""
        return db.session.get(UserProfile, user_id)
    
    def get_all_users(self):
        """获取所有用户"""
        return UserProfile.query.filter_by(is_active=True).order_by(UserProfile.created_at.desc()).all()
    
    def set_default_user(self, user_id):
        """设置默认用户"""
        try:
            # 清除所有默认标记
            UserProfile.query.update({'is_default': False})
            
            # 设置新的默认用户
            user = db.session.get(UserProfile, user_id)
            if not user:
                return False, '用户不存在'
            
            user.is_default = True
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'设置默认用户失败: {str(e)}')
            return False, f'设置默认用户失败: {str(e)}'
    
    def get_default_user(self):
        """获取默认用户"""
        return UserProfile.query.filter_by(is_default=True, is_active=True).first()
    
    def get_user_files(self, user_id):
        """获取用户文件列表"""
        try:
            user_files = UserFile.query.filter_by(user_id=user_id, is_active=True).order_by(UserFile.created_at.desc()).all()
            return user_files, None
        except Exception as e:
            logger.error(f'获取用户文件失败: {str(e)}')
            return [], f'获取用户文件失败: {str(e)}'
    
    def delete_user_file(self, file_id, user_id):
        """删除用户文件"""
        try:
            user_file = UserFile.query.filter_by(id=file_id, user_id=user_id, is_active=True).first()
            if not user_file:
                return False, '文件不存在'
            
            # 删除物理文件
            if os.path.exists(user_file.file_path):
                os.remove(user_file.file_path)
            
            # 标记为删除
            user_file.is_active = False
            user_file.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True, None
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'删除用户文件失败: {str(e)}')
            return False, f'删除用户文件失败: {str(e)}'
    
    def validate_user_data(self, data, is_edit=False):
        """验证用户数据"""
        errors = []
        
        if not data.get('name'):
            errors.append('姓名不能为空')
        
        if not data.get('email'):
            errors.append('邮箱不能为空')
        elif '@' not in data['email']:
            errors.append('邮箱格式不正确')
        
        # 编辑模式下允许邮箱授权码为空（保持原密码不变）
        if not is_edit and not data.get('email_password'):
            errors.append('邮箱授权码不能为空')
        
        if data.get('smtp_port'):
            try:
                port = int(data['smtp_port'])
                if port < 1 or port > 65535:
                    errors.append('SMTP端口必须在1-65535之间')
            except ValueError:
                errors.append('SMTP端口必须是数字')
        
        return errors