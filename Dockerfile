FROM python:3.11-slim

WORKDIR /app

# 更换为国内源（加速 apt-get）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 安装系统依赖（包括Tesseract OCR、MySQL客户端和其他必要的库）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    python3-dev \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    libmysqlclient-dev \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 先只复制 requirements.txt（利用 Docker 缓存层）
COPY backend/requirements.txt /app/backend/requirements.txt

# 安装 Python 依赖（使用国内源加速，添加错误处理）
RUN pip install --no-cache-dir -r /app/backend/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ || \
    (echo "尝试使用官方源..." && pip install --no-cache-dir -r /app/backend/requirements.txt)

# 复制所有代码（使用 .dockerignore 过滤无用文件）
COPY backend/ /app/backend/
COPY NeuralCDM_plus-main/ /app/NeuralCDM_plus-main/

# 设置工作目录
WORKDIR /app/backend

# 启动应用
CMD ["python", "run.py"]