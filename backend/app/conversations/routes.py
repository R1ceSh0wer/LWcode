from flask import jsonify, request, current_app
from datetime import datetime
import requests
from models import db, User, Conversation, Message
from app.conversations import bp


@bp.route('/qa/conversations', methods=['POST'])
def create_conversation():
    """创建新会话"""
    data = request.json
    student_id = data.get('student_id')
    
    # 验证用户存在
    student = User.query.get(student_id)
    if not student or student.role != 'student':
        return jsonify({'success': False, 'message': '无效的学生ID'}), 400
    
    # 创建新会话
    conversation = Conversation(
        student_id=student_id,
        title='新会话',
        created_at=datetime.now()
    )
    
    try:
        db.session.add(conversation)
        db.session.commit()
        return jsonify({'success': True, 'conversation_id': conversation.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/qa/conversations/<int:student_id>', methods=['GET'])
def get_conversations(student_id):
    """获取学生的所有会话"""
    conversations = Conversation.query.filter_by(student_id=student_id).order_by(Conversation.updated_at.desc()).all()
    
    result = []
    for conv in conversations:
        # 获取最新的消息作为会话预览
        latest_message = conv.messages.order_by(Message.created_at.desc()).first()
        preview = latest_message.content if latest_message else ''
        
        result.append({
            'id': conv.id,
            'dify_conversation_id': conv.dify_conversation_id,
            'title': conv.title,
            'preview': preview,
            'created_at': conv.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': conv.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'success': True, 'conversations': result})


@bp.route('/qa/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    """获取会话的所有消息"""
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    
    result = []
    for msg in messages:
        result.append({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'name': msg.name,  # 添加name字段
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'success': True, 'messages': result})


@bp.route('/qa/ask', methods=['POST'])
def ask_question():
    """向AI提问并保存对话"""
    data = request.json
    student_id = data.get('student_id')
    question = data.get('question')
    conversation_id = data.get('conversation_id')  # 可选，用于继续之前的会话
    
    # 验证参数
    if not student_id or not question:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    # 验证用户存在
    student = User.query.get(student_id)
    if not student or student.role != 'student':
        return jsonify({'success': False, 'message': '无效的学生ID'}), 400
    
    # 处理会话
    conversation = None
    if conversation_id:
        # 继续之前的会话
        conversation = Conversation.query.get(conversation_id)
        if not conversation or conversation.student_id != student_id:
            return jsonify({'success': False, 'message': '无效的会话ID'}), 400
    else:
        # 创建新会话
        conversation = Conversation(
            student_id=student_id,
            title=question[:50] + '...' if len(question) > 50 else question,
            created_at=datetime.now()
        )
        db.session.add(conversation)
        db.session.flush()  # 获取新创建的会话ID
    
    try:
        # 调用Dify API
        dify_response = requests.post(
            'https://api.dify.ai/v1/chat-messages',
            headers={
                'Authorization': f'Bearer {current_app.config.get("DIFY_API_KEY", "")}',
                'Content-Type': 'application/json'
            },
            json={
                'query': question,
                'inputs': {},
                'response_mode': 'blocking',  # 或 'streaming' 用于流式输出
                'user': f'student_{student_id}',  # 用户标识，确保唯一
                'conversation_id': conversation.dify_conversation_id if conversation.dify_conversation_id else None
            }
        )
        
        if dify_response.status_code != 200:
            return jsonify({'success': False, 'message': '调用AI服务失败'}), 500
        
        dify_data = dify_response.json()
        
        # 更新会话的dify_conversation_id（如果是第一次调用）
        if not conversation.dify_conversation_id and dify_data.get('conversation_id'):
            conversation.dify_conversation_id = dify_data['conversation_id']
        
        # 保存用户消息
        user_message = Message(
            conversation_id=conversation.id,
            role='user',
            content=question,
            name=student.username,  # 保存学生用户名
            dify_message_id=dify_data.get('message_id') if dify_data.get('message_id') else None,
            created_at=datetime.now()
        )
        
        # 保存AI回答
        ai_message = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=dify_data.get('answer', ''),
            name=student.username,  # 保存学生用户名（因为是与该学生的对话）
            dify_message_id=dify_data.get('message_id') if dify_data.get('message_id') else None,
            created_at=datetime.now()
        )
        
        db.session.add(user_message)
        db.session.add(ai_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'answer': dify_data.get('answer', ''),
            'messages': [
                {
                    'id': user_message.id,
                    'role': 'user',
                    'content': question,
                    'name': user_message.name,  # 添加name字段
                    'created_at': user_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                },
                {
                    'id': ai_message.id,
                    'role': 'assistant',
                    'content': dify_data.get('answer', ''),
                    'name': ai_message.name,  # 添加name字段
                    'created_at': ai_message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/qa/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """删除会话"""
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'success': False, 'message': '会话不存在'}), 404
    
    try:
        # 删除会话的所有消息
        Message.query.filter_by(conversation_id=conversation_id).delete()
        # 删除会话
        db.session.delete(conversation)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/qa/conversations/<int:conversation_id>/name', methods=['POST'])
def rename_conversation(conversation_id):
    """重命名会话"""
    data = request.json
    name = data.get('name', '')
    auto_generate = data.get('auto_generate', False)
    student_id = data.get('student_id')
    
    # 验证参数
    if not student_id:
        return jsonify({'success': False, 'message': '缺少学生ID'}), 400
    
    conversation = Conversation.query.get(conversation_id)
    if not conversation:
        return jsonify({'success': False, 'message': '会话不存在'}), 404
    
    if conversation.student_id != student_id:
        return jsonify({'success': False, 'message': '无权操作此会话'}), 403
    
    try:
        # 如果需要自动生成名称
        if auto_generate:
            # 调用Dify API自动生成名称
            if conversation.dify_conversation_id:
                dify_response = requests.post(
                    f'https://api.dify.ai/v1/conversations/{conversation.dify_conversation_id}/name',
                    headers={
                        'Authorization': f'Bearer {current_app.config.get("DIFY_API_KEY", "")}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'name': '',
                        'auto_generate': True,
                        'user': f'student_{student_id}'
                    }
                )
                
                if dify_response.status_code == 200:
                    dify_data = dify_response.json()
                    name = dify_data.get('name', name)
        
        # 更新会话名称
        conversation.title = name if name else '新会话'
        conversation.updated_at = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'conversation_id': conversation.id,
            'title': conversation.title
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
