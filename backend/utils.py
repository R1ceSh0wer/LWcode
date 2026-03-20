import os
import sys

# 首先设置环境变量，确保在所有导入之前生效

# ========== 修复PyTorch DLL加载问题 ==========
# 1. 添加PyTorch的lib目录到系统PATH
venv_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
torch_lib_path = os.path.join(venv_base, '.venv', 'Lib', 'site-packages', 'torch', 'lib')
if os.path.exists(torch_lib_path):
    os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
    print(f'[Init] 添加PyTorch lib目录到PATH: {torch_lib_path}')

# 2. Python 3.8+ 使用add_dll_directory
if sys.version_info >= (3, 8):
    try:
        if os.path.exists(torch_lib_path):
            os.add_dll_directory(torch_lib_path)
            print(f'[Init] 使用add_dll_directory添加: {torch_lib_path}')
    except Exception as e:
        print(f'[Init] add_dll_directory失败: {e}')

# 3. 禁用可能导致冲突的设置
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'  # 解决OpenMP多线程冲突
os.environ['OMP_NUM_THREADS'] = '1'  # 限制OpenMP线程

print(f'[Init] 环境变量已设置，准备导入模块...')
# ========== PyTorch DLL修复结束 ==========

# 设置环境变量以跳过模型源检查
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

# 禁用ONEDNN以避免转换错误（更全面的设置）
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_use_onednn_bfloat16'] = '0'
os.environ['FLAGS_use_onednn_int8'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_onednn_enabled'] = '0'
os.environ['FLAGS_use_onednn_layout_opt'] = '0'
os.environ['FLAGS_use_onednn_mkldnn_dnnl'] = '0'
os.environ['FLAGS_onednn_verbose'] = '0'
os.environ['FLAGS_onednn_lazy_init'] = '0'
os.environ['FLAGS_onednn_max_cache_size'] = '0'
os.environ['FLAGS_onednn_graph_opt'] = '0'

# 强制使用CPU模式，避免GPU相关问题
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['FLAGS_cudnn_deterministic'] = '0'
os.environ['FLAGS_cudnn_benchmark'] = '0'
os.environ['FLAGS_cudnn_conv_algorithm_search'] = '0'

# 禁用动态图相关功能，可能导致ONEDNN问题
os.environ['FLAGS_dynamic_graph_optimize'] = '0'
os.environ['FLAGS_dynamic_graph_to_static'] = '0'
os.environ['FLAGS_dynamic_graph_to_static_partial_program'] = '0'

# 禁用JIT相关功能
os.environ['FLAGS_use_jit'] = '0'
os.environ['FLAGS_use_jit_pass'] = '0'

# 禁用IR优化
os.environ['FLAGS_ir_optim'] = '0'
os.environ['FLAGS_enable_ir_optim'] = '0'

# 禁用算子融合
os.environ['FLAGS_enable_dynamic_kernel_fusion'] = '0'
os.environ['FLAGS_enable_pass_broadcast_one_op_fusion'] = '0'

# 禁用其他可能导致问题的优化
os.environ['FLAGS_enable_tensorrt'] = '0'
os.environ['FLAGS_enable_mkldnn'] = '0'
os.environ['FLAGS_enable_mkldnn_fusion'] = '0'
os.environ['FLAGS_enable_mkldnn_bfloat16'] = '0'

# 现在再导入其他模块
import json
import subprocess
import time
import re
import hashlib
import threading
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import cv2
import numpy as np
from werkzeug.utils import secure_filename
from flask import current_app
import warnings
warnings.filterwarnings('ignore')

# 尝试导入RapidOCR
try:
    from rapidocr_openvino import RapidOCR
    ocr_available = True
    print(f'[OCR] RapidOCR导入成功')
except ImportError as e:
    print(f'[OCR] RapidOCR导入失败: {str(e)}')
    ocr_available = False
    RapidOCR = None

# 延迟初始化OCR引擎
ocr_engine = None
ocr_engine_initialized = False

# 初始化OCR引擎
def init_ocr_engine():
    """初始化OCR引擎"""
    global ocr_engine, ocr_engine_initialized
    if not ocr_engine_initialized:
        try:
            print(f'[OCR] 开始初始化OCR引擎...')
            
            # 检查是否使用RapidOCR
            if ocr_available:
                print(f'[OCR] 使用RapidOCR引擎...')
                
                # 设置模型路径，使用本地OCR_models文件夹
                base_path = os.path.dirname(os.path.abspath(__file__))
                models_dir = os.path.join(base_path, "OCR_models")
                ov_dir = os.path.join(models_dir, "openvino_fp16")
                
                # 优先使用OpenVINO模型
                det_path = os.path.join(ov_dir, "det_v5_fp16.xml")
                rec_path = os.path.join(ov_dir, "rec_v5_fp16.xml")
                dict_path = os.path.join(models_dir, "temp_dict.txt")
                
                # 如果OpenVINO模型不存在，使用ONNX模型
                if not os.path.exists(det_path):
                    det_path = os.path.join(models_dir, "det_v5.onnx")
                    rec_path = os.path.join(models_dir, "rec_v5.onnx")
                    print(f'[OCR] OpenVINO模型不存在，使用ONNX模型')
                else:
                    print(f'[OCR] 使用OpenVINO模型')
                
                # 检查模型文件是否存在
                if os.path.exists(det_path) and os.path.exists(rec_path) and os.path.exists(dict_path):
                    print(f'[OCR] 模型文件存在，使用本地模型')
                else:
                    print(f'[OCR] 本地模型文件不存在，使用RapidOCR默认模型')
                    det_path = None
                    rec_path = None
                    dict_path = None
                
                # 初始化RapidOCR引擎，参考OCR_Project的参数
                ocr_engine = RapidOCR(
                    det_model_path=det_path,
                    rec_model_path=rec_path,
                    rec_keys_path=dict_path,
                    intra_op_num_threads=14,  # 增加线程数以提高性能
                    print_verbose=False  # 减少日志输出
                )
                print(f'[OCR] RapidOCR引擎初始化成功')
                ocr_engine_initialized = True
                print(f'[OCR] OCR引擎状态: {type(ocr_engine)}')
            else:
                print(f'[OCR] 没有可用的OCR引擎')
                return None
                
        except Exception as e:
            print(f'[OCR] 初始化失败: {str(e)}')
            import traceback
            traceback.print_exc()
            ocr_engine = None
    else:
        print(f'[OCR] OCR引擎已经初始化，跳过')
    return ocr_engine

def enhance_image(img):
    """
    图像增强：提高对比度和亮度，改善低光照条件下的检测效果
    :param img: 输入图像（BGR格式）
    :return: 增强后的图像
    """
    try:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    except Exception as e:
        print(f'[WARN] 图像增强失败，使用原图: {str(e)}')
        return img

def detect_diff_mask(blank_img, answer_img):
    """
    使用差分检测获取标记掩码，作为颜色检测的补充
    :param blank_img: 空白试题图片
    :param answer_img: 学生作答图片
    :return: 差分掩码
    """
    try:
        blank_gray = cv2.cvtColor(blank_img, cv2.COLOR_BGR2GRAY)
        answer_gray = cv2.cvtColor(answer_img, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(answer_gray, blank_gray)
        
        _, diff_mask = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((2, 2), np.uint8)
        diff_mask = cv2.morphologyEx(diff_mask, cv2.MORPH_OPEN, kernel)
        
        return diff_mask
    except Exception as e:
        print(f'[WARN] 差分检测失败: {str(e)}')
        return np.zeros(blank_img.shape[:2], dtype=np.uint8)

def detect_question_numbers(image_path):
    """
    使用OCR识别图片中的题号，返回题号及其y坐标
    :param image_path: 图片路径
    :return: 列表，每个元素为 (题号, y坐标)
    """
    try:
        print(f'[INFO] 开始识别题号: {image_path}')
        
        # 检查文件是否存在
        if not os.path.exists(image_path):
            print(f'[ERROR] 图片文件不存在: {image_path}')
            return []
        
        # 检查文件大小，如果太大则跳过
        file_size = os.path.getsize(image_path)
        if file_size > 10 * 1024 * 1024:  # 10MB
            print(f'[WARN] 图片文件过大 ({file_size / 1024 / 1024:.2f}MB)，可能导致OCR识别缓慢')
        
        # 初始化OCR
        ocr_engine = init_ocr_engine()
        if ocr_engine is None:
            print(f'[ERROR] OCR引擎未初始化')
            return []
        
        # OCR识别
        ocr_result = ocr_engine(image_path)
        
        # RapidOCR返回格式: (识别结果, 其他信息)，需要取第一个元素
        if isinstance(ocr_result, tuple):
            ocr_result = ocr_result[0]
        
        question_numbers = []
        if ocr_result and len(ocr_result) > 0:
            print(f'[INFO] OCR识别到 {len(ocr_result)} 个文本区域')
            for idx, item in enumerate(ocr_result):
                try:
                    # RapidOCR返回格式: [[box], text, score]
                    if isinstance(item, (list, tuple)) and len(item) >= 2:
                        box = item[0]
                        text = str(item[1]).strip()
                        score = float(item[2]) if len(item) >= 3 else 0
                        
                        # 识别题号：匹配多种格式
                        # "1", "2", "1)", "2)", "1.", "2.", "1）", "2）", "1．", "２．" 等
                        import re
                        
                        # 尝试匹配开头的数字
                        match = re.match(r'^\s*(\d+)\s*[)）.．、，,]?\s*', text)
                        if match:
                            num = int(match.group(1))
                            # 计算文本框的中心y坐标
                            center_y = 0
                            if isinstance(box, (list, tuple)) and len(box) >= 2:
                                if isinstance(box[0], (list, tuple)):
                                    # 格式: [[x1,y1], [x2,y2], ...]
                                    y_coords = [float(point[1]) for point in box if len(point) >= 2]
                                    center_y = sum(y_coords) / len(y_coords)
                                else:
                                    # 格式: [x1, y1, x2, y2] 或类似
                                    center_y = float(box[1]) if len(box) >= 2 else 0
                            else:
                                continue
                            
                            question_numbers.append((num, center_y))
                            print(f'[INFO] 识别到题号: {num}, y坐标: {center_y:.0f}')
                        
                        # 也尝试匹配纯数字文本（可能题号单独一行）
                        elif re.match(r'^\s*\d+\s*$', text):
                            num = int(text.strip())
                            center_y = 0
                            if isinstance(box, (list, tuple)) and len(box) >= 2:
                                if isinstance(box[0], (list, tuple)):
                                    y_coords = [float(point[1]) for point in box if len(point) >= 2]
                                    center_y = sum(y_coords) / len(y_coords)
                                else:
                                    center_y = float(box[1]) if len(box) >= 2 else 0
                            
                            question_numbers.append((num, center_y))
                            print(f'[INFO] 识别到纯数字题号: {num}, y坐标: {center_y:.0f}')
                        
                        # 尝试匹配包含题号的文本如 "1. 题目内容" 或 "1）题目"
                        else:
                            match2 = re.search(r'(\d+)\s*[.．)）、]', text)
                            if match2:
                                num = int(match2.group(1))
                                center_y = 0
                                if isinstance(box, (list, tuple)) and len(box) >= 2:
                                    if isinstance(box[0], (list, tuple)):
                                        y_coords = [float(point[1]) for point in box if len(point) >= 2]
                                        center_y = sum(y_coords) / len(y_coords)
                                    else:
                                        center_y = float(box[1]) if len(box) >= 2 else 0
                                
                                question_numbers.append((num, center_y))
                                print(f'[INFO] 识别到题号(含内容): {num}, y坐标: {center_y:.0f}')
                                
                except Exception as e:
                    print(f'[WARN] 解析OCR结果{idx}失败: {str(e)}')
                    continue
        else:
            print(f'[WARN] OCR未识别到任何文本')
        
        # 按题号排序
        question_numbers.sort(key=lambda x: x[0])
        
        # 去重：同一题号只保留一个（取y坐标最小的）
        unique_questions = {}
        for num, y in question_numbers:
            if num not in unique_questions or y < unique_questions[num]:
                unique_questions[num] = y
        
        question_numbers = [(num, y) for num, y in unique_questions.items()]
        question_numbers.sort(key=lambda x: x[0])
        
        print(f'[INFO] 共识别到 {len(question_numbers)} 个题号: {[q[0] for q in question_numbers]}')
        return question_numbers
        
    except Exception as e:
        print(f'[ERROR] 题号识别失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return []

def detect_circles(image_path, total_questions):
    """
    检测图片中的画圈标记，返回圈的中心y坐标列表
    :param image_path: 学生作答图片路径
    :param total_questions: 总题目数量
    :return: 圈的中心y坐标列表
    """
    try:
        print(f'[INFO] 开始检测画圈标记: {image_path}')
        
        # 使用文件流读取图片
        with open(image_path, 'rb') as f:
            img_data = f.read()
        img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
        
        if img is None:
            print(f'[ERROR] 无法读取图片: {image_path}')
            return []
        
        img_height = img.shape[0]
        img_width = img.shape[1]
        
        # 图像增强
        img = enhance_image(img)
        
        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 检测红色和蓝色的圈（教师常用的批改颜色）
        # 红色范围
        lower_red1 = np.array([0, 80, 80])
        upper_red1 = np.array([15, 255, 255])
        lower_red2 = np.array([165, 80, 80])
        upper_red2 = np.array([180, 255, 255])
        
        # 蓝色范围
        lower_blue = np.array([90, 80, 80])
        upper_blue = np.array([140, 255, 255])
        
        # 创建颜色掩码
        mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask_red = mask_red1 | mask_red2
        
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # 合并颜色掩码
        combined_mask = mask_red | mask_blue
        
        # 形态学操作 - 先去除噪点
        kernel_small = np.ones((2, 2), np.uint8)
        kernel_medium = np.ones((4, 4), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel_small)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel_medium)
        
        # 查找轮廓
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 检测圆形/椭圆形轮廓
        circled_ys = []
        min_area = max(300, img_height * img_width * 0.0005)
        max_area = img_height * img_width * 0.1
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # 面积过滤：排除太小和太大的轮廓
            if area < min_area or area > max_area:
                continue
            
            # 获取轮廓的外接矩形
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h
            
            # 计算圆形度
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
            else:
                circularity = 0
            
            # 计算填充率（轮廓面积 / 外接矩形面积）
            rect_area = w * h
            fill_ratio = area / rect_area if rect_area > 0 else 0
            
            # 严格的圆形/椭圆形判断
            is_circle = False
            # 标准圆形：宽高比接近1，圆形度高
            if 0.6 < aspect_ratio < 1.6 and circularity > 0.5 and fill_ratio > 0.4:
                is_circle = True
            # 椭圆形：宽高比略大，圆形度中等
            elif 0.5 < aspect_ratio < 2.0 and circularity > 0.4 and fill_ratio > 0.35:
                is_circle = True
            
            if is_circle:
                # 记录圈的中心y坐标
                center_y = y + h // 2
                circled_ys.append(center_y)
                print(f'[INFO] 检测到画圈标记: 位置({x}, {y}), 中心y={center_y}, 圆形度{circularity:.2f}')
        
        print(f'[INFO] 检测到 {len(circled_ys)} 个画圈标记')
        
        return circled_ys
        
    except Exception as e:
        print(f'[ERROR] 画圈检测失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return []

# 图片对比功能，用于识别教师批改的画圈标记
def compare_images(blank_image_path, answer_image_path, total_questions=6):
    """
    识别学生作答图片中的画圈标记，匹配题号
    :param blank_image_path: 空白试题图片路径（用于识别题号位置）
    :param answer_image_path: 学生作答图片路径
    :param total_questions: 总题目数量，默认6题
    :return: 对错情况字典 {题号: True/False}，以及题号位置列表
    """
    try:
        # 规范化路径格式
        answer_image_path = answer_image_path.replace('/', '\\')
        if blank_image_path:
            blank_image_path = blank_image_path.replace('/', '\\')
        
        # 检查文件是否存在
        if not os.path.exists(answer_image_path):
            print(f'[ERROR] 学生作答图片不存在: {answer_image_path}')
            return {}, []
        
        # 1. 识别题号及其位置（优先使用空白试题图片）
        question_positions = []
        if blank_image_path and os.path.exists(blank_image_path):
            question_positions = detect_question_numbers(blank_image_path)
        
        # 如果空白图片没有识别到题号，尝试用作答图片识别
        if not question_positions:
            question_positions = detect_question_numbers(answer_image_path)
        
        # 根据识别到的题号数量动态调整总题数
        if question_positions:
            max_question = max([q[0] for q in question_positions])
            actual_total = max(total_questions, max_question)
            print(f'[INFO] 识别到最大题号: {max_question}，使用实际总题数: {actual_total}')
        else:
            actual_total = total_questions
        
        # 2. 检测画圈标记的位置
        circled_ys = detect_circles(answer_image_path, actual_total)
        
        # 3. 根据位置匹配，判断哪些题号被圈了
        # 每个画圈只匹配最近的一个题号
        result = {q_num: False for q_num, _ in question_positions}  # 初始化为未画圈
        matched_questions = set()  # 已匹配的题号
        
        for c_y in circled_ys:
            # 找到距离这个圈最近的题号
            min_distance = float('inf')
            closest_q_num = None
            closest_q_y = None
            
            for q_num, q_y in question_positions:
                if q_num > actual_total:
                    continue
                if q_num in matched_questions:
                    continue
                
                distance = abs(c_y - q_y)
                if distance < min_distance:
                    min_distance = distance
                    closest_q_num = q_num
                    closest_q_y = q_y
            
            # 只有距离在阈值内才标记为画圈
            if closest_q_num is not None and min_distance < 60:
                result[closest_q_num] = True
                matched_questions.add(closest_q_num)
                print(f'[INFO] 画圈(y={c_y:.0f})匹配到第{closest_q_num}题(y={closest_q_y:.0f})，距离={min_distance:.0f}')
        
        # 打印结果
        for q_num, q_y in question_positions:
            if q_num > actual_total:
                continue
            is_circled = result.get(q_num, False)
            status = "错误（已画圈）" if is_circled else "正确（未画圈）"
            print(f'[INFO] 第{q_num}题: {status}')
        
        return result, question_positions
        
    except Exception as e:
        print(f'[ERROR] 图片对比失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return {}, []
        
def batch_compare_images(blank_image_paths, answer_image_paths, total_questions=6):
    """
    批量对比图片，识别教师批改的画圈标记
    :param blank_image_paths: 空白试题图片路径列表
    :param answer_image_paths: 学生作答图片路径列表
    :param total_questions: 总题目数量，默认6题
    :return: 对错情况列表，按题号顺序，True表示正确（未画圈），False表示错误（已画圈）
    """
    all_results = {}
    all_question_positions = []
    
    for blank_path, answer_path in zip(blank_image_paths, answer_image_paths):
        if answer_path and answer_path != "无":
            if not os.path.isabs(answer_path):
                answer_path = answer_path.replace('/', '\\')
                answer_path = os.path.join(os.getcwd(), answer_path)
            else:
                answer_path = answer_path.replace('/', '\\')
            
            if blank_path and not os.path.isabs(blank_path):
                blank_path = blank_path.replace('/', '\\')
                blank_path = os.path.join(os.getcwd(), blank_path)
            
            result_dict, question_positions = compare_images(blank_path, answer_path, total_questions)
            all_results.update(result_dict)
            all_question_positions.extend(question_positions)
    
    # 根据识别到的最大题号确定实际总题数
    if all_results:
        max_q_num = max(all_results.keys())
        actual_total = max_q_num  # 只使用识别到的最大题号作为实际总题数
    else:
        actual_total = total_questions
    
    # 按题号顺序生成结果列表
    final_results = [True] * actual_total
    for q_num, is_circled in all_results.items():
        if 1 <= q_num <= actual_total:
            final_results[q_num - 1] = not is_circled  # is_circled=True表示错误，所以取反
    
    print(f'[INFO] 批量识别完成，识别到 {len(all_results)} 个题号的批改结果，实际总题数: {actual_total}')
    return final_results

# 不再尝试导入PaddleOCR，避免ONEDNN错误
paddleocr_available = False
PaddleOCR = None

# OCR配置参数
OCR_CONFIG = {
    # 轻量级模型配置（速度优先）
    'light': {
        'lang': 'ch'
    },
    # 高质量模型配置（质量优先）
    'high': {
        'lang': 'ch'
    }
}



# 图片缓存（避免重复处理）
_image_cache = {}
_cache_lock = threading.Lock()

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_image_cache_key(image_path, quality_mode='light'):
    """生成图片缓存键，包含质量模式"""
    if image_path == "无":
        return "none"
    # 使用文件路径、修改时间和质量模式生成缓存键
    mtime = os.path.getmtime(image_path) if os.path.exists(image_path) else 0
    return f"{image_path}:{mtime}:{quality_mode}"

def preprocess_image_for_ocr(image_path, target_height=640, target_width=640, quality_mode='light'):
    """
    为OCR预处理图片，智能调整大小以平衡速度和质量
    """
    try:
        print(f'[OCR] 开始预处理图片: {image_path}')
        
        # 根据质量模式调整预处理策略
        if quality_mode == 'light':
            # 快速模式：使用较小尺寸和基础预处理
            max_size = 800
            interpolation = cv2.INTER_LINEAR  # 更快的插值方法
        else:
            # 高质量模式：使用较大尺寸和增强预处理
            max_size = 1280
            interpolation = cv2.INTER_CUBIC  # 更高质量的插值方法
        
        print(f'[OCR] 目标尺寸: {target_width}x{target_height}')
        print(f'[OCR] 预处理模式: {quality_mode}')
        
        # 读取图片（使用文件流方式，处理中文路径问题）
        try:
            with open(image_path, 'rb') as f:
                img_data = f.read()
            img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
        except Exception as e:
            print(f'[ERROR] 文件流读取失败: {str(e)}')
            return None
        
        if img is None:
            print(f'[ERROR] 无法解码图片: {image_path}')
            return None
        
        print(f'[OCR] 成功读取图片，原始尺寸: {img.shape}')
        
        # 确保图片是BGR格式
        if len(img.shape) == 2:
            print(f'[OCR] 图片是灰度图，转换为BGR')
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif len(img.shape) == 4:
            print(f'[OCR] 图片是BGRA格式，转换为BGR')
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # 获取原始尺寸
        h, w = img.shape[:2]
        print(f'[OCR] 原始宽高: {w}x{h}')
        
        # 智能调整大小
        if max(h, w) > max_size:
            print(f'[OCR] 图片过大，需要调整大小')
            # 按比例缩放
            scale = min(max_size / h, max_size / w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            print(f'[OCR] 新尺寸: {new_w}x{new_h}')
            # 根据质量模式选择插值方法
            img = cv2.resize(img, (new_w, new_h), interpolation=interpolation)
            print(f'[OCR] 调整大小后尺寸: {img.shape}')
        else:
            print(f'[OCR] 图片尺寸合适，无需调整')
        
        # 快速对比度增强
        if quality_mode == 'light':
            # 快速模式：适度的对比度增强
            img = cv2.convertScaleAbs(img, alpha=1.1, beta=5)
        else:
            # 高质量模式：更强的对比度增强
            img = cv2.convertScaleAbs(img, alpha=1.3, beta=15)
            # 添加高斯模糊以减少噪声
            img = cv2.GaussianBlur(img, (3, 3), 0)
        
        # 自动亮度调整 - 仅在高质量模式下使用
        if quality_mode != 'light':
            print(f'[OCR] 开始自动亮度调整')
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            # 使用自适应直方图均衡化
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l = clahe.apply(l)
            lab = cv2.merge((l, a, b))
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        print(f'[OCR] 预处理完成，最终尺寸: {img.shape}')
        
        return img
    except Exception as e:
        print(f'[ERROR] 图片预处理失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return None


def paddleocr_process(image_path, quality_mode='light'):
    """
    使用RapidOCR进行图片文字识别（替代PaddleOCR以避免ONEDNN错误）
    :param image_path: 图片文件路径
    :param quality_mode: 质量模式 'light'（快速）或 'high'（准确）
    :return: 识别出的文字内容
    """
    # 如果图片路径为"无"，直接返回"无"
    if image_path == "无":
        return "无"

    print(f'[OCR] 接收到的图片路径: {image_path}')
    print(f'[OCR] 路径类型: {"绝对路径" if os.path.isabs(image_path) else "相对路径"}')

    # 处理相对路径，转换为绝对路径
    if not os.path.isabs(image_path):
        # 尝试将相对路径转换为绝对路径
        abs_path = os.path.join(os.getcwd(), image_path)
        print(f'[OCR] 转换为绝对路径: {abs_path}')
        if os.path.exists(abs_path):
            image_path = abs_path
            print(f'[OCR] 转换相对路径为绝对路径成功: {image_path}')
        else:
            # 尝试直接使用相对路径
            print(f'[WARN] 相对路径不存在: {abs_path}')
            # 检查当前工作目录
            print(f'[OCR] 当前工作目录: {os.getcwd()}')
            # 检查 uploads 目录是否存在
            uploads_dir = os.path.join(os.getcwd(), 'uploads')
            print(f'[OCR] uploads 目录是否存在: {os.path.exists(uploads_dir)}')
            if os.path.exists(uploads_dir):
                print(f'[OCR] uploads 目录内容: {os.listdir(uploads_dir)}')
            return "图片不存在"
    else:
        print(f'[OCR] 已经是绝对路径: {image_path}')

    if not os.path.exists(image_path):
        print(f'[WARN] 图片不存在: {image_path}')
        # 检查父目录是否存在
        parent_dir = os.path.dirname(image_path)
        print(f'[OCR] 父目录: {parent_dir}')
        print(f'[OCR] 父目录是否存在: {os.path.exists(parent_dir)}')
        if os.path.exists(parent_dir):
            print(f'[OCR] 父目录内容: {os.listdir(parent_dir)}')
        return "图片不存在"

    print(f'[OCR] 图片文件存在，大小: {os.path.getsize(image_path)} bytes')

    start_time = time.time()

    # 检查缓存
    cache_key = get_image_cache_key(image_path, quality_mode)
    with _cache_lock:
        if cache_key in _image_cache:
            print(f'[OCR] 使用缓存结果: {os.path.basename(image_path)}')
            return _image_cache[cache_key]

    # 检查OCR引擎是否可用
    print(f'[OCR] 检查OCR引擎状态...')
    global ocr_engine
    
    # 如果OCR引擎未初始化，尝试初始化
    if ocr_engine is None:
        print(f'[OCR] OCR引擎未初始化，尝试重新初始化...')
        init_ocr_engine()
    
    if ocr_engine is None:
        print(f'[ERROR] 没有可用的OCR引擎')
        return "OCR引擎初始化失败: 没有可用的OCR引擎"
    
    print(f'[OCR] OCR引擎就绪')

    try:
        print(f'[OCR] 开始处理 ({quality_mode}): {os.path.basename(image_path)}')

        # 根据质量模式选择不同的预处理策略
        if quality_mode == 'light':
            # 快速模式：使用较小尺寸和基础预处理
            print(f'[OCR] 使用快速模式处理')
            processed_img = preprocess_image_for_ocr(image_path, target_height=480, target_width=480, quality_mode=quality_mode)
        else:
            # 高质量模式：使用较大尺寸和增强预处理
            print(f'[OCR] 使用高质量模式处理')
            processed_img = preprocess_image_for_ocr(image_path, target_height=800, target_width=800, quality_mode=quality_mode)

        if processed_img is None:
            print(f'[WARN] 预处理失败，使用文件流读取原图')
            try:
                with open(image_path, 'rb') as f:
                    img_data = f.read()
                processed_img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                print(f'[OCR] 文件流读取结果: {processed_img is not None}')
            except Exception as e:
                print(f'[ERROR] 文件流读取失败: {str(e)}')
                import traceback
                traceback.print_exc()
        else:
            print(f'[OCR] 预处理成功，图片尺寸: {processed_img.shape}')

        if processed_img is None:
            print(f'[WARN] 无法读取图片: {image_path}')
            return "无法读取图片"

        print(f'[INFO] 图片尺寸: {processed_img.shape}')

        # 执行OCR识别
        result = None
        try:
            print(f'[OCR] 正在调用OCR引擎...')
            
            # 使用全局OCR引擎
            if RapidOCR is not None and isinstance(ocr_engine, RapidOCR):
                # 使用RapidOCR
                print(f'[OCR] 使用RapidOCR引擎')
                # RapidOCR可以直接处理图片数据或文件路径
                result, _ = ocr_engine(
                    processed_img, 
                    limit_side_len=1536,  # 增大限制边长，提高大图片识别效果
                    det_limit_side_len=1536,  # 检测限制边长
                    det_boxes_thresh=0.5  # 检测框阈值
                )
                print(f'[OCR] RapidOCR识别成功')
            else:
                # RapidOCR引擎不可用
                print(f'[ERROR] RapidOCR引擎不可用')
                return "OCR引擎初始化失败: RapidOCR引擎不可用"
            
            print(f'[OCR] OCR结果类型: {type(result)}')
            if result:
                print(f'[OCR] OCR结果长度: {len(result)}')
                print(f'[OCR] OCR结果示例: {result[0] if len(result) > 0 else "无"}')
        except Exception as e:
            print(f'[ERROR] OCR识别失败: {str(e)}')
            print(f'[ERROR] 错误类型: {type(e)}')
            import traceback
            print(f'[ERROR] 详细错误信息:')
            traceback.print_exc()
            return f"OCR识别失败: {str(e)}"

        # 检查结果格式
        if result is None:
            print(f'[WARN] OCR返回None')
            return "OCR识别: 无有效内容"

        if not result:
            print(f'[WARN] OCR返回空列表')
            return "OCR识别: 无有效内容"

        # 提取文字结果
        text = ""
        try:
            # 处理RapidOCR的结果格式
            # RapidOCR结果格式: [(box, text, confidence), ...]
            for item in result:
                if len(item) >= 2:
                    line_text = item[1]
                    confidence = item[2] if len(item) >= 3 else 0.0
                    
                    # 根据质量模式调整置信度阈值
                    if quality_mode == 'light':
                        if confidence >= 0.3:  # 降低阈值，提高召回率
                            text += line_text + "\n"
                            print(f'[OCR] 识别到: "{line_text[:50]}..." (置信度: {confidence:.2f})')
                    else:
                        if confidence >= 0.5:  # 高质量模式使用更高阈值
                            text += line_text + "\n"
                            print(f'[OCR] 识别到: "{line_text[:50]}..." (置信度: {confidence:.2f})')
        except Exception as e:
            print(f'[ERROR] 解析OCR结果失败: {str(e)}')
            import traceback
            traceback.print_exc()

        # 清理结果
        text = text.strip()

        # 缓存结果
        if text:
            with _cache_lock:
                _image_cache[cache_key] = text

        if text:
            print(f'[OCR] 最终结果: {text[:100]}...')
        else:
            print(f'[OCR] 未识别到有效文字')

        print(f'[OCR] 总耗时: {time.time() - start_time:.2f}s')

        return text if text else "OCR识别: 无有效内容"
    except Exception as e:
        print(f'[OCR] 处理失败: {os.path.basename(image_path)} - {str(e)}')
        import traceback
        traceback.print_exc()
        return f"OCR处理失败: {str(e)}"

def batch_ocr_process(image_paths, quality_mode='light', max_workers=2):
    """
    批量处理多张图片的OCR
    :param image_paths: 图片路径列表
    :param quality_mode: 质量模式
    :param max_workers: 最大并发数
    :return: 识别结果列表
    """
    if not image_paths:
        return []
    
    start_time = time.time()
    print(f'[OCR] 开始批量处理 {len(image_paths)} 张图片')
    
    results = [None] * len(image_paths)
    
    # 使用单例OCR引擎，避免重复初始化
    ocr_engine = init_ocr_engine()
    print(f'[OCR] 使用单例OCR引擎: {ocr_engine is not None}')
    
    # 顺序处理，避免多线程冲突
    for i, path in enumerate(image_paths):
        if path and path != "无":
            try:
                print(f'[OCR] 处理图片 {i+1}/{len(image_paths)}: {path}')
                results[i] = paddleocr_process(path, quality_mode)
            except Exception as e:
                print(f'[OCR] 处理失败 {i}: {str(e)}')
                results[i] = "OCR处理失败"
        else:
            results[i] = None
    
    print(f'[OCR] 批量处理完成，总耗时: {time.time() - start_time:.2f}s')
    return results

def ocr_process(image_path, quality_mode='light'):
    """
    使用RapidOCR进行图片文字识别（保持原有接口）
    :param image_path: 图片文件路径
    :param quality_mode: 质量模式
    :return: 识别出的文字内容
    """
    return paddleocr_process(image_path, quality_mode)

def call_ai_service(prompt, system_role="teacher"):
    """
    调用外部AI生成评语。
    """
    # TODO: 使用 requests 调用 OpenAI/Claude/文心一言 等接口
    print(f"[AI] Generating with prompt len: {len(prompt)}")
    
    # 模拟AI返回
    return f"【AI生成】这是基于您的要求生成的{system_role}风格评语。分析表明..."

def construct_comment_prompt(student_info, question_text, answer_text, style, feedback=None):
    """构建生成单次评语的提示词"""
    prompt = f"""
    你是一名经验丰富的教师。请根据以下信息为学生生成评语。

    【学生基本信息】：
    姓名：{student_info.name}，年级：{student_info.grade}

    【试题内容】：
    {question_text}

    【学生作答情况（OCR识别）】：
    {answer_text}

    【评语风格要求】：
    {style}
    """

    if feedback:
        prompt += f"\n【注意】：学生之前对评语有反馈：'{feedback}'。请参考此反馈重新生成更合适的评语。"

    prompt += "\n请给出具体的分析、改进建议和鼓励。"
    return prompt

def construct_summary_prompt(student_info, past_comments):
    """
    构建总评提示词
    """
    comments_text = "\n".join([f"- {c.created_at}: {c.content}" for c in past_comments])
    prompt = f"""
    请为学生 {student_info.name} 生成一份阶段性学习总结。

    【历史评语记录】：
    {comments_text}

    请分析学生的进步趋势、薄弱环节，并给出下一阶段的学习规划。
    """
    return prompt

def save_uploaded_file(file, allowed_exts=None):
    """
    保存上传的文件并返回路径
    """
    if not file:
        return None, None

    filename = getattr(file, 'filename', '') or ''
    if not filename:
        return None, None

    # 如果调用方显式指定允许扩展名，则按其校验；否则沿用 ALLOWED_EXTENSIONS
    if allowed_exts is not None:
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if ext not in set(e.lower() for e in allowed_exts):
            return None, None
    else:
        if not allowed_file(filename):
            return None, None

    if file:
        # 提取原始文件名和后缀名
        original_filename = filename
        name, ext = os.path.splitext(original_filename)
        
        # 处理文件名部分，保留原始文件名信息
        safe_name = secure_filename(name)
        
        # 确保文件名部分不为空
        if not safe_name:
            # 如果处理后文件名为空，使用默认名称
            safe_name = "image"
        
        # 确保后缀名格式正确
        if ext:
            # 提取后缀名中的扩展名部分（去掉点号）
            ext_part = ext[1:]  # 去掉开头的点号
            safe_ext_part = secure_filename(ext_part)
            # 重新构造后缀名，确保包含点号
            safe_ext = f".{safe_ext_part}"
        else:
            safe_ext = ""
        
        # 添加时间戳防止文件名重复
        timestamp = int(time.time())
        filename = f"{timestamp}_{safe_name}{safe_ext}"
        
        # 确保文件名格式正确
        if not filename.endswith(safe_ext):
            filename = f"{timestamp}_{safe_name}{ext}"
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # 返回相对路径时使用正斜杠确保URL正确
        relative_path = f'uploads/{filename}'
        return file_path, filename
    return None, None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
NEURALCDM_DIR = os.path.join(PROJECT_ROOT, 'NeuralCDM_plus-main')
NEURALCDM_PYTHON = os.path.join(NEURALCDM_DIR, '.venv', 'Scripts', 'python.exe')
NETKNOWLEDGE_SCRIPT = os.path.join(NEURALCDM_DIR, 'netknowledge_service.py')
NETKNOWLEDGE_MODEL_PATH = os.path.join(NEURALCDM_DIR, 'netknowledge', 'model_epoch18')

def _call_netknowledge_service(text, model_path, top_k=5):
    input_data = {
        'text': text,
        'model_path': model_path,
        'top_k': top_k
    }
    
    try:
        result = subprocess.run(
            [NEURALCDM_PYTHON, NETKNOWLEDGE_SCRIPT],
            cwd=NEURALCDM_DIR,
            input=json.dumps(input_data),
            capture_output=True,
            encoding='utf-8',
            timeout=100
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout)
            if output.get('success'):
                return output['knowledge']
            else:
                print(f'[NetKnowledge] 服务失败: {output.get("error")}')
        else:
            print(f'[NetKnowledge] 服务错误: {result.stderr}')
    except Exception as e:
        print(f'[NetKnowledge] 调用服务失败: {str(e)}')
        import traceback
        traceback.print_exc()
    
    return {}

def load_netknowledge_model(model_path=None):
    if model_path is None:
        model_path = NETKNOWLEDGE_MODEL_PATH
    
    if os.path.exists(model_path):
        print(f'[NetKnowledge] 模型路径: {model_path}')
        return {'path': model_path}
    else:
        print(f'[NetKnowledge] 模型不存在: {model_path}')
        return None

def predict_knowledge_from_text(model, text, top_k=5):
    if model is None:
        return []
    
    model_path = model.get('path') if isinstance(model, dict) else model
    
    knowledge = _call_netknowledge_service(text, model_path, top_k)
    
    results = []
    for k_id, score in knowledge.items():
        results.append({'knowledge_id': int(k_id), 'probability': score})
    
    results.sort(key=lambda x: x['probability'], reverse=True)
    return results

def extract_question_texts_with_knowledge(image_path, ocr_engine, knowledge_model):
    try:
        print(f'[OCR] 开始识别题目文本: {image_path}')
        
        if not os.path.exists(image_path):
            print(f'[WARN] 图片不存在: {image_path}')
            return {}, {}
        
        ocr_result = ocr_engine(image_path)
        
        if isinstance(ocr_result, tuple):
            ocr_result = ocr_result[0]
        
        if not ocr_result or len(ocr_result) == 0:
            print(f'[WARN] OCR未识别到任何文本')
            return {}, {}
        
        texts_with_positions = []
        for item in ocr_result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                box = item[0]
                text = str(item[1]).strip()
                
                if isinstance(box, (list, tuple)) and len(box) >= 2:
                    if isinstance(box[0], (list, tuple)):
                        y_coords = [float(point[1]) for point in box if len(point) >= 2]
                        y = sum(y_coords) / len(y_coords)
                    else:
                        y = float(box[1])
                    texts_with_positions.append((y, text))
        
        texts_with_positions.sort(key=lambda x: x[0])
        
        question_pattern = re.compile(r'^\s*(\d+)\s*[.．)）、,，]?\s*(.*)')
        
        questions = {}
        current_question = None
        current_text = []
        
        for y, text in texts_with_positions:
            match = question_pattern.match(text)
            if match:
                if current_question is not None:
                    questions[current_question] = ''.join(current_text)
                
                current_question = int(match.group(1))
                remaining = match.group(2)
                current_text = [remaining] if remaining else []
            elif current_question is not None:
                current_text.append(text)
        
        if current_question is not None and current_text:
            questions[current_question] = ''.join(current_text)
        
        print(f'[OCR] 识别到 {len(questions)} 道题目')
        for q_num, q_text in questions.items():
            print(f'  第{q_num}题: {q_text[:50]}...' if len(q_text) > 50 else f'  第{q_num}题: {q_text}')
        
        knowledge = {}
        if knowledge_model:
            for q_num, q_text in questions.items():
                knowledge_results = predict_knowledge_from_text(knowledge_model, q_text, top_k=3)
                knowledge[q_num] = [r['knowledge_id'] for r in knowledge_results]
                print(f'  第{q_num}题知识点预测: {knowledge[q_num]}')
        
        return questions, knowledge
    except Exception as e:
        print(f'[ERROR] 题目文本提取失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return {}, {}

def process_question_images_for_knowledge(image_paths, ocr_engine, knowledge_model):
    all_questions = {}
    all_knowledge = {}
    last_question_num = None
    
    for i, image_path in enumerate(image_paths):
        if not image_path or image_path == '无':
            continue
        
        print(f'[INFO] 处理第{i+1}页: {image_path}')
        
        # 获取OCR结果
        ocr_result = None
        try:
            ocr_result = ocr_engine(image_path)
            if isinstance(ocr_result, tuple):
                ocr_result = ocr_result[0]
        except Exception as e:
            print(f'[WARN] 获取OCR结果失败: {str(e)}')
            continue
        
        if not ocr_result or len(ocr_result) == 0:
            print(f'[WARN] OCR未识别到任何文本')
            continue
        
        # 提取文本和位置信息
        texts_with_positions = []
        for item in ocr_result:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                box = item[0]
                text = str(item[1]).strip()
                
                if isinstance(box, (list, tuple)) and len(box) >= 2:
                    if isinstance(box[0], (list, tuple)):
                        y_coords = [float(point[1]) for point in box if len(point) >= 2]
                        y = sum(y_coords) / len(y_coords)
                    else:
                        y = float(box[1])
                    texts_with_positions.append((y, text))
        
        texts_with_positions.sort(key=lambda x: x[0])
        
        question_pattern = re.compile(r'^\s*(\d+)\s*[.．)）、,，]?\s*(.*)')
        
        # 分离前导文本和题目文本
        leading_text = []
        question_texts = []
        found_first_question = False
        
        for y, text in texts_with_positions:
            if not found_first_question and question_pattern.match(text):
                found_first_question = True
                question_texts.append((y, text))
            elif found_first_question:
                question_texts.append((y, text))
            else:
                leading_text.append(text)
        
        # 处理题目文本
        current_question = None
        current_text = []
        page_questions = {}
        
        for y, text in question_texts:
            match = question_pattern.match(text)
            if match:
                # 遇到新的题号
                if current_question is not None:
                    # 保存当前题目
                    page_questions[current_question] = ''.join(current_text)
                
                # 开始新题目
                current_question = int(match.group(1))
                remaining = match.group(2)
                current_text = [remaining] if remaining else []
            elif current_question is not None:
                # 追加到当前题目
                current_text.append(text)
        
        # 保存最后一个题目
        if current_question is not None and current_text:
            page_questions[current_question] = ''.join(current_text)
        
        print(f'[INFO] 第{i+1}页识别到 {len(page_questions)} 道题目: {list(page_questions.keys())}')
        if leading_text:
            print(f'[INFO] 第{i+1}页有 {len(leading_text)} 行前导文本')
        
        # 处理分页逻辑
        if i == 0:
            # 第一页，直接添加所有题目
            for q_num, q_text in page_questions.items():
                all_questions[q_num] = q_text
                all_knowledge[q_num] = []  # 后续会预测知识点
            
            # 更新最后一个题目
            if page_questions:
                last_question_num = max(page_questions.keys())
                print(f'[INFO] 第一页最后一个题目: {last_question_num}')
        else:
            # 非第一页
            # 处理前导文本
            if leading_text and last_question_num is not None:
                # 将前导文本追加到上一个题目
                leading_text_str = ''.join(leading_text)
                all_questions[last_question_num] += leading_text_str
                print(f'[INFO] 将 {len(leading_text)} 行前导文本追加到第{last_question_num}题')
            
            # 添加新题目
            for q_num, q_text in page_questions.items():
                if q_num not in all_questions:
                    all_questions[q_num] = q_text
                    all_knowledge[q_num] = []  # 后续会预测知识点
                    print(f'[INFO] 添加新题目: {q_num}')
            
            # 更新最后一个题目
            if page_questions:
                last_question_num = max(page_questions.keys())
                print(f'[INFO] 当前页面最后一个题目: {last_question_num}')
    
    # 为所有题目预测知识点
    if knowledge_model:
        for q_num, q_text in all_questions.items():
            knowledge_results = predict_knowledge_from_text(knowledge_model, q_text, top_k=3)
            all_knowledge[q_num] = [r['knowledge_id'] for r in knowledge_results]
            print(f'[INFO] 为第{q_num}题预测知识点: {all_knowledge[q_num]}')
    
    return all_questions, all_knowledge

def extract_knowledge_from_ocr_text(ocr_text, knowledge_model):
    """
    从OCR识别的文本中提取题目并预测知识点
    :param ocr_text: OCR识别的文本
    :param knowledge_model: 知识点模型
    :return: (题目字典, 知识点字典)
    """
    if not ocr_text or not knowledge_model:
        return {}, {}
    
    try:
        print(f'[Knowledge] 从OCR文本中提取题目...')
        
        # 按行分割文本
        lines = ocr_text.split('\n')
        
        question_pattern = re.compile(r'^\s*(\d+)\s*[.．)）、,，]?\s*(.*)')
        
        questions = {}
        current_question = None
        current_text = []
        
        for line in lines:
            match = question_pattern.match(line)
            if match:
                if current_question is not None:
                    questions[current_question] = ''.join(current_text)
                
                current_question = int(match.group(1))
                remaining = match.group(2)
                current_text = [remaining] if remaining else []
            elif current_question is not None:
                current_text.append(line)
        
        if current_question is not None and current_text:
            questions[current_question] = ''.join(current_text)
        
        print(f'[Knowledge] 识别到 {len(questions)} 道题目')
        for q_num, q_text in questions.items():
            print(f'  第{q_num}题: {q_text[:50]}...' if len(q_text) > 50 else f'  第{q_num}题: {q_text}')
        
        # 预测知识点
        knowledge = {}
        for q_num, q_text in questions.items():
            knowledge_results = predict_knowledge_from_text(knowledge_model, q_text, top_k=3)
            knowledge[q_num] = [r['knowledge_id'] for r in knowledge_results]
            print(f'  第{q_num}题知识点预测: {knowledge[q_num]}')
        
        return questions, knowledge
    except Exception as e:
        print(f'[ERROR] 从OCR文本提取知识点失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return {}, {}

_knowledge_model = None

def get_knowledge_model():
    global _knowledge_model
    if _knowledge_model is None:
        _knowledge_model = load_netknowledge_model()
    return _knowledge_model

_knowledge_mapping = None

def load_knowledge_mapping():
    global _knowledge_mapping
    if _knowledge_mapping is not None:
        return _knowledge_mapping
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    mapping_file = os.path.join(base_path, 'models', 'knowledge_mapping.txt')
    
    print(f'[Knowledge] 加载知识点映射: {mapping_file}')
    
    if not os.path.exists(mapping_file):
        print(f'[ERROR] 知识点映射文件不存在: {mapping_file}')
        _knowledge_mapping = {}
        return _knowledge_mapping
    
    try:
        mapping = {}
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '：' in line:
                    parts = line.split('：', 1)
                    if len(parts) == 2:
                        k_id = parts[0].strip()
                        k_name = parts[1].strip()
                        mapping[k_id] = k_name
                        mapping[int(k_id)] = k_name  
        
        _knowledge_mapping = mapping
        print(f'[Knowledge] 成功加载 {len(mapping)} 个知识点映射')
        return mapping
    except Exception as e:
        print(f'[ERROR] 加载知识点映射失败: {e}')
        _knowledge_mapping = {}
        return {}

def get_knowledge_names(knowledge_ids):
    mapping = load_knowledge_mapping()
    result = {}
    for k_id in knowledge_ids:
        if isinstance(k_id, int):
            result[str(k_id)] = mapping.get(k_id, mapping.get(str(k_id), f'知识点{k_id}'))
        else:
            result[k_id] = mapping.get(k_id, mapping.get(int(k_id) if k_id.isdigit() else k_id, f'知识点{k_id}'))
    return result

def clean_think_tags(text):
    """移除 <think> 和 </think> 标签及其内容"""
    import re
    if not text:
        return text
    result = text
    # 首先移除完整的 <think>...</think> 标签对
    for _ in range(10):
        old = result
        result = re.sub(r'<think>[\s\S]*?</think>', '', result)
        if old == result:
            break
    # 然后移除单独的 <think> 或 </think> 标签
    result = re.sub(r'</?think>', '', result)
    # 清理多余的空白字符
    result = re.sub(r'\s+', ' ', result).strip()
    return result

def build_diagnosis_data(student_name, exercise_ids, predictions, actual_scores, knowledge_codes):
    valid_predictions = []
    valid_actuals = []
    valid_knowledge = []
    
    for pred, actual, kc in zip(predictions, actual_scores, knowledge_codes):
        if actual != -1:
            valid_predictions.append(pred)
            valid_actuals.append(actual)
            valid_knowledge.append(kc)
    
    if not valid_predictions:
        return None
    
    average_prediction = sum(valid_predictions) / len(valid_predictions)
    accuracy = sum(valid_actuals) / len(valid_actuals)
    
    knowledge_mastery = {}
    all_knowledge_ids = set()
    
    for kc, pred, actual in zip(valid_knowledge, valid_predictions, valid_actuals):
        for k_id in kc:
            k_str = str(k_id)
            if k_str not in knowledge_mastery:
                knowledge_mastery[k_str] = {
                    'predicted_mastery': [],
                    'actual_mastery': []
                }
            knowledge_mastery[k_str]['predicted_mastery'].append(pred)
            knowledge_mastery[k_str]['actual_mastery'].append(actual)
            all_knowledge_ids.add(k_id)
    
    for k_str in knowledge_mastery:
        preds = knowledge_mastery[k_str]['predicted_mastery']
        actuals = knowledge_mastery[k_str]['actual_mastery']
        avg_pred = sum(preds) / len(preds)
        avg_actual = sum(actuals) / len(actuals)
        knowledge_mastery[k_str] = {
            'predicted_mastery': round(avg_pred, 4),
            'actual_mastery': avg_actual,
            'performance_gap': round(avg_pred - avg_actual, 4)
        }
    
    strengths = []
    weaknesses = []
    for k_str, mastery in knowledge_mastery.items():
        if mastery['actual_mastery'] >= 0.7:
            strengths.append(int(k_str))
        elif mastery['actual_mastery'] < 0.5:
            weaknesses.append(int(k_str))
    
    diagnosis_data = {
        'student_name': student_name,
        'average_prediction': round(average_prediction, 4),
        'accuracy': round(accuracy, 4),
        'knowledge_mastery': knowledge_mastery,
        'strengths': strengths,
        'weaknesses': weaknesses
    }
    
    knowledge_names = get_knowledge_names(all_knowledge_ids)
    
    return diagnosis_data, knowledge_names

def call_dify_agent(diagnosis_data, knowledge_names, dify_api='http://localhost:83/v1', api_key=None):
    import requests
    import json
    
    if api_key is None:
        from config import Config
        api_key = getattr(Config, 'DIFY_COMMENT_API_KEY', '')
        print(f'[Dify] 使用评语生成API密钥: {api_key[:10]}...')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 构建 inputs 数据
    inputs_data = {
        'diagnosis': diagnosis_data,
        'knowledge_names': knowledge_names,
        'more': {}
    }
    
    # 构建请求 payload，将 inputs 作为 query 发送
    payload = {
        'query': json.dumps(inputs_data, ensure_ascii=False),
        'inputs': inputs_data,
        'response_mode': 'streaming',  # 改为流式处理
        'user': 'teacher'
    }
    
    # 打印 payload 结构以调试
    print(f'[Dify] 构建的 payload: {json.dumps(payload, ensure_ascii=False)}')
    
    print(f'[Dify] 调用Dify智能体: {dify_api}')
    
    debug_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dify_request_debug.txt')
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("发送给Dify智能体的请求内容\n")
        f.write("=" * 60 + "\n\n")
        f.write("API地址: " + dify_api + "/chat-messages\n\n")
        f.write("Headers:\n")
        headers_debug = {k: v for k, v in headers.items()}
        headers_debug['Authorization'] = 'Bearer ' + '*' * 20  # 隐藏密钥
        f.write(json.dumps(headers_debug, ensure_ascii=False, indent=2) + "\n\n")
        f.write("Payload:\n")
        f.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n\n")
        f.write("诊断数据 (格式化):\n")
        f.write(json.dumps(diagnosis_data, ensure_ascii=False, indent=2) + "\n\n")
        f.write("知识点名称:\n")
        f.write(json.dumps(knowledge_names, ensure_ascii=False, indent=2) + "\n")
    print(f'[Dify] 请求内容已保存到: {debug_file}')
    
    try:
        print(f'[Dify] 正在发送流式请求...')
        response = requests.post(
            f'{dify_api}/chat-messages',
            headers=headers,
            json=payload,
            stream=True,  # 开启流式请求
            timeout=500  # 流式请求的超时时间
        )
        
        print(f'[Dify] 响应状态码: {response.status_code}')
        if response.status_code == 200:
            print(f'[Dify] 开始接收流式响应...')
            full_answer = ""
            for chunk in response.iter_lines():
                if chunk:
                    # 处理每个数据块
                    chunk_str = chunk.decode('utf-8')
                    # 检查是否是数据块开头
                    if chunk_str.startswith('data: '):
                        data_str = chunk_str[6:]  # 去掉 'data: ' 前缀
                        if data_str == '[DONE]':
                            break  # 流结束
                        try:
                            data = json.loads(data_str)
                            # 提取文本内容
                            if 'answer' in data:
                                chunk_text = data['answer']
                                full_answer += chunk_text
                        except json.JSONDecodeError:
                            print(f'[Dify] 解析数据块失败: {data_str}')
            
            if full_answer:
                # 对完整文本进行最终清理，确保所有 <think></think> 标签都被去除
                final_clean_answer = clean_think_tags(full_answer)
                print(f'[Dify] 原始文本: {full_answer[:100]}...')
                print(f'[Dify] 清理后文本: {final_clean_answer[:100]}...')
                print(f'[Dify] 成功获取完整评语: {final_clean_answer[:50]}...')
                return final_clean_answer
            else:
                print(f'[Dify] 未接收到有效内容')
                return None
        else:
            print(f'[Dify] API调用失败: {response.status_code} - {response.text}')
            return None
    except requests.exceptions.Timeout as e:
        print(f'[ERROR] 调用Dify智能体超时: {e}')
        print(f'[ERROR] 请检查Dify服务是否正常运行')
        return None
    except requests.exceptions.ConnectionError as e:
        print(f'[ERROR] 连接Dify服务失败: {e}')
        print(f'[ERROR] 请检查网络连接和Dify服务状态')
        return None
    except Exception as e:
        print(f'[ERROR] 调用Dify智能体失败: {e}')
        import traceback
        traceback.print_exc()
        return None

def generate_comment_with_dify(student_name, exercise_ids, predictions, actual_scores, knowledge_codes, dify_api='http://localhost:83/v1'):
    print(f'\n{"="*60}')
    print(f'[Dify] 开始生成基于神经认知诊断的评语')
    print(f'{"="*60}')
    
    result = build_diagnosis_data(student_name, exercise_ids, predictions, actual_scores, knowledge_codes)
    if result is None:
        print(f'[ERROR] 无法构建诊断数据')
        return None
    
    diagnosis_data, knowledge_names = result
    
    print(f'[Dify] 诊断数据:')
    print(f'  学生: {diagnosis_data["student_name"]}')
    print(f'  平均预测: {diagnosis_data["average_prediction"]}')
    print(f'  正确率: {diagnosis_data["accuracy"]}')
    print(f'  知识点掌握: {len(diagnosis_data["knowledge_mastery"])}个知识点')
    print(f'  优势: {diagnosis_data["strengths"]}')
    print(f'  薄弱: {diagnosis_data["weaknesses"]}')
    print(f'[Dify] 知识点名称: {knowledge_names}')
    
    comment = call_dify_agent(diagnosis_data, knowledge_names, dify_api)
    
    if comment:
        print(f'[Dify] 生成的评语: {comment[:100]}...')
    else:
        print(f'[Dify] 评语生成失败')
    
    print(f'{"="*60}\n')
    return comment
