import os
import subprocess
import sys

def convert_to_fp16():
    # 1. 定义原始模型路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    
    det_onnx = os.path.join(models_dir, "det_v5.onnx")
    rec_onnx = os.path.join(models_dir, "rec_v5.onnx")

    # 2. 定义输出目录 (创建 dedicated 的 OpenVINO 目录)
    output_dir = os.path.join(models_dir, "openvino_fp16")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"🚀 开始转换模型至 OpenVINO FP16 格式 (适配 Intel NPU)...")
    print(f"📂 输出目录: {output_dir}\n")

    # 3. 构造转换命令 (使用 mo 工具)
    # 核心参数: --compress_to_fp16 (这是 NPU 提速的关键)
    cmds = [
        # 转换检测模型 (DET)
        f'mo --input_model "{det_onnx}" --output_dir "{output_dir}" --model_name det_v5_fp16 --compress_to_fp16',
        
        # 转换识别模型 (REC)
        f'mo --input_model "{rec_onnx}" --output_dir "{output_dir}" --model_name rec_v5_fp16 --compress_to_fp16'
    ]

    for cmd in cmds:
        print(f"正在执行: {cmd}")
        try:
            # 调用命令行工具
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError:
            print("❌ 转换失败！请确保已安装: pip install openvino-dev")
            return

    print("\n✅ 转换成功！")
    print("生成文件:")
    print(f"  - {os.path.join(output_dir, 'det_v5_fp16.xml')} (结构)")
    print(f"  - {os.path.join(output_dir, 'det_v5_fp16.bin')} (权重)")
    print(f"  - {os.path.join(output_dir, 'rec_v5_fp16.xml')}")
    print(f"  - {os.path.join(output_dir, 'rec_v5_fp16.bin')}")

if __name__ == "__main__":
    convert_to_fp16()