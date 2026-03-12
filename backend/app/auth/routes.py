from flask import jsonify, request
from ..users.models import db, User
from . import bp


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    selected_role = data.get('role')
    
    try:
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            if selected_role and user.role != selected_role:
                return jsonify({'success': False, 'message': '请选择正确身份'}), 401
            
            return jsonify({
                'success': True,
                'user': {
                    'username': user.username,
                    'role': user.role,
                    'name': user.username,
                    'id': user.id
                }
            })
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败：{str(e)}'}), 500


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    try:
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 创建新用户
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': {
                'username': new_user.username,
                'role': new_user.role,
                'name': new_user.username,
                'id': new_user.id
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'注册失败：{str(e)}'}), 500
