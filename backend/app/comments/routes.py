from flask import jsonify, request, current_app
from datetime import datetime
from .models import Comment, SummaryComment
from ..users.models import db, User
from ..columns.models import ExamColumn
from app.api_response import ok, fail
from utils import allowed_file, ocr_process, batch_ocr_process, call_ai_service, construct_comment_prompt, construct_summary_prompt, batch_compare_images, generate_comment_with_dify
from neuralcdm_predict import load_neuralcdm_model, predict_student_performance, analyze_student_weaknesses, format_cdm_predictions
import os
import json
from . import bp


@bp.route('/comments', methods=['GET'])
def get_comments():
    try:
        student_id = request.args.get('studentId')
        
        if student_id:
            comments = Comment.query.filter_by(student_id=student_id).all()
        else:
            comments = Comment.query.all()
        
        result = []
        for comment in comments:
            result.append({
                'id': str(comment.id),
                'columnId': str(comment.column_id),
                'studentId': str(comment.student_id),
                'content': comment.content,
                'style': comment.style,
                'createdAt': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'isRegenerated': comment.is_regenerated,
                'feedback': comment.feedback,
                'feedbackTime': comment.feedback_time.strftime('%Y-%m-%d %H:%M:%S') if comment.feedback_time else None,
                'answerImagePath1': comment.answer_image_path1,
                'answerImagePath2': comment.answer_image_path2,
                'answerImagePath3': comment.answer_image_path3,
                'answerImagePath4': comment.answer_image_path4,
                'answerImagePath5': comment.answer_image_path5,
                'answerImagePath6': comment.answer_image_path6
            })
        
        return ok(result)
    except Exception as e:
        return fail(f'获取评语列表失败：{str(e)}', 500)


@bp.route('/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    try:
        existing_comment = Comment.query.filter_by(
            student_id=data.get('studentId'),
            column_id=data.get('columnId')
        ).first()
        
        if existing_comment:
            return ok({
                'id': str(existing_comment.id),
                'columnId': str(existing_comment.column_id),
                'studentId': str(existing_comment.student_id),
                'content': existing_comment.content,
                'style': existing_comment.style,
                'createdAt': existing_comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'isRegenerated': existing_comment.is_regenerated
            })
        
        new_comment = Comment(
            column_id=data.get('columnId'),
            student_id=data.get('studentId'),
            content=data.get('content'),
            style=data.get('style', '鼓励')
        )
        db.session.add(new_comment)
        db.session.commit()
        
        return ok({
            'id': str(new_comment.id),
            'columnId': str(new_comment.column_id),
            'studentId': str(new_comment.student_id),
            'content': new_comment.content,
            'style': new_comment.style,
            'createdAt': new_comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'isRegenerated': new_comment.is_regenerated
        }, status_code=201)
    except Exception as e:
        db.session.rollback()
        return fail(f'创建评语失败：{str(e)}', 500)


@bp.route('/comments/<string:id>', methods=['GET'])
def get_comment(id):
    try:
        comment = Comment.query.filter_by(id=id).first()
        
        if comment:
            return ok({
                'id': str(comment.id),
                'columnId': str(comment.column_id),
                'studentId': str(comment.student_id),
                'content': comment.content,
                'style': comment.style,
                'createdAt': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'isRegenerated': comment.is_regenerated,
                'feedback': comment.feedback,
                'feedbackTime': comment.feedback_time.strftime('%Y-%m-%d %H:%M:%S') if comment.feedback_time else None,
                'answerResult': comment.answer_result,
                'answerImagePath1': comment.answer_image_path1,
                'answerImagePath2': comment.answer_image_path2,
                'answerImagePath3': comment.answer_image_path3,
                'answerImagePath4': comment.answer_image_path4,
                'answerImagePath5': comment.answer_image_path5,
                'answerImagePath6': comment.answer_image_path6
            })
        return fail('评语不存在', 404)
    except Exception as e:
        return fail(f'获取评语信息失败：{str(e)}', 500)


@bp.route('/comments/<string:commentId>/feedback', methods=['POST'])
def submit_feedback(commentId):
    data = request.get_json()
    try:
        comment = Comment.query.filter_by(id=commentId).first()
        if not comment:
            return fail('评语不存在', 404)
        
        comment.feedback = data.get('feedback')
        comment.feedback_time = datetime.now()
        db.session.commit()
        
        return ok(None, message='反馈已提交')
    except Exception as e:
        db.session.rollback()
        return fail(f'提交反馈失败：{str(e)}', 500)


@bp.route('/comments/<string:commentId>', methods=['DELETE'])
def delete_comment(commentId):
    try:
        comment = Comment.query.filter_by(id=commentId).first()
        if not comment:
            return fail('评语不存在', 404)
        
        image_paths_to_delete = []
        for i in range(1, 7):
            image_path = getattr(comment, f'answer_image_path{i}', None)
            if image_path and image_path != '无' and image_path != '':
                image_paths_to_delete.append(image_path)
        
        db.session.delete(comment)
        db.session.commit()
        
        for image_path in image_paths_to_delete:
            try:
                full_path = os.path.join(os.getcwd(), image_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f'成功删除图片: {full_path}')
                else:
                    print(f'图片不存在: {full_path}')
            except Exception as image_error:
                print(f'删除图片失败 {image_path}: {str(image_error)}')
        
        return ok(None, message='评语和相关图片删除成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'删除评语失败：{str(e)}', 500)


@bp.route('/comments/<string:commentId>/regenerate', methods=['POST'])
def regenerate_comment(commentId, data=None):
    if data is None:
        data = request.get_json()
    
    try:
        comment = Comment.query.filter_by(id=commentId).first()
        if not comment:
            return fail('评语不存在', 404)
        
        student = User.query.filter_by(id=comment.student_id).first()
        column = ExamColumn.query.filter_by(id=comment.column_id).first()
        
        if not student or not column:
            return fail('学生或专栏信息不存在', 404)
        
        # 从answer_result构建combined_answer_text
        answer_texts = []
        if comment.answer_result:
            results = comment.answer_result.split('|')
            for i, result in enumerate(results):
                if result == "正确":
                    answer_texts.append(f"第{i+1}题：正确（勾）")
                elif result == "错误":
                    answer_texts.append(f"第{i+1}题：错误（叉）")
                elif result == "未识别":
                    answer_texts.append(f"第{i+1}题：未识别")
        combined_answer_text = "\n\n".join(answer_texts) if answer_texts else "没有批改结果"
        
        ai_result = f"这是{student.username}在{column.title}的评语（{comment.style}风格）。批改结果：{combined_answer_text[:100]}..."
        
        comment.content = ai_result
        comment.is_regenerated = True
        db.session.commit()
        
        if data is not None:
            return comment
        
        return ok({
            'id': str(comment.id),
            'content': comment.content,
            'isRegenerated': comment.is_regenerated
        })
    except Exception as e:
        db.session.rollback()
        return fail(f'重新生成评语失败：{str(e)}', 500)


@bp.route('/summary-comments/<string:studentId>', methods=['GET'])
@bp.route('/comments/summary/<string:studentId>', methods=['GET'])
def get_summary_comment(studentId):
    try:
        summary = SummaryComment.query.filter_by(student_id=studentId).order_by(SummaryComment.created_at.desc()).first()
        
        if summary:
            return ok({
                'id': str(summary.id),
                'studentId': str(summary.student_id),
                'content': summary.content,
                'createdAt': summary.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        return fail('总结评语不存在', 404)
    except Exception as e:
        return fail(f'获取总结评语失败：{str(e)}', 500)


@bp.route('/summary-comments', methods=['POST'])
@bp.route('/comments/summary/<string:studentId>', methods=['POST'])
def create_summary_comment(studentId=None):
    data = request.get_json()
    if not studentId:
        studentId = data.get('studentId')
    
    try:
        student = User.query.filter_by(id=studentId, role='student').first()
        if not student:
            return fail('学生不存在', 404)
        
        comments = Comment.query.filter_by(student_id=studentId).all()
        if not comments:
            return fail('还没有单科评语，无法生成总结', 400)
        
        prompt = construct_summary_prompt(student.student_info, comments)
        ai_result = call_ai_service(prompt, system_role="mentor")
        
        new_summary = SummaryComment(
            student_id=studentId,
            content=ai_result
        )
        db.session.add(new_summary)
        db.session.commit()
        
        return ok({
            'id': str(new_summary.id),
            'studentId': str(new_summary.student_id),
            'content': new_summary.content,
            'createdAt': new_summary.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }, status_code=201)
    except Exception as e:
        db.session.rollback()
        return fail(f'生成总结评语失败：{str(e)}', 500)


@bp.route('/comments/generate', methods=['POST'])
def generate_comment():
    data = request.get_json()
    student_id = data.get('studentId')
    column_id = data.get('columnId')
    style = data.get('style', 'encouraging')
    image_ids = data.get('imageIds', [])
    image_paths = data.get('imagePaths', [])
    addition = data.get('addition', '')
    
    style_map = {
        'encouraging': '鼓励',
        'detailed': '详细',
        'concise': '简洁'
    }
    style = style_map.get(style, '鼓励')
    
    try:
        student = User.query.filter_by(id=student_id, role='student').first()
        if not student:
            return fail('学生不存在', 404)
        
        column = ExamColumn.query.filter_by(id=column_id).first()
        if not column:
            return fail('专栏不存在', 404)
        
        existing_comment = Comment.query.filter_by(
            student_id=student_id,
            column_id=column_id
        ).first()
        
        answer_image_paths = ["无" for _ in range(6)]
        images_to_delete = []
        
        if existing_comment:
            for i in range(6):
                old_path = getattr(existing_comment, f"answer_image_path{i+1}")
                if old_path and old_path != "无":
                    images_to_delete.append(old_path)
        
        if image_paths:
            print(f"使用前端直接传递的图片路径: {image_paths}")
            for i, path in enumerate(image_paths[:6]):
                # 移除完整 URL 前缀，只保留相对路径
                if path.startswith('http://') or path.startswith('https://'):
                    # 提取路径部分
                    import urllib.parse
                    parsed_url = urllib.parse.urlparse(path)
                    path = parsed_url.path
                # 移除开头的斜杠
                if path.startswith('/'):
                    path = path[1:]
                answer_image_paths[i] = path
        else:
            if not existing_comment and image_ids:
                upload_folder = os.path.join(os.getcwd(), 'uploads')
                
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                    print(f"创建uploads目录: {upload_folder}")
                
                print(f"image_ids: {image_ids}")
                if os.path.exists(upload_folder):
                    print(f"uploads目录内容: {os.listdir(upload_folder)}")
                    
                    for i, image_id in enumerate(image_ids[:6]):
                        for filename in os.listdir(upload_folder):
                            if image_id in filename:
                                answer_image_paths[i] = f"uploads/{filename}"
                                print(f"匹配到图片 {image_id} -> {filename}")
                                break
        
        if existing_comment:
            print(f"找到现有记录，更新ID: {existing_comment.id}")
            new_comment = existing_comment
            new_comment.answer_image_path1 = answer_image_paths[0]
            new_comment.answer_image_path2 = answer_image_paths[1]
            new_comment.answer_image_path3 = answer_image_paths[2]
            new_comment.answer_image_path4 = answer_image_paths[3]
            new_comment.answer_image_path5 = answer_image_paths[4]
            new_comment.answer_image_path6 = answer_image_paths[5]
            new_comment.style = style
            new_comment.addition = addition
            # 重置新字段的值
            new_comment.answer_result = None
            new_comment.cdm_predictions = None
            new_comment.student_proficiency = None
            for i in range(1, 7):
                setattr(new_comment, f"answer_text{i}", "")
            db.session.commit()
        else:
            new_comment = Comment(
                column_id=column_id,
                student_id=student_id,
                answer_image_path1=answer_image_paths[0],
                answer_image_path2=answer_image_paths[1],
                answer_image_path3=answer_image_paths[2],
                answer_image_path4=answer_image_paths[3],
                answer_image_path5=answer_image_paths[4],
                answer_image_path6=answer_image_paths[5],
                style=style,
                addition=addition
            )
            db.session.add(new_comment)
            db.session.commit()
            print(f"创建新记录，ID: {new_comment.id}")
        
        # 获取专栏创建时的空白试题图片路径
        blank_image_paths = [
            column.question_image_path1,
            column.question_image_path2,
            column.question_image_path3,
            column.question_image_path4,
            column.question_image_path5,
            column.question_image_path6
        ]
        
        # 使用画圈识别功能识别教师批改的错题号
        print(f'[INFO] 开始识别画圈标记')
        print(f'[DEBUG] 空白图片路径: {blank_image_paths}')
        print(f'[DEBUG] 答案图片路径: {answer_image_paths}')
        try:
            answer_results = batch_compare_images(blank_image_paths, answer_image_paths, total_questions=6)
            print(f'[DEBUG] 识别结果: {answer_results}')
            
            # 处理批量对比结果，将列表扁平化
            flattened_results = []
            for result in answer_results:
                if isinstance(result, list):
                    for mark in result:
                        flattened_results.append(mark)
                else:
                    flattened_results.append(result)
            print(f'[DEBUG] 扁平化结果: {flattened_results}')
            
            # 将对错情况存入 answer_result 列
            answer_result_str = "|".join(["正确" if r is True else "错误" if r is False else "未识别" for r in flattened_results])
            print(f'[DEBUG] answer_result_str: {answer_result_str}')
            new_comment.answer_result = answer_result_str
            print(f'[DEBUG] new_comment.answer_result: {new_comment.answer_result}')
        except Exception as e:
            print(f'[ERROR] 识别画圈标记失败: {str(e)}')
            import traceback
            traceback.print_exc()
            # 设置默认值
            new_comment.answer_result = "未识别|未识别|未识别|未识别|未识别|未识别"
            print(f'[DEBUG] 异常情况下的 answer_result: {new_comment.answer_result}')
        
        print(f'[DEBUG] 提交前 - new_comment.id: {new_comment.id}')
        print(f'[DEBUG] 提交前 - new_comment.answer_result: {new_comment.answer_result}')
        db.session.commit()
        print(f'[DEBUG] 提交后 - new_comment.id: {new_comment.id}')
        print(f'[DEBUG] 提交后 - new_comment.answer_result: {new_comment.answer_result}')
        # 重新加载对象以验证保存
        temp_comment = Comment.query.get(new_comment.id)
        print(f'[DEBUG] 重新加载后 - temp_comment.answer_result: {temp_comment.answer_result}')
        
        # ========== NeuralCDM+ 模型预测流程 ==========
        print(f'\n{"="*60}')
        print(f'[NeuralCDM] 开始学生能力预测分析')
        print(f'{"="*60}')
        
        # 根据专栏关联的存档确定模型路径
        print(f'[DEBUG] 专栏ID: {column.id}')
        print(f'[DEBUG] 存档ID: {column.archive_id}')
        
        if column.archive_id:
            from app.archives.models import ModelArchive
            archive = ModelArchive.query.get(column.archive_id)
            print(f'[DEBUG] 存档对象: {archive}')
            
            if archive and archive.diagnosis_model_path:
                print(f'[DEBUG] 存档名称: {archive.name}')
                print(f'[DEBUG] 诊断模型路径: {archive.diagnosis_model_path}')
                
                # 检查路径是否存在
                if os.path.isabs(archive.diagnosis_model_path):
                    cdm_model_path = archive.diagnosis_model_path
                else:
                    # 使用更可靠的路径计算方式
                    # 获取 backend 目录的绝对路径（__file__ 是 app/comments/routes.py）
                    # dirname(__file__) 是 app/comments
                    # dirname(app/comments) 是 app
                    # dirname(app) 是 backend
                    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                    
                    # archives 目录在 backend 根目录下，不在 uploads 下
                    archives_dir = os.path.join(backend_dir, 'archives')
                    
                    print(f'[DEBUG] backend_dir: {backend_dir}')
                    print(f'[DEBUG] archives_dir: {archives_dir}')
                    
                    # 尝试 archives 目录
                    cdm_model_path = os.path.join(archives_dir, archive.diagnosis_model_path)
                    print(f'[DEBUG] 尝试路径1 (archives): {cdm_model_path}, 存在: {os.path.exists(cdm_model_path)}')
                    
                    if not os.path.exists(cdm_model_path):
                        # 尝试将路径中的 archives 替换为 uploads/archives
                        model_path_in_uploads = archive.diagnosis_model_path.replace('archives\\', 'uploads\\archives\\').replace('archives/', 'uploads/archives/')
                        cdm_model_path = os.path.join(backend_dir, model_path_in_uploads)
                        print(f'[DEBUG] 尝试路径2 (uploads/archives): {cdm_model_path}, 存在: {os.path.exists(cdm_model_path)}')
                        
                        if not os.path.exists(cdm_model_path):
                            # 尝试当前工作目录
                            cdm_model_path = os.path.join(os.getcwd(), archive.diagnosis_model_path)
                            print(f'[DEBUG] 尝试路径3 (cwd): {cdm_model_path}, 存在: {os.path.exists(cdm_model_path)}')
                            
                            if not os.path.exists(cdm_model_path):
                                # 尝试父目录
                                cdm_model_path = os.path.join(os.path.dirname(os.getcwd()), archive.diagnosis_model_path)
                                print(f'[DEBUG] 尝试路径4 (parent): {cdm_model_path}, 存在: {os.path.exists(cdm_model_path)}')
                
                print(f'[NeuralCDM] 使用存档模型：{archive.name}')
            else:
                # 尝试不同的默认路径
                cdm_model_path = os.path.join(os.getcwd(), 'NeuralCDM_plus-main', 'model', 'model_epoch28')
                if not os.path.exists(cdm_model_path):
                    cdm_model_path = os.path.join(os.path.dirname(os.getcwd()), 'NeuralCDM_plus-main', 'model', 'model_epoch28')
                print(f'[NeuralCDM] 存档模型不可用，使用默认模型')
        else:
            # 尝试不同的默认路径
            cdm_model_path = os.path.join(os.getcwd(), 'NeuralCDM_plus-main', 'model', 'model_epoch28')
            if not os.path.exists(cdm_model_path):
                cdm_model_path = os.path.join(os.path.dirname(os.getcwd()), 'NeuralCDM_plus-main', 'model', 'model_epoch28')
            print(f'[NeuralCDM] 未关联存档，使用默认模型')
        
        print(f'[NeuralCDM] 模型路径：{cdm_model_path}')
        print(f'[DEBUG] 模型路径是否存在: {os.path.exists(cdm_model_path)}')
        
        try:
            cdm_model = load_neuralcdm_model(cdm_model_path)
            
            student_id_int = int(student_id) if student_id else 0
            print(f'[NeuralCDM] 学生ID: {student_id_int}')
            
            exercise_ids = []
            knowledge_codes = []
            actual_scores = []
            
            question_knowledge = {}
            if column.question_knowledge:
                try:
                    question_knowledge = json.loads(column.question_knowledge)
                    print(f'[NeuralCDM] 加载专栏知识点: {question_knowledge}')
                except:
                    print(f'[NeuralCDM] 知识点解析失败，使用默认值')
            
            for i, result in enumerate(flattened_results):
                exer_id = i + 1
                exercise_ids.append(exer_id)
                
                q_key = str(exer_id)
                if q_key in question_knowledge and question_knowledge[q_key]:
                    kc = question_knowledge[q_key]
                else:
                    kc = [exer_id]
                knowledge_codes.append(kc)
                
                if result is True:
                    actual_scores.append(1)
                elif result is False:
                    actual_scores.append(0)
                else:
                    actual_scores.append(-1)
            
            print(f'[NeuralCDM] 题目ID列表: {exercise_ids}')
            print(f'[NeuralCDM] 知识点编码列表: {knowledge_codes}')
            print(f'[NeuralCDM] 实际得分列表: {actual_scores} (1=正确, 0=错误, -1=未识别)')
            
            if exercise_ids:
                # 确保学生 ID 在模型范围内
                if student_id_int >= 190:
                    # 使用默认学生 ID 1
                    student_id_int = 1
                    print(f'[NeuralCDM] 学生 ID {student_id} 超出模型范围，使用默认 ID 1')
                
                print(f'[DEBUG] 调用 predict_student_performance')
                print(f'[DEBUG] cdm_model: {cdm_model}')
                print(f'[DEBUG] student_id_int: {student_id_int}')
                print(f'[DEBUG] exercise_ids: {exercise_ids}')
                print(f'[DEBUG] knowledge_codes: {knowledge_codes}')
                
                predictions = predict_student_performance(
                    cdm_model, 
                    student_id_int, 
                    exercise_ids, 
                    knowledge_codes
                )
                
                print(f'[DEBUG] 预测结果: {predictions}')
                
                print(f'\n[NeuralCDM] 预测结果:')
                print(f'-' * 60)
                for i, (exer_id, pred, actual) in enumerate(zip(exercise_ids, predictions, actual_scores)):
                    actual_str = '正确' if actual == 1 else '错误' if actual == 0 else '未识别'
                    pred_str = '正确' if pred >= 0.5 else '错误'
                    match_str = '✓' if (pred >= 0.5 and actual == 1) or (pred < 0.5 and actual == 0) else '✗'
                    print(f'  第{exer_id}题: 预测正确率={pred:.4f} ({pred_str}), 实际={actual_str}, 预测{match_str}')
                
                print(f'\n[NeuralCDM] 学生知识点掌握情况分析:')
                print(f'-' * 60)
                weaknesses = analyze_student_weaknesses(cdm_model, student_id_int, top_n=5)
                print(f'[DEBUG] 弱点分析结果: {weaknesses}')
                for wk in weaknesses:
                    print(f'  知识点{wk["knowledge_id"]}: 掌握度={wk["proficiency"]:.4f} ({wk["level"]})')
                
                avg_proficiency = sum([w['proficiency'] for w in weaknesses]) / len(weaknesses)
                print(f'\n[NeuralCDM] 学生整体能力评估:')
                print(f'  平均掌握度: {avg_proficiency:.4f}')
                print(f'  能力等级: {"优秀" if avg_proficiency > 0.7 else "良好" if avg_proficiency > 0.5 else "一般" if avg_proficiency > 0.3 else "需加强"}')
                
                cdm_results = format_cdm_predictions(exercise_ids, predictions)
                print(f'[DEBUG] cdm_results: {cdm_results}')
                print(f'[DEBUG] cdm_results 类型: {type(cdm_results)}')
                new_comment.cdm_predictions = str(cdm_results)
                new_comment.student_proficiency = avg_proficiency
                print(f'[DEBUG] 提交前 - new_comment.cdm_predictions: {new_comment.cdm_predictions}')
                print(f'[DEBUG] 提交前 - new_comment.student_proficiency: {new_comment.student_proficiency}')
                db.session.commit()
                print(f'[DEBUG] 提交后 - new_comment.cdm_predictions: {new_comment.cdm_predictions}')
                print(f'[DEBUG] 提交后 - new_comment.student_proficiency: {new_comment.student_proficiency}')
                # 重新加载对象以验证保存
                temp_comment = Comment.query.get(new_comment.id)
                print(f'[DEBUG] 重新加载后 - temp_comment.cdm_predictions: {temp_comment.cdm_predictions}')
                print(f'[DEBUG] 重新加载后 - temp_comment.student_proficiency: {temp_comment.student_proficiency}')
                
                print(f'\n[NeuralCDM] 预测结果已保存至数据库')
                
                # ========== 使用Dify智能体生成评语 ==========
                print(f'\n{"="*60}')
                print(f'[Dify] 开始生成基于Dify的评语')
                print(f'{"="*60}')
                
                dify_comment = generate_comment_with_dify(
                    student.username,
                    exercise_ids, 
                    predictions, 
                    actual_scores, 
                    knowledge_codes,
                    dify_api='http://localhost:83/v1'
                )
                
                if dify_comment:
                    new_comment.content = dify_comment
                    db.session.commit()
                    print(f'[Dify] 评语已保存至数据库')
                else:
                    print(f'[Dify] 评语生成失败，使用默认评语')
                    # 构建默认评语
                    answer_texts = []
                    for i, (exer_id, pred, actual) in enumerate(zip(exercise_ids, predictions, actual_scores)):
                        actual_str = '正确' if actual == 1 else '错误' if actual == 0 else '未识别'
                        pred_str = f'{pred:.2%}'
                        answer_texts.append(f"第{exer_id}题：实际={actual_str}，预测正确率={pred_str}")
                    default_comment = f"{student.username}在{column.title}的{style}风格评语：{'; '.join(answer_texts)}。整体掌握度：{avg_proficiency:.2%}，能力等级：{'优秀' if avg_proficiency > 0.7 else '良好' if avg_proficiency > 0.5 else '一般' if avg_proficiency > 0.3 else '需加强'}"
                    new_comment.content = default_comment
                    db.session.commit()
                
            else:
                print(f'[NeuralCDM] 跳过预测: 无题目数据或学生ID超出模型范围')
                # 无预测数据时的默认处理
                answer_texts = []
                if new_comment.answer_result:
                    results = new_comment.answer_result.split('|')
                    for i, result in enumerate(results):
                        if result == "正确":
                            answer_texts.append(f"第{i+1}题：正确")
                        elif result == "错误":
                            answer_texts.append(f"第{i+1}题：错误")
                        elif result == "未识别":
                            answer_texts.append(f"第{i+1}题：未识别")
                default_comment = f"{student.username}在{column.title}的{style}风格评语：{'; '.join(answer_texts) if answer_texts else '无结果'}"
                new_comment.content = default_comment
                # 设置默认值
                new_comment.cdm_predictions = str([])
                new_comment.student_proficiency = 0.5
                print(f'[DEBUG] 无预测数据时 - new_comment.cdm_predictions: {new_comment.cdm_predictions}')
                print(f'[DEBUG] 无预测数据时 - new_comment.student_proficiency: {new_comment.student_proficiency}')
                db.session.commit()
                print(f'[DEBUG] 提交后 - new_comment.cdm_predictions: {new_comment.cdm_predictions}')
                print(f'[DEBUG] 提交后 - new_comment.student_proficiency: {new_comment.student_proficiency}')
                # 重新加载对象以验证保存
                temp_comment = Comment.query.get(new_comment.id)
                print(f'[DEBUG] 重新加载后 - temp_comment.cdm_predictions: {temp_comment.cdm_predictions}')
                print(f'[DEBUG] 重新加载后 - temp_comment.student_proficiency: {temp_comment.student_proficiency}')
        
        except Exception as cdm_error:
            print(f'[NeuralCDM] 预测过程出错: {str(cdm_error)}')
            import traceback
            traceback.print_exc()
            # 出错时生成默认评语
            answer_texts = []
            if new_comment.answer_result:
                results = new_comment.answer_result.split('|')
                for i, result in enumerate(results):
                    if result == "正确":
                        answer_texts.append(f"第{i+1}题：正确")
                    elif result == "错误":
                        answer_texts.append(f"第{i+1}题：错误")
                    elif result == "未识别":
                        answer_texts.append(f"第{i+1}题：未识别")
            default_comment = f"{student.username}在{column.title}的{style}风格评语：{'; '.join(answer_texts) if answer_texts else '无结果'}"
            new_comment.content = default_comment
            # 设置默认值
            new_comment.cdm_predictions = str([])
            new_comment.student_proficiency = 0.5
            print(f'[DEBUG] 异常情况下 - new_comment.cdm_predictions: {new_comment.cdm_predictions}')
            print(f'[DEBUG] 异常情况下 - new_comment.student_proficiency: {new_comment.student_proficiency}')
            db.session.commit()
            print(f'[DEBUG] 提交后 - new_comment.cdm_predictions: {new_comment.cdm_predictions}')
            print(f'[DEBUG] 提交后 - new_comment.student_proficiency: {new_comment.student_proficiency}')
            # 重新加载对象以验证保存
            temp_comment = Comment.query.get(new_comment.id)
            print(f'[DEBUG] 重新加载后 - temp_comment.cdm_predictions: {temp_comment.cdm_predictions}')
            print(f'[DEBUG] 重新加载后 - temp_comment.student_proficiency: {temp_comment.student_proficiency}')
        
        print(f'{"="*60}\n')
        # ========== 评语生成流程结束 ==========
        
        for old_image_path in images_to_delete:
            try:
                full_path = os.path.join(os.getcwd(), old_image_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    print(f"删除旧图片文件: {full_path}")
                else:
                    print(f"旧图片文件不存在: {full_path}")
            except Exception as e:
                print(f"删除旧图片文件失败 {old_image_path}: {str(e)}")
        
        updated_comment = Comment.query.filter_by(id=new_comment.id).first()
        
        answer_image_paths_dict = {
            "answerImagePath1": updated_comment.answer_image_path1,
            "answerImagePath2": updated_comment.answer_image_path2,
            "answerImagePath3": updated_comment.answer_image_path3,
            "answerImagePath4": updated_comment.answer_image_path4,
            "answerImagePath5": updated_comment.answer_image_path5,
            "answerImagePath6": updated_comment.answer_image_path6
        }
        
        return ok({
            'id': str(updated_comment.id),
            'columnId': str(updated_comment.column_id),
            'studentId': str(updated_comment.student_id),
            'content': updated_comment.content,
            'style': updated_comment.style,
            'addition': updated_comment.addition,
            'answerResult': updated_comment.answer_result,
            'cdmPredictions': updated_comment.cdm_predictions,
            'studentProficiency': updated_comment.student_proficiency,
            **answer_image_paths_dict,
            'createdAt': updated_comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'isRegenerated': updated_comment.is_regenerated
        }, status_code=201)
    except Exception as e:
        db.session.rollback()
        return fail(f'生成评语失败：{str(e)}', 500)
