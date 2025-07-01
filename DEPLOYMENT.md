# 部署说明 - 协作思维导图系统

## 📋 项目概述

这是一个基于 Vue.js + Django 的协作思维导图系统，支持多用户实时协作编辑思维导图。

## 🚀 快速部署

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/collaborative-mindmap-system.git
cd collaborative-mindmap-system
```

### 2. 后端部署 (Django)

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver
```

后端将运行在 `http://localhost:8000`

### 3. 前端部署 (Vue.js)

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 `http://localhost:5173`

## 🌐 生产环境部署

### Docker 部署（推荐）

1. 构建并运行容器：
```bash
# 构建后端
cd backend
docker build -t mindmap-backend .

# 构建前端
cd ../frontend
docker build -t mindmap-frontend .

# 使用 docker-compose 运行
docker-compose up -d
```

### 传统部署

#### 后端部署 (Django)
- 配置 PostgreSQL 数据库
- 设置环境变量
- 使用 Gunicorn + Nginx
- 配置 SSL 证书

#### 前端部署 (Vue.js)
- 构建生产版本：`npm run build`
- 将 `dist` 目录部署到 Web 服务器
- 配置反向代理

## 🔧 环境变量配置

### 后端环境变量 (`.env`)
```
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/mindmap_db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# 可选：邮件配置
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 前端环境变量 (`.env`)
```
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WS_BASE_URL=wss://api.yourdomain.com
```

## 📝 API 接口说明

### 认证接口
- `POST /api/auth/register/` - 用户注册
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/logout/` - 用户登出
- `GET /api/auth/me/` - 获取当前用户信息

### 项目管理
- `GET /api/projects/` - 获取项目列表
- `POST /api/projects/` - 创建项目
- `GET /api/projects/{id}/` - 获取项目详情
- `PUT /api/projects/{id}/` - 更新项目
- `DELETE /api/projects/{id}/` - 删除项目

### 思维导图节点
- `GET /api/projects/{id}/nodes/` - 获取项目的所有节点
- `POST /api/projects/{id}/nodes/` - 创建节点
- `PUT /api/nodes/{id}/` - 更新节点
- `DELETE /api/nodes/{id}/` - 删除节点

### WebSocket 实时协作
- 连接：`ws://localhost:8000/ws/mindmap/{project_id}/`
- 支持实时同步节点变更、用户状态等

## 🛠 技术栈

### 后端
- **Django 4.2+** - Web 框架
- **Django REST Framework** - API 开发
- **Django Channels** - WebSocket 支持
- **SQLite/PostgreSQL** - 数据库
- **Redis** - 缓存和消息队列

### 前端
- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **Element Plus** - UI 组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Simple Mind Map** - 思维导图组件
- **Vite** - 构建工具

## 🔒 安全注意事项

1. **更改默认密钥**：生产环境必须设置强密码的 `SECRET_KEY`
2. **HTTPS 配置**：生产环境启用 HTTPS
3. **CORS 配置**：正确配置跨域资源共享
4. **数据库安全**：使用强密码，限制数据库访问
5. **备份策略**：定期备份数据库和用户数据

## 🐛 故障排除

### 常见问题

1. **CORS 错误**
   - 检查后端 `CORS_ALLOWED_ORIGINS` 设置
   - 确保前端请求 URL 正确

2. **WebSocket 连接失败**
   - 确认 WebSocket URL 配置
   - 检查防火墙设置

3. **数据库连接错误**
   - 验证数据库配置
   - 确保数据库服务运行

4. **静态文件加载失败**
   - 运行 `python manage.py collectstatic`
   - 检查 Web 服务器配置

## 📞 技术支持

如有问题，请：
1. 查看项目 Issues
2. 提交 Bug 报告
3. 联系开发团队

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。
