# 使用官方 Python 镜像作为基础
FROM python:3.9-slim-buster

# 设置工作目录
WORKDIR /app

# 复制 backend 文件夹下的所有内容到容器的 /app 目录
# 确保所有模型文件、weights 等都在这个目录结构下
COPY . /app/backend/

# 将 backend 目录设置为 PYTHONPATH，以便内部模块可以正确导入
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# 安装 Python 依赖
# 假设 requirements.txt 也在 backend 目录下
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 如果您的模型有额外的系统依赖（例如 OpenVINO），需要在这里安装
# 例如：
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libgl1-mesa-glx libgtk2.0-0 && rm -rf /var/lib/apt/lists/*

# 暴露 Flask 应用程序运行的端口
EXPOSE 5000

# 启动 Gunicorn WSGI 服务器来运行 Flask 应用
# 假设您的 Flask 应用实例在 run.py 文件中名为 'app'
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
