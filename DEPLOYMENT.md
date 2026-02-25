# 部署文档

## 项目概述

这是一个基于 Flask + Vue 3 的智能教学辅助系统，用于教师和学生进行教学和学习活动。系统包含知识图谱、AI 评语生成器、资源面板等核心功能。

## 技术栈

### 后端
- **Flask**：Python Web 框架
- **Flask-CORS**：处理跨域请求
- **Python 3.8+**：编程语言

### 前端
- **Vue 3**：JavaScript 框架
- **Vue Router**：路由管理
- **Pinia**：状态管理
- **Axios**：HTTP 客户端
- **Vite**：构建工具

## 环境要求

### 后端
- Python 3.8 或更高版本
- pip 包管理工具

### 前端
- Node.js 16 或更高版本
- npm 或 yarn 包管理工具

## 部署步骤

### 1. 克隆项目

```bash
git clone <项目地址>
cd <项目目录>
```

### 2. 后端部署

#### 2.1 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 2.2 配置环境变量

创建 `.env` 文件并添加必要的环境变量：

```bash
# Flask 配置
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your_secret_key_here

# 数据库配置（如果需要）
DATABASE_URL=sqlite:///app.db
```

#### 2.3 启动后端服务

##### 开发环境

```bash
flask run
```

##### 生产环境（使用 Gunicorn）

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 3. 前端部署

#### 3.1 安装依赖

```bash
cd frontend
npm install
```

#### 3.2 构建生产版本

```bash
npm run build
```

构建产物将生成在 `dist` 目录中。

#### 3.3 部署前端静态文件

##### 使用 Nginx

1. 安装 Nginx
2. 配置 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        root /path/to/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

3. 启动 Nginx

```bash
systemctl start nginx
```

### 4. 访问系统

部署完成后，可以通过以下地址访问系统：

- 前端：http://your_domain.com
- 后端 API：http://your_domain.com/api

## 开发环境设置

### 后端开发

```bash
cd backend
flask run --debug
```

### 前端开发

```bash
cd frontend
npm run dev
```

## 项目结构

```
.
├── backend/              # 后端代码
│   ├── app.py            # Flask 主应用
│   ├── requirements.txt  # 依赖列表
│   └── README.md         # 后端文档
├── frontend/             # 前端代码
│   ├── src/              # 源代码
│   ├── index.html        # 入口 HTML
│   ├── package.json      # 依赖配置
│   ├── vite.config.js    # Vite 配置
│   └── README.md         # 前端文档
├── README.md             # 项目总文档
└── DEPLOYMENT.md         # 部署文档
```

## 主要功能

### 教师功能
- 知识图谱可视化
- AI 评语生成器
- 资源面板管理
- 学生管理
- 专栏管理

### 学生功能
- 知识图谱学习
- 查看个人评语
- 学习资源访问
- 个人资料管理
- 反馈建议

## 常见问题

### 1. 跨域请求问题

确保 Flask 应用已配置 CORS：

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
```

### 2. 前端构建失败

确保 Node.js 和 npm 版本符合要求，并已安装所有依赖：

```bash
npm install
```

### 3. 后端服务无法启动

检查端口是否被占用，或环境变量配置是否正确。

### 4. 数据库连接错误

确保数据库服务已启动，连接字符串配置正确。

## 维护与更新

### 更新依赖

#### 后端

```bash
cd backend
pip install -r requirements.txt --upgrade
```

#### 前端

```bash
cd frontend
npm update
```

### 数据库迁移

如果使用 SQLAlchemy 和 Flask-Migrate：

```bash
flask db migrate -m "描述迁移内容"
flask db upgrade
```

## 安全建议

1. 生产环境中禁用调试模式
2. 使用强密码和密钥
3. 定期更新依赖包
4. 配置 HTTPS
5. 限制 API 访问频率
6. 对敏感数据进行加密

## 联系方式

如果在部署过程中遇到问题，请联系项目维护人员。
