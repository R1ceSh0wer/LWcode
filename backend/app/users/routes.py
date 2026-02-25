from flask import jsonify, request, send_from_directory, current_app
from datetime import datetime
from models import db, User, StudentInfo
from neo4j_service import neo4j_conn
import os
import openpyxl
from app.users import bp


@bp.route('/accounts', methods=['GET'])
def get_accounts():
    try:
        accounts = User.query.all()
        
        result = []
        for account in accounts:
            account_data = {
                'id': str(account.id),
                'username': account.username,
                'role': account.role,
                'created_at': account.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if account.role == 'student' and account.student_info:
                account_data['grade'] = account.student_info.grade
                account_data['studentNumber'] = account.student_info.student_number
                account_data['name'] = account.student_info.name
                account_data['features'] = account.student_info.features
            
            result.append(account_data)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取账号列表失败：{str(e)}'}), 500


@bp.route('/accounts', methods=['POST'])
def create_account():
    data = request.get_json()
    try:
        new_account = User(
            username=data.get('username'),
            password=data.get('password'),
            role=data.get('role')
        )
        db.session.add(new_account)
        db.session.commit()
        
        if new_account.role == 'student':
            student_info = StudentInfo(
                user_id=new_account.id,
                name=data.get('name'),
                grade=data.get('grade'),
                student_number=data.get('studentNumber'),
                features=data.get('features')
            )
            db.session.add(student_info)
            db.session.commit()
            
            neo4j_conn.create_node(
                'Student',
                {
                    'student_id': str(new_account.id),
                    'name': data.get('name'),
                    'grade': data.get('grade'),
                    'student_number': data.get('studentNumber'),
                    'features': data.get('features')
                }
            )
        
        return jsonify({
            'id': str(new_account.id),
            'username': new_account.username,
            'role': new_account.role,
            'created_at': new_account.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建账号失败：{str(e)}'}), 500


@bp.route('/accounts/<string:id>', methods=['DELETE'])
def delete_account(id):
    try:
        account = User.query.filter_by(id=id).first()
        if not account:
            return jsonify({'success': False, 'message': '账号不存在'}), 404
        
        if account.role == 'student':
            if account.student_info:
                db.session.delete(account.student_info)
            
            comments = Comment.query.filter_by(student_id=id).all()
            for comment in comments:
                db.session.delete(comment)
            
            summary_comments = SummaryComment.query.filter_by(student_id=id).all()
            for summary_comment in summary_comments:
                db.session.delete(summary_comment)
        elif account.role == 'teacher':
            columns = ExamColumn.query.filter_by(teacher_id=id).all()
            for column in columns:
                comments = Comment.query.filter_by(column_id=column.id).all()
                for comment in comments:
                    db.session.delete(comment)
                db.session.delete(column)
        
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '账号已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除账号失败：{str(e)}'}), 500


@bp.route('/accounts/template', methods=['GET'])
def download_account_template():
    try:
        template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'example.xlsx')
        if os.path.exists(template_path):
            return send_from_directory(
                os.path.dirname(template_path),
                'example.xlsx',
                as_attachment=True,
                download_name='账号模板.xlsx'
            )
        else:
            return jsonify({'success': False, 'message': '模板文件不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载模板失败：{str(e)}'}), 500


@bp.route('/accounts/batch', methods=['POST'])
def batch_add_accounts():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
        
        temp_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(temp_file_path)
        
        wb = openpyxl.load_workbook(temp_file_path)
        ws = wb.active
        
        success_count = 0
        failure_count = 0
        failures = []
        
        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                if all(cell is None for cell in row):
                    continue
                
                role_code = row[0]
                
                if role_code not in [1, '1', 2, '2']:
                    continue
                
                if len(row) < 3:
                    failure_count += 1
                    failures.append(f'行 {row_num}: 数据不完整')
                    continue
                
                username = row[1]
                password = row[2]
                name = row[3] if len(row) > 3 else ''
                grade = row[4] if len(row) > 4 else ''
                student_number = row[5] if len(row) > 5 else ''
                features = row[6] if len(row) > 6 else ''
                
                if role_code == 1 or role_code == '1':
                    role = 'student'
                else:
                    role = 'teacher'
                
                if not username or not password:
                    failure_count += 1
                    failures.append(f'行 {row_num}: 用户名或密码不能为空')
                    continue
                
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    failure_count += 1
                    failures.append(f'行 {row_num}: 用户名已存在')
                    continue
                
                new_account = User(
                    username=username,
                    password=password,
                    role=role
                )
                db.session.add(new_account)
                db.session.commit()
                
                if role == 'student':
                    if not name or not grade or not student_number:
                        failure_count += 1
                        failures.append(f'行 {row_num}: 学生姓名、班级或学号不能为空')
                        db.session.delete(new_account)
                        db.session.commit()
                        continue
                    
                    student_info = StudentInfo(
                        user_id=new_account.id,
                        name=name,
                        grade=grade,
                        student_number=student_number,
                        features=features
                    )
                    db.session.add(student_info)
                    db.session.commit()
                    
                    try:
                        neo4j_conn.create_node(
                            'Student',
                            {
                                'student_id': str(new_account.id),
                                'name': name,
                                'grade': grade,
                                'student_number': student_number,
                                'features': features
                            }
                        )
                    except Exception as neo4j_error:
                        print(f"Neo4j创建学生节点失败 (行 {row_num}): {str(neo4j_error)}")
                
                success_count += 1
            except Exception as e:
                failure_count += 1
                failures.append(f'行 {row_num}: 处理失败 - {str(e)}')
                db.session.rollback()
        
        os.remove(temp_file_path)
        
        return jsonify({
            'success': True,
            'successCount': success_count,
            'failureCount': failure_count,
            'failures': failures
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'批量添加账号失败：{str(e)}'}), 500


@bp.route('/accounts/<string:id>', methods=['PUT'])
def update_account(id):
    data = request.get_json()
    try:
        account = User.query.filter_by(id=id).first()
        if not account:
            return jsonify({'success': False, 'message': '账号不存在'}), 404
        
        if 'username' in data:
            account.username = data['username']
        if 'password' in data and data['password']:
            account.password = data['password']
        if 'role' in data:
            account.role = data['role']
        
        db.session.commit()
        
        if account.role == 'student':
            student_info = StudentInfo.query.filter_by(user_id=account.id).first()
            if not student_info:
                student_info = StudentInfo(user_id=account.id)
                db.session.add(student_info)
            
            if 'name' in data:
                student_info.name = data['name']
            if 'grade' in data:
                student_info.grade = data['grade']
            if 'studentNumber' in data:
                student_info.student_number = data['studentNumber']
            if 'features' in data:
                student_info.features = data['features']
            
            db.session.commit()
            
            neo4j_conn.update_node(
                'Student',
                'student_id',
                id,
                {
                    'name': data.get('name', ''),
                    'grade': data.get('grade', ''),
                    'student_number': data.get('studentNumber', ''),
                    'features': data.get('features', '')
                }
            )
        
        return jsonify({
            'id': str(account.id),
            'username': account.username,
            'role': account.role,
            'created_at': account.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新账号失败：{str(e)}'}), 500
