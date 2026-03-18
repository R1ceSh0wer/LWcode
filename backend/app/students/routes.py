from flask import jsonify, request
from ..users.models import db, User, StudentInfo
from neo4j_service import neo4j_conn
from app.api_response import ok, fail
from . import bp


@bp.route('/students', methods=['GET'])
def get_students():
    try:
        students = User.query.join(StudentInfo).filter(User.role == 'student').all()
        
        result = []
        for student in students:
            result.append({
                'id': str(student.id),
                'name': student.student_info.name,
                'studentId': student.student_info.student_number,
                'className': student.student_info.grade,
                'username': student.username
            })
        
        return ok(result)
    except Exception as e:
        return fail(f'获取学生列表失败：{str(e)}', 500)


@bp.route('/students/<string:id>', methods=['GET'])
def get_student(id):
    try:
        student = User.query.filter_by(id=id, role='student').first()
        
        if student and student.student_info:
            return ok({
                'id': str(student.id),
                'name': student.student_info.name,
                'studentId': student.student_info.student_number,
                'className': student.student_info.grade,
                'username': student.username,
                'features': student.student_info.features
            })
        return fail('学生不存在', 404)
    except Exception as e:
        return fail(f'获取学生信息失败：{str(e)}', 500)


@bp.route('/students/integrated/<string:student_id>', methods=['GET'])
def get_integrated_student_data(student_id):
    try:
        student = User.query.filter_by(id=student_id, role='student').first()
        if not student or not student.student_info:
            return fail('学生不存在', 404)
        
        mysql_data = {
            'id': str(student.id),
            'username': student.username,
            'name': student.student_info.name,
            'student_number': student.student_info.student_number,
            'grade': student.student_info.grade,
            'features': student.student_info.features,
            'created_at': student.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        neo4j_results = neo4j_conn.find_nodes(
            'Student',
            {'student_id': student_id}
        )
        
        neo4j_data = []
        for record in neo4j_results:
            node = record['n']
            neo4j_data.append({
                'node_id': str(node.id),
                'properties': dict(node.items())
            })
        
        return ok({'mysql_data': mysql_data, 'neo4j_data': neo4j_data})
    except Exception as e:
        return fail(f'获取集成数据失败：{str(e)}', 500)
