# --- 构建阶段：使用 Node.js 镜像构建 Vue 应用 ---
FROM node:16-alpine as builder

WORKDIR /app

# 复制 package.json 和 package-lock.json 并安装依赖
COPY frontend/package*.json ./ 
RUN npm install --omit=dev

# 复制前端代码并执行构建
COPY frontend/ . 
RUN npm run build

# --- 运行阶段：使用轻量级 Nginx 镜像提供静态文件 ---
FROM nginx:stable-alpine

# 删除 Nginx 默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 复制自定义 Nginx 配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建好的静态文件到 Nginx 的默认静态文件目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露 Nginx 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
