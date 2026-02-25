import sys, os, cv2, yaml, time, math
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QLabel, QFileDialog, QTextEdit)
from PyQt6.QtGui import QImage, QPixmap, QTextCharFormat, QColor, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# 引入 NPU 加速引擎
from rapidocr_openvino import RapidOCR


class TextMerger:
    def __init__(self):
        pass

    def process_layout(self, ocr_results):
        """
        1. 物理分列
        2. 识别大小字/双行夹注
        3. 合并连续的大字框
        4. 生成最终排序列表
        """
        if not ocr_results: return []

        # --- 第一步：数据清洗与基本属性计算 ---
        boxes = []
        all_widths = []
        for line in ocr_results:
            pts = np.array(line[0], np.int32)
            x_min, x_max = np.min(pts[:, 0]), np.max(pts[:, 0])
            y_min, y_max = np.min(pts[:, 1]), np.max(pts[:, 1])
            w = x_max - x_min
            h = y_max - y_min
            
            all_widths.append(w)
            boxes.append({
                'box': [x_min, y_min, x_max, y_max],
                'cx': (x_min + x_max) / 2,
                'cy': (y_min + y_max) / 2,
                'w': w, 'h': h,
                'txt': line[1],
                'raw_pts': pts
            })

        # 计算大字的标准宽度 (取中位数或较宽的平均值)
        if not all_widths: return []
        median_w = np.median(all_widths)
        
        # --- 第二步：物理列聚类 (X轴) ---
        # 按 X 从大到小（从右向左）排序
        boxes.sort(key=lambda b: b['cx'], reverse=True)
        
        columns = []
        current_col = []
        
        for box in boxes:
            if not current_col:
                current_col.append(box)
                continue
            
            # 获取当前列的平均 X 中心
            col_avg_cx = np.mean([b['cx'] for b in current_col])
            
            # 阈值：如果 X 偏差小于 0.7 倍字宽，归入同一列
            if abs(box['cx'] - col_avg_cx) < (median_w * 0.7):
                current_col.append(box)
            else:
                columns.append(current_col)
                current_col = [box]
        if current_col: columns.append(current_col)

        # --- 第三步：列内处理 (合并大字 + 排序小字) ---
        final_merged_list = []

        # 对每一列进行处理
        for col in columns:
            # 1. 判定该列内部的大小字属性
            # 先按 Y 从上到下排
            col.sort(key=lambda b: b['cy'])
            
            # 标记属性
            for b in col:
                # 判定逻辑：宽度明显小于标准宽(0.75倍)，或者高度极小，或者是双行结构
                # 简单判定：宽 < 0.75 * median_w
                if b['w'] < (median_w * 0.75):
                    b['type'] = 'small'
                else:
                    b['type'] = 'large'

            # 2. 核心逻辑：合并连续的大字 (Large)
            # 我们将创建一个新的列表 new_col_items
            new_col_items = []
            
            # 临时变量，用于积攒待合并的大字
            pending_large = None
            
            # 辅助函数：执行合并
            def merge_box(b1, b2):
                x1 = min(b1['box'][0], b2['box'][0])
                y1 = min(b1['box'][1], b2['box'][1])
                x2 = max(b1['box'][2], b2['box'][2])
                y2 = max(b1['box'][3], b2['box'][3])
                return {
                    'box': [x1, y1, x2, y2],
                    'cx': (x1+x2)/2, 'cy': (y1+y2)/2,
                    'w': x2-x1, 'h': y2-y1,
                    'txt': b1['txt'] + b2['txt'], # 文本拼接
                    'type': 'large'
                }

            # 处理列内双行夹注的特殊排序 (先右后左)
            # 我们使用一个子循环来处理"同一行高"的元素
            # 但为了简化合并逻辑，我们先处理合并，排序在绘制时通过索引体现即可? 
            # 不，古籍阅读顺序必须先排好。
            
            # 双行重排逻辑：检查是否有 Y 高度重叠且 X 不同的项
            # 简单的冒泡修正：如果 b[i] 和 b[i+1] Y 接近，且 b[i].x < b[i+1].x (左在右前)，则交换
            for i in range(len(col)-1):
                curr = col[i]
                next_b = col[i+1]
                # Y 重叠判定
                y_overlap = min(curr['box'][3], next_b['box'][3]) - max(curr['box'][1], next_b['box'][1])
                if y_overlap > 0: # 有重叠
                    # 如果当前在左边 (X较小)，后面在右边 (X较大)，这违反了先读右边的规则
                    if curr['cx'] < next_b['cx']:
                        col[i], col[i+1] = col[i+1], col[i]

            # 开始合并循环
            for item in col:
                if item['type'] == 'large':
                    if pending_large is None:
                        pending_large = item
                    else:
                        # 尝试合并：判断垂直距离是否够近
                        # 古籍字距通常很近。如果Y距离太远（比如隔了很远的空白），也不合并
                        dist = item['box'][1] - pending_large['box'][3]
                        if dist < median_w * 1.5: # 允许 1.5 倍字高的间距合并
                            pending_large = merge_box(pending_large, item)
                        else:
                            # 距离太远，断开
                            new_col_items.append(pending_large)
                            pending_large = item
                else:
                    # 遇到小字 (Small)
                    # 1. 先把积攒的大字结算了
                    if pending_large:
                        new_col_items.append(pending_large)
                        pending_large = None
                    
                    # 2. 小字直接加入，不合并
                    new_col_items.append(item)
            
            # 循环结束，如果有剩下的大字
            if pending_large:
                new_col_items.append(pending_large)
            
            final_merged_list.extend(new_col_items)

        return final_merged_list

# ==========================================
# 线程与UI逻辑
# ==========================================
class AnalysisThread(QThread):
    result_ready = pyqtSignal(list, float, np.ndarray)

    def __init__(self, engine, image_path):
        super().__init__()
        self.engine = engine
        self.image_path = image_path
        self.merger = TextMerger()

    def run(self):
        start_time = time.time()
        img = cv2.imread(self.image_path)
        if img is None: return
        
        # 1. NPU OCR 识别
        ocr_result, _ = self.engine(img, limit_side_len=1280)
        
        # 2. 智能合并与排序
        merged_boxes = self.merger.process_layout(ocr_result)
        
        elapse = time.time() - start_time
        self.result_ready.emit(merged_boxes, elapse, img)

class LayoutWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("古籍文本识别 - 智能排版版")
        self.resize(1600, 1000)
        self.setup_engine()
        self.init_ui()

    def setup_engine(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(base_path, "models")
        ov_dir = os.path.join(models_dir, "openvino_fp16")
        det_path = os.path.join(ov_dir, "det_v5_fp16.xml")
        rec_path = os.path.join(ov_dir, "rec_v5_fp16.xml")
        dict_path = os.path.join(models_dir, "temp_dict.txt")
        
        if not os.path.exists(det_path):
            det_path = os.path.join(models_dir, "det_v5.onnx")
            rec_path = os.path.join(models_dir, "rec_v5.onnx")

        self.engine = RapidOCR(
            det_model_path=det_path, rec_model_path=rec_path,
            rec_keys_path=dict_path, intra_op_num_threads=14
        )

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # 左侧
        left_p = QVBoxLayout()
        self.img_label = QLabel("请载入古籍\n[大字合并 | 夹注区分 | 序号标注]")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet("background:#1a1a1a; color:#00ffbf; border:2px solid #444;")
        self.img_label.mousePressEvent = lambda e: self.select_img()
        left_p.addWidget(self.img_label, 7)
        
        self.btn = QPushButton("开始识别与排版")
        self.btn.setFixedHeight(60)
        self.btn.setEnabled(False)
        self.btn.clicked.connect(self.run_analysis)
        self.btn.setStyleSheet("font-size:18px; font-weight:bold; color: #1a1a1a; background: #00ffbf;")
        left_p.addWidget(self.btn, 1)
        layout.addLayout(left_p, 6)
        
        # 右侧：改为富文本展示
        self.txt_out = QTextEdit()
        self.txt_out.setReadOnly(True)
        self.txt_out.setStyleSheet("""
            QTextEdit {
                background: #fdf6e3;
                border-left: 10px solid #d4c4b5;
                padding: 20px;
            }
        """)
        layout.addWidget(self.txt_out, 4)
        self.curr_path = None

    def select_img(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.jpg *.png *.tif)")
        if path:
            self.curr_path = path
            self.img_label.setPixmap(QPixmap(path).scaled(self.img_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
            self.btn.setEnabled(True)

    def run_analysis(self):
        self.btn.setEnabled(False)
        self.txt_out.setHtml("<h3 style='color:#555'>正在进行 NPU 识别与结构化重组...</h3>")
        self.worker = AnalysisThread(self.engine, self.curr_path)
        self.worker.result_ready.connect(self.show_results)
        self.worker.start()

    def show_results(self, results, t, img):
        self.btn.setEnabled(True)
        self.txt_out.clear()
        draw_img = img.copy()
        
        # 构建 HTML 字符串
        html_content = "<div style='font-family: Kaiti, SimSun; line-height: 1.8;'>"
        
        for idx, item in enumerate(results):
            # 1. 坐标数据清洗
            box_data = np.array(item['box'], dtype=np.float32).astype(int).flatten()
            x1, y1, x2, y2 = box_data[:4]
            
            # 2. 视觉标注
            # 大字用绿色框，小字用紫色框
            is_large = (item['type'] == 'large')
            color_bgr = (0, 180, 0) if is_large else (180, 0, 180) # BGR
            thickness = 2 if is_large else 1
            
            cv2.rectangle(draw_img, (x1, y1), (x2, y2), color_bgr, thickness)
            
            # 序号标注 (红色)
            # 放在框的右上角
            cv2.putText(draw_img, str(idx+1), (x2, y1+15), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6 if is_large else 0.4, (0, 0, 255), 2)
            
            # 3. 文本生成 (HTML)
            txt = item['txt']
            if is_large:
                # 大字样式：黑色，大号
                html_content += f"<span style='font-size:24px; color:#000000; font-weight:bold;'>{txt}</span><br>"
            else:
                # 小字样式：深红/赭石色，小号，且不换行（或者根据需求，小字通常紧随其后）
                # 您的需求是：区别于大字。这里我们用 span 包裹
                # 注意：如果是双行夹注，通常是嵌在大字中间。
                # 视觉上我们在文本框里用【】或者颜色区分
                html_content += f"&nbsp;<span style='font-size:16px; color:#8B0000;'>[{txt}]</span>&nbsp;"

        html_content += "</div>"
        
        # 更新界面
        self.txt_out.setHtml(html_content)
        self.txt_out.append(f"\n========\n耗时: {t:.3f}s | 共识别 {len(results)} 个逻辑块")
        
        # 显示图片
        h, w, c = draw_img.shape
        qimg = QImage(draw_img.data, w, h, c*w, QImage.Format.Format_BGR888)
        self.img_label.setPixmap(QPixmap.fromImage(qimg).scaled(self.img_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = LayoutWindow()
    w.show()
    sys.exit(app.exec())