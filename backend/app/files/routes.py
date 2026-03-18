from flask import jsonify, request, send_from_directory, current_app
from datetime import datetime
from werkzeug.utils import secure_filename
from utils import allowed_file, save_uploaded_file
import os
import uuid
import time
from app.api_response import ok, fail
from app.files import bp


@bp.route('/upload', methods=['POST'])
def upload_file():
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    
    try:
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        if 'file' not in request.files:
            return fail('没有文件上传', 400)
        
        file = request.files['file']
        
        if file.filename == '':
            return fail('没有选择文件', 400)
        
        if not allowed_file(file.filename):
            return fail('文件类型不支持', 400)
        
        file_path, filename = save_uploaded_file(file)
        
        if not file_path:
            return fail('文件保存失败', 500)
        
        return ok({'fileUrl': f'uploads/{filename}', 'filename': filename}, message='文件上传成功')
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return fail(f'文件上传失败：{str(e)}', 500)


@bp.route('/images', methods=['GET'])
def get_images():
    """获取图片列表"""
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    try:
        if not os.path.exists(upload_folder):
            return ok([])
        
        files = []
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                files.append({
                    'id': filename,
                    'name': filename,
                    'url': f'uploads/{filename}',
                    'size': os.path.getsize(os.path.join(upload_folder, filename)),
                    'created': datetime.fromtimestamp(os.path.getctime(os.path.join(upload_folder, filename))).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return ok(files)
    except Exception as e:
        return fail(f'获取图片列表失败：{str(e)}', 500)


@bp.route('/images/<string:id>', methods=['GET'])
def get_image_by_id(id):
    """获取单个图片"""
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    file_path = os.path.join(upload_folder, id)
    
    try:
        if not os.path.exists(file_path):
            return fail('图片不存在', 404)
        
        return ok({
            'id': id,
            'name': id,
            'url': f'uploads/{id}',
            'size': os.path.getsize(file_path),
            'created': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return fail(f'获取图片失败：{str(e)}', 500)


@bp.route('/images/<string:id>', methods=['DELETE'])
def delete_image_by_id(id):
    """删除图片"""
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    file_path = os.path.join(upload_folder, id)
    
    try:
        if not os.path.exists(file_path):
            return fail('图片不存在', 404)
        
        os.remove(file_path)
        return ok(None, message='图片删除成功')
    except Exception as e:
        return fail(f'删除图片失败：{str(e)}', 500)


@bp.route('/images/batch', methods=['DELETE'])
def delete_images_batch():
    """批量删除图片"""
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return fail('缺少图片ID列表', 400)
        
        ids = data['ids']
        deleted = []
        failed = []
        
        for id in ids:
            file_path = os.path.join(upload_folder, id)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted.append(id)
                else:
                    failed.append({'id': id, 'message': '图片不存在'})
            except Exception as e:
                failed.append({'id': id, 'message': str(e)})
        
        return ok({'deleted': deleted, 'failed': failed}, message=f'成功删除 {len(deleted)} 张图片')
    except Exception as e:
        return fail(f'批量删除失败：{str(e)}', 500)


@bp.route('/images/stats', methods=['GET'])
def get_image_stats():
    """获取图片统计信息"""
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    
    try:
        if not os.path.exists(upload_folder):
            return ok({'total': 0, 'size': 0})
        
        files = []
        total_size = 0
        for filename in os.listdir(upload_folder):
            if allowed_file(filename):
                files.append(filename)
                total_size += os.path.getsize(os.path.join(upload_folder, filename))
        
        return ok({'total': len(files), 'size': total_size})
    except Exception as e:
        return fail(f'获取统计信息失败：{str(e)}', 500)


@bp.route('/uploads/<path:filename>', methods=['GET'])
def uploaded_file(filename):
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    return send_from_directory(upload_folder, filename)


@bp.route('/images/<filename>', methods=['GET'])
def get_image(filename):
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    return send_from_directory(upload_folder, filename)


@bp.route('/files/images', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return fail('没有文件上传', 400)
    
    file = request.files['file']
    if file.filename == '':
        return fail('没有选择文件', 400)
    
    if not allowed_file(file.filename):
        return fail('文件类型不支持', 400)
    
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # 使用 secure_filename 函数处理文件名
    filename = secure_filename(file.filename)
    # 添加时间戳防止文件名重复
    timestamp = int(time.time())
    filename = f"{timestamp}_{filename}"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    return ok({'imageUrl': f'images/{filename}'}, message='上传成功')
