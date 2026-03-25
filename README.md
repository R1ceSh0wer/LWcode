# LWcode 项目启动指南

## 项目简介

LWcode 是一个基于 AI 的智能教育系统，集成了神经认知诊断模型、OCR 识别、知识图谱等功能，为教师和学生提供个性化的教育服务。

## 技术栈

- **前端**：Vue 3 + Vite + TailwindCSS + vis.js
- **后端**：Flask + SQLAlchemy + MySQL
- **AI 模型**：NeuralCDM+ (PyTorch)
- **OCR**：RapidOCR + Tesseract
- **知识图谱**：Neo4j

## 项目结构

```
LWcode/
├── backend/          # 后端Flask应用
│   ├── app/          # 应用核心代码
│   ├── OCR_models/   # OCR模型文件
│   ├── archives/     # 模型存档
│   ├── uploads/      # 上传文件
│   ├── run.py        # 后端启动文件
│   └── config.py     # 配置文件
├── frontend/         # 前端Vue应用
│   ├── src/          # 前端源代码
│   └── package.json  # 前端依赖
├── NeuralCDM_plus-main/  # 神经认知诊断模型
├── Dify知识库/        # Dify知识库源文件
└── README.md         # 项目说明文档
```

## 环境要求

### 前端环境
- Node.js 16+
- npm

### 后端环境
- Python 3.11+（建议使用项目.venv虚拟环境）
- PyTorch
- Flask
- Neo4j 数据库
- MySQL 数据库

## 快速开始

### 1. 安装前端依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 2. 安装后端依赖

```bash
# 进入后端目录
cd backend

# 安装Python依赖（建议使用虚拟环境）
pip install -r requirements.txt

# 如果没有requirements.txt文件，请安装以下依赖：
pip install flask flask-cors sqlalchemy pymysql torch rapidocr-openvino pytesseract neo4j-driver numpy Pillow requests python-dotenv
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env`，并根据实际情况修改配置：

```bash
# 进入后端目录
cd backend

# 复制环境变量文件
copy .env.example .env
```

编辑 `.env` 文件，配置以下内容：

```env
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=weijinqi20040811
DB_NAME=test

# Neo4j数据库配置
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=weijinqi20040811

# 应用配置
SECRET_KEY=weijinqi20040811

# 百度AI配置 (可选)
APP_ID=your-app-id
API_KEY=your-api-key
SECRET_KEY_BAIDU=your-secret-key

# Tesseract OCR配置 (可选)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Dify AI配置
DIFY_API_KEY=app-rS3rKf3JVLMVdYCnAcsoF141
DIFY_COMMENT_API_KEY=app-Hrra4alKn8tM7nOwlYnQ8WyR
```

### 4. 启动服务

#### 启动后端服务

```bash
# 进入后端目录
cd backend

# 启动后端服务
python run.py
```

后端服务将在 `http://127.0.0.1:5000` 运行。

#### 启动前端服务

```bash
# 进入前端目录
cd frontend

# 启动前端开发服务器
npm run dev
```

前端服务将在 `http://127.0.0.1:5173` 运行。

### 5. 访问应用

打开浏览器，访问 `http://127.0.0.1:5173` 即可进入应用。

## 核心功能

### 教师端
- 专栏管理：创建、编辑专栏
- 批量生成评语：基于学生答题情况自动生成个性化评语
- 学习资源管理：上传、分发学习资源
- 知识图谱构建：创建和管理知识图谱

### 学生端
- 查看评语：查看教师生成的个性化评语
- 学习资源：查看教师分发的学习资源
- 知识图谱：查看知识图谱和知识点关联

## 模型使用

### 神经认知诊断模型

1. 确保 `NeuralCDM_plus-main` 目录存在
2. 后端会自动加载模型进行预测

### OCR 模型

1. 确保 `backend/OCR_models` 目录下有正确的模型文件
2. 系统会自动使用 OCR 识别学生上传的图片

## 常见问题

### 1. 后端启动失败

- 检查 NeuralCDM_plus-main 是否按照其README.md进行配置，建议使用虚拟环境进行解释器分离
- 检查依赖是否安装完整
- 检查 MySQL 数据库是否运行，并按照mysqlcreate.txt创建数据库
- 检查 Neo4j 数据库是否运行

### 2. 前端启动失败

- 检查 Node.js 版本是否为 16+
- 检查依赖是否安装完整

### 3. 模型预测失败

- 检查 `NeuralCDM_plus-main` 目录是否存在
- 检查模型文件是否完整

### 4. OCR 识别失败

- 检查 `OCR_models` 目录下是否有正确的模型文件

## 开发说明

### 前端开发

```bash
# 进入前端目录
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 后端开发

```bash
# 进入后端目录
cd backend

# 启动开发服务器
python run.py
```

## 部署说明

### 生产环境部署

1. 构建前端生产版本：
   ```bash
   cd frontend
   npm run build
   ```

2. 将构建结果复制到后端静态文件目录

3. 启动后端服务：
   ```bash
   cd backend
   python run.py
   ```

## 许可证

MIT License

## 致谢

本项目使用了 NeuralCDM+ 代码，该代码基于以下论文：

- Wang, F., Liu, Q., Chen, E., Huang, Z., Chen, Y., Yin, Y., Huang, Z., & Wang, S. (2020). Neural Cognitive Diagnosis for Intelligent Education Systems. In Thirty-Fourth AAAI Conference on Artificial Intelligence.

- Wang, F., Liu, Q., Chen, E., Huang, Z., Yin, Y., Wang, S., & Su, Y. (2022). NeuralCD: A General Framework for Cognitive Diagnosis. IEEE Transactions on Knowledge and Data Engineering.

原始代码来源：[NeuralCDM_plus](https://github.com/bigdata-ustc/Neural_Cognitive_Diagnosis-NeuralCD)

## 联系信息

如有问题，请联系项目维护者。