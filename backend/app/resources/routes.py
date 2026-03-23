from flask import Blueprint, request, current_app
from config import db
from .models import LearningResource, StudentResource
from ..users.models import User
from ..api_response import ok, fail
from utils import save_uploaded_file
import os

bp = Blueprint('resources', __name__, url_prefix='/api/resources')

ALLOWED_RESOURCE_TYPES = ['文档', '视频', '练习题', 'PPT', '其它']


def _parse_teacher_id():
    """从 query / form / JSON 获取 teacher_id 并校验为教师。"""
    tid = request.args.get('teacher_id') or request.form.get('teacher_id')
    if tid is None and request.is_json:
        tid = (request.get_json(silent=True) or {}).get('teacher_id')
    if tid is None or str(tid).strip() == '':
        return None, fail('缺少参数 teacher_id', 400)
    try:
        tid_int = int(tid)
    except (TypeError, ValueError):
        return None, fail('teacher_id 无效', 400)
    user = User.query.get(tid_int)
    if not user or user.role != 'teacher':
        return None, fail('无效的教师账号', 403)
    return tid_int, None


def _parse_student_id():
    sid = request.args.get('student_id')
    if sid is None or str(sid).strip() == '':
        return None, fail('缺少参数 student_id', 400)
    try:
        sid_int = int(sid)
    except (TypeError, ValueError):
        return None, fail('student_id 无效', 400)
    user = User.query.get(sid_int)
    if not user or user.role != 'student':
        return None, fail('无效的学生账号', 403)
    return sid_int, None


@bp.route('', methods=['POST'])
def create_resource():
    teacher_id, err = _parse_teacher_id()
    if err:
        return err

    name = request.form.get('name')
    resource_type = request.form.get('type')
    file = request.files.get('file')

    if not name or not resource_type or not file:
        return fail('资源名称、类型和文件为必填项', 400)

    if resource_type not in ALLOWED_RESOURCE_TYPES:
        return fail(f"无效的资源类型，允许的类型有: {', '.join(ALLOWED_RESOURCE_TYPES)}", 400)

    file_path, filename = save_uploaded_file(file, allow_any=True)
    if not file_path:
        return fail('保存资源文件失败（不支持的文件或保存出错）', 500)

    relative_file_path = os.path.join('uploads', filename).replace('\\', '/')

    new_resource = LearningResource(
        teacher_id=teacher_id,
        name=name,
        type=resource_type,
        file_path=relative_file_path
    )

    try:
        db.session.add(new_resource)
        db.session.commit()
        return ok(
            {'id': new_resource.id, 'name': new_resource.name, 'type': new_resource.type, 'filePath': new_resource.file_path},
            message='学习资源创建成功',
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建学习资源失败: {e}')
        return fail('创建学习资源失败', 500)


@bp.route('', methods=['GET'])
def get_resources():
    teacher_id, err = _parse_teacher_id()
    if err:
        return err

    resources = LearningResource.query.filter_by(teacher_id=teacher_id).all()
    resources_data = []
    for resource in resources:
        distributed_count = StudentResource.query.filter_by(resource_id=resource.id).count()
        resources_data.append({
            'id': resource.id,
            'name': resource.name,
            'type': resource.type,
            'filePath': resource.file_path,
            'distributedCount': distributed_count,
            'createdAt': resource.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updatedAt': resource.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
    return ok(resources_data, message='获取学习资源列表成功')


@bp.route('/<int:resource_id>', methods=['PUT'])
def update_resource(resource_id):
    teacher_id, err = _parse_teacher_id()
    if err:
        return err

    resource = LearningResource.query.get(resource_id)
    if not resource:
        return fail('资源不存在', 404)

    if resource.teacher_id != teacher_id:
        return fail('无权修改此资源', 403)

    name = request.form.get('name')
    resource_type = request.form.get('type')
    file = request.files.get('file')

    if name:
        resource.name = name

    if resource_type:
        if resource_type not in ALLOWED_RESOURCE_TYPES:
            return fail(f"无效的资源类型，允许的类型有: {', '.join(ALLOWED_RESOURCE_TYPES)}", 400)
        resource.type = resource_type

    if file:
        if resource.file_path:
            full_old = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(resource.file_path))
            if os.path.exists(full_old):
                try:
                    os.remove(full_old)
                except Exception as e:
                    current_app.logger.warning(f'删除旧资源文件失败: {e}')

        file_path, filename = save_uploaded_file(file, allow_any=True)
        if not file_path:
            return fail('保存新资源文件失败', 500)
        resource.file_path = os.path.join('uploads', filename).replace('\\', '/')

    try:
        db.session.commit()
        return ok(
            {'id': resource.id, 'name': resource.name, 'type': resource.type, 'filePath': resource.file_path},
            message='学习资源修改成功'
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'修改学习资源失败: {e}')
        return fail('修改学习资源失败', 500)


@bp.route('/<int:resource_id>', methods=['DELETE'])
def delete_resource(resource_id):
    teacher_id, err = _parse_teacher_id()
    if err:
        return err

    resource = LearningResource.query.get(resource_id)
    if not resource:
        return fail('资源不存在', 404)

    if resource.teacher_id != teacher_id:
        return fail('无权删除此资源', 403)

    StudentResource.query.filter_by(resource_id=resource.id).delete()

    if resource.file_path:
        full_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(resource.file_path))
        if os.path.exists(full_file_path):
            try:
                os.remove(full_file_path)
            except Exception as e:
                current_app.logger.warning(f'删除资源文件 {full_file_path} 失败: {e}')

    try:
        db.session.delete(resource)
        db.session.commit()
        return ok(None, message='学习资源删除成功')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除学习资源失败: {e}')
        return fail('删除学习资源失败', 500)


@bp.route('/<int:resource_id>/distribute', methods=['POST'])
def distribute_resource(resource_id):
    teacher_id, err = _parse_teacher_id()
    if err:
        return err

    resource = LearningResource.query.get(resource_id)
    if not resource:
        return fail('资源不存在', 404)

    if resource.teacher_id != teacher_id:
        return fail('无权发放此资源', 403)

    data = request.get_json(silent=True) or {}
    student_ids = data.get('student_ids', [])

    if not student_ids:
        return fail('请选择要发放的学生', 400)

    new_distributions = []
    for sid in student_ids:
        try:
            student_id = int(sid)
        except (TypeError, ValueError):
            continue

        student_user = User.query.filter_by(id=student_id, role='student').first()
        if not student_user:
            current_app.logger.warning(f'跳过无效学生 ID {student_id}')
            continue

        # 允许重复发放资源给学生
        new_distributions.append(StudentResource(student_id=student_id, resource_id=resource_id))

    if not new_distributions:
        return fail('没有有效的学生ID', 400)

    try:
        db.session.add_all(new_distributions)
        db.session.commit()
        return ok({'count': len(new_distributions)}, message=f'成功发放 {len(new_distributions)} 个学习资源')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'发放学习资源失败: {e}')
        return fail('发放学习资源失败', 500)


@bp.route('/student', methods=['GET'])
def get_student_resources():
    student_id, err = _parse_student_id()
    if err:
        return err

    resource_type = request.args.get('type')
    search_query = request.args.get('search')

    q = StudentResource.query.filter_by(student_id=student_id).join(LearningResource)

    if resource_type and resource_type.strip() and resource_type != 'all':
        q = q.filter(LearningResource.type == resource_type)

    if search_query and search_query.strip():
        q = q.filter(LearningResource.name.ilike(f'%{search_query.strip()}%'))

    distributed_resources = q.all()

    resources_data = []
    for dr in distributed_resources:
        res = dr.resource
        teacher_name = res.teacher.username if res.teacher else ''
        resources_data.append({
            'id': res.id,
            'name': res.name,
            'type': res.type,
            'filePath': res.file_path,
            'distributedAt': dr.distributed_at.strftime('%Y-%m-%d %H:%M:%S'),
            'readStatus': dr.read_status,
            'teacherName': teacher_name,
        })

    return ok(resources_data, message='获取学生学习资源成功')
