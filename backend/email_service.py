import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from datetime import datetime
from typing import List, Dict, Optional
import base64

logger = logging.getLogger(__name__)

class EmailService:
    """邮件发送服务类"""
    
    def __init__(self):
        self.smtp_servers = {
            '163.com': {'server': 'smtp.163.com', 'port': 465},
            'qq.com': {'server': 'smtp.qq.com', 'port': 587},
            'gmail.com': {'server': 'smtp.gmail.com', 'port': 587},
            'outlook.com': {'server': 'smtp-mail.outlook.com', 'port': 587},
            'sina.com': {'server': 'smtp.sina.com', 'port': 25}
        }

    def get_smtp_config(self, email: str) -> Dict[str, any]:
        """根据邮箱地址获取SMTP配置"""
        domain = email.split('@')[1].lower()
        return self.smtp_servers.get(domain, {
            'server': 'smtp.' + domain,
            'port': 587
        })
    
    def send_email(self, 
                   recipient_email: str,
                   recipient_name: str,
                   subject: str,
                   content: str,
                   sender_config: Dict[str, str],
                   attachments: Optional[List[str]] = None,
                   attachment_data: Optional[List[Dict[str, any]]] = None,
                   content_type: str = 'html') -> bool:
        """
        发送邮件
        
        Args:
            recipient_email: 收件人邮箱
            recipient_name: 收件人姓名
            subject: 邮件主题
            content: 邮件内容
            sender_config: 发件人配置 {'email': '', 'name': '', 'password': ''}
            attachments: 附件文件路径列表
            attachment_data: 附件数据列表，格式为 [{'filename': '', 'content': 'base64', 'content_type': ''}]
            content_type: 内容类型 'html' 或 'plain'
            
        Returns:
            bool: 发送是否成功
        """
        try:
            # 计算SMTP配置，优先使用用户在sender_config中配置的服务器与端口
            default_cfg = self.get_smtp_config(sender_config['email'])
            smtp_server = (sender_config.get('smtp_server') or default_cfg['server']).strip()
            smtp_port = int(sender_config.get('smtp_port') or default_cfg['port'])
            use_ssl = bool(sender_config.get('use_ssl')) or smtp_port == 465
            use_starttls = bool(sender_config.get('use_starttls')) or (smtp_port == 587 and not use_ssl)

            logger.info(
                f"准备发送邮件: to={recipient_name} <{recipient_email}>, "
                f"server={smtp_server}, port={smtp_port}, "
                f"security={'SSL' if use_ssl else ('STARTTLS' if use_starttls else 'PLAIN')}"
            )
            
            # 创建邮件对象
            message = MIMEMultipart()
            
            # 设置发件人信息
            sender_name = sender_config.get('name', sender_config['email'])
            message['From'] = f"{Header(sender_name, 'utf-8').encode()} <{sender_config['email']}>"
            message['To'] = f"{Header(recipient_name, 'utf-8').encode()} <{recipient_email}>"
            message['Subject'] = Header(subject, 'utf-8')
            
            # 添加邮件内容
            content_part = MIMEText(content, content_type, 'utf-8')
            message.attach(content_part)
            
            # 添加文件路径附件
            if attachments:
                for attachment in attachments:
                    if isinstance(attachment, str):
                        # 兼容旧格式：直接传递文件路径
                        if os.path.isfile(attachment):
                            self._add_attachment(message, attachment)
                        else:
                            logger.warning(f"附件文件不存在: {attachment}")
                    elif isinstance(attachment, dict):
                        # 新格式：包含file_path和display_name的字典
                        file_path = attachment.get('file_path')
                        display_name = attachment.get('display_name')
                        if file_path and os.path.isfile(file_path):
                            self._add_attachment(message, file_path, display_name)
                        else:
                            logger.warning(f"附件文件不存在: {file_path}")
            
            # 添加base64编码的附件数据
            if attachment_data:
                for attachment in attachment_data:
                    self._add_attachment_from_data(message, attachment)
            
            # 发送邮件：根据端口/配置自动选择SSL或STARTTLS
            if use_ssl:
                with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30) as smtp_obj:
                    smtp_obj.login(sender_config['email'], sender_config['password'])
                    smtp_obj.sendmail(
                        sender_config['email'], 
                        recipient_email, 
                        message.as_string()
                    )
            else:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as smtp_obj:
                    if use_starttls:
                        smtp_obj.starttls()
                    smtp_obj.login(sender_config['email'], sender_config['password'])
                    smtp_obj.sendmail(
                        sender_config['email'], 
                        recipient_email, 
                        message.as_string()
                    )
            
            logger.info(f"邮件发送成功: {recipient_name} <{recipient_email}>")
            return True
            
        except Exception as e:
            logger.error(
                f"邮件发送失败: {recipient_name} <{recipient_email}> - {e!r}"
            )
            return False

    def _add_attachment(self, message: MIMEMultipart, file_path: str, display_name: Optional[str] = None):
        """添加附件到邮件"""
        try:
            # 读取文件内容
            with open(file_path, 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
            
            # 编码附件
            encoders.encode_base64(part)
            
            # 获取文件名
            filename = display_name or os.path.basename(file_path)
            
            # 设置附件头信息
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {Header(filename, "utf-8").encode()}'
            )
            
            message.attach(part)
            logger.info(f"成功添加附件: {filename}")
            
        except Exception as e:
            logger.error(f"添加附件失败: {file_path} - {str(e)}")

    def _add_attachment_from_data(self, message: MIMEMultipart, attachment_info: Dict[str, any]):
        """从base64数据添加附件到邮件"""
        try:
            # 解码base64数据
            file_data = base64.b64decode(attachment_info['content'])
            
            # 创建附件对象
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file_data)
            
            # 编码附件
            encoders.encode_base64(part)
            
            # 设置附件头信息
            filename = attachment_info['filename']
            content_type = attachment_info.get('content_type', 'application/octet-stream')
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {Header(filename, "utf-8").encode()}'
            )
            
            # 设置内容类型
            if content_type:
                part.replace_header('Content-Type', content_type)
            
            message.attach(part)
            logger.info(f"成功添加附件: {filename}")
            
        except Exception as e:
            logger.error(f"添加base64附件失败: {attachment_info.get('filename', 'unknown')} - {str(e)}")

    def send_batch_emails(self, 
                         email_list: List[Dict],
                         sender_config: Dict[str, str],
                         interval_seconds: int = 1) -> Dict[str, int]:
        """
        批量发送邮件
        
        Args:
            email_list: 邮件列表，每个元素包含收件人信息和邮件内容
            sender_config: 发件人配置
            interval_seconds: 发送间隔（秒）
            
        Returns:
            Dict: 发送统计 {'success': 成功数量, 'failed': 失败数量}
        """
        import time
        
        stats = {'success': 0, 'failed': 0}
        
        for i, email_info in enumerate(email_list):
            try:
                success = self.send_email(
                    recipient_email=email_info['recipient_email'],
                    recipient_name=email_info['recipient_name'],
                    subject=email_info['subject'],
                    content=email_info['content'],
                    sender_config=sender_config,
                    attachments=email_info.get('attachments'),
                    content_type=email_info.get('content_type', 'html')
                )
                
                if success:
                    stats['success'] += 1
                else:
                    stats['failed'] += 1
                
                # 如果不是最后一封邮件，等待指定间隔
                if i < len(email_list) - 1:
                    time.sleep(interval_seconds)
                    
            except Exception as e:
                logger.error(f"批量发送邮件出错: {str(e)}")
                stats['failed'] += 1
        
        logger.info(f"批量邮件发送完成: 成功 {stats['success']} 封，失败 {stats['failed']} 封")
        return stats

    def validate_email_config(self, sender_config: Dict[str, str]) -> bool:
        """
        验证邮件配置是否有效
        
        Args:
            sender_config: 发件人配置
            
        Returns:
            bool: 配置是否有效
        """
        try:
            required_fields = ['email', 'password']
            for field in required_fields:
                if not sender_config.get(field):
                    logger.error(f"邮件配置缺少必要字段: {field}")
                    return False
            
            # 计算SMTP配置（优先使用用户自定义）
            default_cfg = self.get_smtp_config(sender_config['email'])
            smtp_server = (sender_config.get('smtp_server') or default_cfg['server']).strip()
            smtp_port = int(sender_config.get('smtp_port') or default_cfg['port'])
            use_ssl = bool(sender_config.get('use_ssl')) or smtp_port == 465
            use_starttls = bool(sender_config.get('use_starttls')) or (smtp_port == 587 and not use_ssl)

            logger.info(
                f"验证邮件配置: server={smtp_server}, port={smtp_port}, "
                f"security={'SSL' if use_ssl else ('STARTTLS' if use_starttls else 'PLAIN')}"
            )
            
            if use_ssl:
                with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as smtp_obj:
                    smtp_obj.login(sender_config['email'], sender_config['password'])
            else:
                with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as smtp_obj:
                    if use_starttls:
                        smtp_obj.starttls()
                    smtp_obj.login(sender_config['email'], sender_config['password'])
            
            logger.info(f"邮件配置验证成功: {sender_config['email']}")
            return True
            
        except Exception as e:
            logger.error(f"邮件配置验证失败: {e!r}")
            return False

    def create_html_content(self, template_content: str, replacements: Dict[str, str]) -> str:
        """
        根据模板和替换内容生成HTML邮件内容
        
        Args:
            template_content: 模板内容
            replacements: 替换字典
            
        Returns:
            str: 生成的HTML内容
        """
        html_content = template_content
        
        # 执行替换
        for placeholder, replacement in replacements.items():
            html_content = html_content.replace(placeholder, replacement)
        
        return html_content