from flask import Blueprint, request, jsonify
from backend.database import db, Professor
import logging

logger = logging.getLogger(__name__)

# 创建教授管理蓝图
professor_bp = Blueprint('professor', __name__, url_prefix='/api')


@professor_bp.route('/professors', methods=['GET', 'POST'])
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


@professor_bp.route('/professors/all', methods=['GET'])
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


@professor_bp.route('/professors/<int:professor_id>', methods=['GET', 'PUT', 'DELETE'])
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