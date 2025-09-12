from flask import Blueprint, request, jsonify, send_from_directory, Response
from backend.import_service import ImportService
from backend.database import Professor
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

# 创建导入导出管理蓝图
import_bp = Blueprint('import', __name__, url_prefix='/api')

# 初始化服务
import_service = ImportService()


@import_bp.route('/import/template', methods=['GET'])
def download_csv_template():
    """下载CSV模板"""
    try:
        template_path = import_service.generate_csv_template()
        return send_from_directory(
            os.path.dirname(template_path), 
            os.path.basename(template_path), 
            as_attachment=True, 
            download_name='professor_template.csv'
        )
    except Exception as e:
        logger.error(f"下载CSV模板失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


@import_bp.route('/import/preview', methods=['POST'])
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


@import_bp.route('/import/professors', methods=['POST'])
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


@import_bp.route('/export/professors', methods=['GET'])
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
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'professors_export_{timestamp}.csv'
        
        # 直接返回CSV内容
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