from openai import OpenAI
import logging
from typing import Dict, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    """LLM服务类，用于生成个性化套磁信内容"""
    
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None, model: Optional[str] = None, provider: Optional[str] = None):
        """
        初始化LLM服务
        
        Args:
            api_key: API密钥
            api_base: API基础URL
            model: 使用的模型名称（火山方舟可以是推理接入点ID或模型名称）
            provider: API提供商 (openai, volcengine, custom)
        """
        from backend.config import Config
        
        self.provider = provider or 'openai'
        self.api_key = api_key or Config.LLM_API_KEY
        self.api_base = api_base or Config.LLM_API_BASE
        self.model = model or Config.LLM_MODEL
        
        # 根据提供商配置客户端
        if self.provider == 'volcengine':
            self._setup_volcengine_client()
        else:
            self._setup_openai_client()
    
    def _setup_openai_client(self):
        """配置OpenAI客户端"""
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
    
    def _setup_volcengine_client(self):
        """配置火山方舟客户端"""
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
    
    def generate_email(self,
                       professor_info: Dict[str, str],
                       self_introduction: str,
                       template_content: Optional[str] = None,
                       additional_requirements: Optional[str] = None,
                       prompt_config: Optional[Dict] = None,
                       format_type: str = 'html') -> str:
        """
        生成个性化套磁信内容
        
        Args:
            professor_info: 教授信息字典
            self_introduction: 自我介绍
            email_template: 邮件模板（可选）
            additional_requirements: 额外要求（可选）
            
        Returns:
            str: 生成的邮件内容
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(
                professor_info=professor_info,
                self_introduction=self_introduction,
                template_content=template_content,
                additional_requirements=additional_requirements,
                prompt_config=prompt_config,
                format_type=format_type
            )
            
            # 调用LLM生成内容
            response = self.client.chat.completions.create(
                model=self.model,  # 统一使用self.model，火山方舟可以是推理接入点ID或模型名称
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的学术邮件写作助手，擅长撰写个性化的套磁信。请根据提供的信息生成一封专业、诚恳且个性化的套磁邮件。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            email_content = response.choices[0].message.content.strip()
            
            logger.info(f"成功生成套磁信内容，教授: {professor_info.get('name', 'Unknown')}")
            return email_content
            
        except Exception as e:
            logger.error(f"生成套磁信内容失败: {str(e)}")
            # 返回默认模板
            return self._get_default_template(professor_info, self_introduction)
    
    def _build_prompt(self,
                      professor_info: Dict[str, str],
                      self_introduction: str,
                      template_content: Optional[str] = None,
                      additional_requirements: Optional[str] = None,
                      prompt_config: Optional[Dict] = None,
                      format_type: str = 'html') -> str:
        """
        构建LLM提示词
        """
        # 使用自定义提示词配置或默认提示
        if prompt_config and prompt_config.get('user_prompt_template'):
            # 使用自定义用户提示模板
            template_section = f"\n## 邮件模板参考：\n{template_content}" if template_content else ""
            additional_section = f"\n## 额外要求：\n{additional_requirements}" if additional_requirements else ""
            
            prompt = prompt_config['user_prompt_template'].format(
                professor_name=professor_info.get('name', '未知'),
                professor_university=professor_info.get('university', '未知'),
                professor_department=professor_info.get('department', '未知'),
                professor_research_area=professor_info.get('research_area', '未知'),
                professor_introduction=professor_info.get('introduction', '无'),
                self_introduction=self_introduction,
                template_section=template_section,
                additional_section=additional_section,
                format_instruction='使用纯文本格式，段落之间用空行分隔，不要使用HTML标签' if format_type == 'text' else '使用HTML格式'
            )
            return prompt
        
        # 使用默认提示构建
        prompt_parts = [
            "请根据以下信息生成一封个性化的套磁邮件：\n",
            "\n## 教授信息：",
            f"姓名: {professor_info.get('name', '未知')}",
            f"大学: {professor_info.get('university', '未知')}",
            f"院系: {professor_info.get('department', '未知')}",
            f"研究领域: {professor_info.get('research_area', '未知')}",
            f"教授介绍: {professor_info.get('introduction', '无')}",
            "\n## 申请者自我介绍：",
            self_introduction,
        ]
        
        if template_content:
             prompt_parts.extend([
                 "\n## 邮件模板参考：",
                 template_content
             ])
        
        if additional_requirements:
            prompt_parts.extend([
                "\n## 额外要求：",
                additional_requirements
            ])
        
        # 根据格式类型调整要求
        if format_type == 'text':
            prompt_parts.extend([
                "\n## 要求：",
                "1. 邮件应该专业、诚恳且个性化",
                "2. 突出申请者与教授研究领域的匹配度",
                "3. 体现申请者的学术背景和研究兴趣",
                "4. 语言要礼貌得体，符合学术邮件规范",
                "5. 长度适中，不要过于冗长",
                "6. 如果教授信息中有具体的研究内容，要针对性地提及",
                "7. 邮件应该包含明确的申请意图",
                "8. 请使用纯文本格式返回邮件内容，段落之间用空行分隔",
                "9. 不要使用HTML标签或Markdown格式",
                "\n请直接返回纯文本格式的邮件正文内容，不需要包含主题行。"
            ])
        else:
            prompt_parts.extend([
                "\n## 要求：",
                "1. 邮件应该专业、诚恳且个性化",
                "2. 突出申请者与教授研究领域的匹配度",
                "3. 体现申请者的学术背景和研究兴趣",
                "4. 语言要礼貌得体，符合学术邮件规范",
                "5. 长度适中，不要过于冗长",
                "6. 如果教授信息中有具体的研究内容，要针对性地提及",
                "7. 邮件应该包含明确的申请意图",
                "8. 请使用HTML格式返回邮件内容，包含适当的段落标签<p>和换行<br>",
                "\n请直接返回HTML格式的邮件正文内容，不需要包含主题行。"
            ])
        
        return "\n".join(prompt_parts)
    
    def _get_default_template(self, professor_info: Dict[str, str], self_introduction: str) -> str:
        """
        获取默认邮件模板（当LLM服务不可用时使用）
        """
        professor_name = professor_info.get('name', '教授')
        university = professor_info.get('university', '')
        research_area = professor_info.get('research_area', '')
        
        template = f"""<p>尊敬的{professor_name}：</p>

<p>您好！我是一名对{research_area}领域非常感兴趣的学生。通过了解您在{university}的研究工作，我对您的研究方向产生了浓厚的兴趣。</p>

<p>{self_introduction}</p>

<p>我希望能够有机会在您的指导下进行研究学习。如果您目前有招收学生的计划，我非常希望能够进一步交流。</p>

<p>感谢您抽出宝贵时间阅读这封邮件，期待您的回复。</p>

<p>此致<br>
敬礼！</p>

<p>{datetime.now().strftime('%Y年%m月%d日')}</p>"""
        
        return template
    
    def generate_subject(self, professor_info: Dict[str, str], applicant_name: str) -> str:
        """
        生成邮件主题
        
        Args:
            professor_info: 教授信息
            applicant_name: 申请者姓名
            
        Returns:
            str: 邮件主题
        """
        try:
            prompt = f"""
请为以下套磁邮件生成一个合适的主题：

教授姓名: {professor_info.get('name', '未知')}
教授大学: {professor_info.get('university', '未知')}
研究领域: {professor_info.get('research_area', '未知')}
申请者姓名: {applicant_name}

要求：
1. 主题要简洁明了
2. 体现申请意图
3. 包含关键信息（如研究领域或申请类型）
4. 长度控制在50字符以内
5. 专业且礼貌

请只返回主题内容，不要包含其他文字。
"""
            
            if self.provider == 'volcengine':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的邮件主题生成助手。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.5,
                    max_tokens=100
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的邮件主题生成助手。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.5,
                    max_tokens=100
                )
            
            subject = response.choices[0].message.content.strip()
            return subject
            
        except Exception as e:
            logger.error(f"生成邮件主题失败: {str(e)}")
            # 返回默认主题
            research_area = professor_info.get('research_area', '相关领域')
            return f"关于{research_area}研究的学习申请 - {applicant_name}"
    
    def optimize_email_content(self, original_content: str, optimization_request: str) -> str:
        """
        优化邮件内容
        
        Args:
            original_content: 原始邮件内容
            optimization_request: 优化要求
            
        Returns:
            str: 优化后的邮件内容
        """
        try:
            prompt = f"""
请根据以下要求优化这封套磁邮件：

## 原始邮件内容：
{original_content}

## 优化要求：
{optimization_request}

## 注意事项：
1. 保持邮件的专业性和礼貌性
2. 确保优化后的内容符合学术邮件规范
3. 保留原邮件的核心信息和申请意图
4. 根据要求进行针对性调整

请返回优化后的邮件内容：
"""
            
            if self.provider == 'volcengine':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的邮件优化助手，擅长改进学术邮件的表达和结构。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.6,
                    max_tokens=1500
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的邮件优化助手，擅长改进学术邮件的表达和结构。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.6,
                    max_tokens=1500
                )
            
            optimized_content = response.choices[0].message.content.strip()
            
            logger.info("邮件内容优化成功")
            return optimized_content
            
        except Exception as e:
            logger.error(f"优化邮件内容失败: {str(e)}")
            return original_content
    
    def check_api_status(self) -> bool:
        """
        检查LLM API是否可用
        
        Returns:
            bool: API是否可用
        """
        try:
            if self.provider == 'volcengine':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": "Hello"
                        }
                    ],
                    max_tokens=10
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": "Hello"
                        }
                    ],
                    max_tokens=10
                )
            return True
        except Exception as e:
            logger.error(f"LLM API不可用: {str(e)}")
            return False