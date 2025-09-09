import pandas as pd
import os
from typing import List, Dict, Any, Tuple
from werkzeug.datastructures import FileStorage
from .database import Professor, db
import logging

logger = logging.getLogger(__name__)

class ImportService:
    """CSV导入服务"""
    
    def __init__(self):
        self.required_columns = ['name', 'email', 'university']
        self.optional_columns = ['department', 'research_area', 'introduction']
        self.all_columns = self.required_columns + self.optional_columns
    
    def validate_csv_file(self, file: FileStorage) -> Tuple[bool, str]:
        """验证CSV文件格式"""
        try:
            # 检查文件扩展名
            if not file.filename.lower().endswith('.csv'):
                return False, "文件必须是CSV格式"
            
            # 读取CSV文件
            df = pd.read_csv(file.stream)
            
            # 重置文件指针
            file.stream.seek(0)
            
            # 检查是否为空
            if df.empty:
                return False, "CSV文件不能为空"
            
            # 检查必需列
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                return False, f"缺少必需的列: {', '.join(missing_columns)}"
            
            # 检查必需列是否有空值
            for col in self.required_columns:
                if df[col].isnull().any():
                    return False, f"列 '{col}' 不能有空值"
            
            # 检查邮箱格式
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            invalid_emails = df[~df['email'].str.match(email_pattern, na=False)]
            if not invalid_emails.empty:
                return False, f"发现无效邮箱格式，行号: {invalid_emails.index.tolist()}"
            
            return True, "文件验证通过"
            
        except Exception as e:
            logger.error(f"CSV文件验证失败: {str(e)}")
            return False, f"文件读取失败: {str(e)}"
    
    def preview_csv_data(self, file: FileStorage, limit: int = 10) -> Dict[str, Any]:
        """预览CSV数据"""
        try:
            df = pd.read_csv(file.stream)
            file.stream.seek(0)
            
            # 获取预览数据
            preview_data = df.head(limit).fillna('').to_dict('records')
            
            # 统计信息
            stats = {
                'total_rows': len(df),
                'columns': list(df.columns),
                'required_columns': self.required_columns,
                'optional_columns': self.optional_columns,
                'preview_data': preview_data
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"CSV预览失败: {str(e)}")
            raise Exception(f"预览失败: {str(e)}")
    
    def import_professors_from_csv(self, file: FileStorage, skip_duplicates: bool = True) -> Dict[str, Any]:
        """从CSV导入教授信息"""
        try:
            # 验证文件
            is_valid, message = self.validate_csv_file(file)
            if not is_valid:
                raise Exception(message)
            
            # 读取CSV数据
            df = pd.read_csv(file.stream)
            df = df.fillna('')  # 填充空值
            
            imported_count = 0
            skipped_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # 检查是否已存在
                    existing_professor = Professor.query.filter_by(email=row['email']).first()
                    
                    if existing_professor:
                        if skip_duplicates:
                            skipped_count += 1
                            continue
                        else:
                            # 更新现有记录
                            existing_professor.name = row['name']
                            existing_professor.university = row['university']
                            existing_professor.department = row.get('department', '')
                            existing_professor.research_area = row.get('research_area', '')
                            existing_professor.introduction = row.get('introduction', '')
                            imported_count += 1
                    else:
                        # 创建新记录
                        professor = Professor(
                            name=row['name'],
                            email=row['email'],
                            university=row['university'],
                            department=row.get('department', ''),
                            research_area=row.get('research_area', ''),
                            introduction=row.get('introduction', '')
                        )
                        db.session.add(professor)
                        imported_count += 1
                
                except Exception as e:
                    error_count += 1
                    errors.append(f"行 {index + 2}: {str(e)}")
                    logger.error(f"导入第 {index + 2} 行失败: {str(e)}")
            
            # 提交数据库更改
            if imported_count > 0:
                db.session.commit()
            
            result = {
                'success': True,
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'error_count': error_count,
                'total_rows': len(df),
                'errors': errors[:10]  # 只返回前10个错误
            }
            
            logger.info(f"CSV导入完成: 导入 {imported_count}, 跳过 {skipped_count}, 错误 {error_count}")
            return result
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"CSV导入失败: {str(e)}")
            raise Exception(f"导入失败: {str(e)}")
    
    def generate_csv_template(self) -> str:
        """生成CSV模板文件"""
        try:
            # 创建示例数据
            template_data = {
                'name': ['张教授', '李教授', '王教授'],
                'email': ['zhang@university.edu', 'li@university.edu', 'wang@university.edu'],
                'university': ['清华大学', '北京大学', '复旦大学'],
                'department': ['计算机科学与技术学院', '信息科学技术学院', '计算机科学技术学院'],
                'research_area': ['机器学习', '计算机视觉', '自然语言处理'],
                'introduction': [
                    '专注于机器学习算法研究，在顶级会议发表论文多篇',
                    '计算机视觉领域专家，主要研究图像识别和目标检测',
                    '自然语言处理研究者，在文本分析和语言模型方面有深入研究'
                ]
            }
            
            df = pd.DataFrame(template_data)
            
            # 保存到临时文件
            template_path = os.path.join('uploads', 'professor_template.csv')
            os.makedirs('uploads', exist_ok=True)
            df.to_csv(template_path, index=False, encoding='utf-8-sig')
            
            return template_path
            
        except Exception as e:
            logger.error(f"生成CSV模板失败: {str(e)}")
            raise Exception(f"生成模板失败: {str(e)}")
    
    def export_professors_to_csv(self, professors: List[Professor] = None) -> str:
        """导出教授信息到CSV"""
        try:
            if professors is None:
                professors = Professor.query.all()
            
            if not professors:
                raise Exception("没有可导出的教授信息")
            
            # 转换为DataFrame
            data = []
            for prof in professors:
                data.append({
                    'name': prof.name,
                    'email': prof.email,
                    'university': prof.university,
                    'department': prof.department or '',
                    'research_area': prof.research_area or '',
                    'introduction': prof.introduction or ''
                })
            
            df = pd.DataFrame(data)
            
            # 保存到文件
            export_path = os.path.join('uploads', f'professors_export_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.csv')
            os.makedirs('uploads', exist_ok=True)
            df.to_csv(export_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"导出 {len(professors)} 个教授信息到 {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"导出CSV失败: {str(e)}")
            raise Exception(f"导出失败: {str(e)}")