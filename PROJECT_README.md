# 协作思维导图系统

一个基于 Vue.js + Django + WebSocket 的实时协作思维导图平台，支持多用户实时编辑、权限管理和节点级别的协作控制。

## 功能特性

### ✅ 已完成功能

#### 后端功能
- **用户认证系统**: Django Session 认证，支持登录/注册/登出
- **项目管理**: 创建、编辑、删除项目，支持成员邀请和权限管理
- **思维导图节点**: 完整的 CRUD 操作，支持层级结构和富文本
- **权限控制**: 项目级权限（read/edit/admin）+ 节点级所有权
- **实时协作框架**: Django Channels + WebSocket 支持
- **RESTful API**: 完整的 API 接口，支持 CORS 和 CSRF 保护

#### 前端功能
- **现代化界面**: Vue 3 + Element Plus，响应式设计
- **用户认证**: 登录/注册页面，自动CSRF处理
- **项目管理**: 项目列表、创建、操作面板
- **思维导图编辑器**: 集成 simple-mind-map，支持节点编辑和样式自定义
- **实时状态**: WebSocket 连接状态显示，在线用户统计
- **开发工具**: 调试页面，API 测试工具

### 🚧 开发中功能
- WebSocket 实时协作逻辑
- 成员管理界面
- 文件上传和导出功能
- 移动端优化

## 技术架构

### 后端技术栈
- **Django 5.2**: Web 框架
- **Django REST Framework**: API 开发
- **Django Channels**: WebSocket 支持
- **SQLite**: 数据库（开发环境）
- **Redis**: Channel Layer（生产环境）

### 前端技术栈
- **Vue 3**: 前端框架
- **TypeScript**: 类型安全
- **Element Plus**: UI 组件库
- **Pinia**: 状态管理
- **Vue Router**: 路由管理
- **Axios**: HTTP 客户端
- **Simple Mind Map**: 思维导图组件

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- pnpm 或 npm

### 后端设置

```bash
# 1. 创建虚拟环境
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 数据库迁移
python manage.py migrate

# 4. 创建超级用户
python manage.py createsuperuser

# 5. 启动开发服务器
python manage.py runserver
```

### 前端设置

```bash
# 1. 安装依赖
cd frontend
npm install

# 2. 启动开发服务器
npm run dev
```

### 访问应用

- 前端应用: http://localhost:5173
- 后端 API: http://localhost:8000
- Django 管理后台: http://localhost:8000/admin
- 调试工具: http://localhost:5173/debug

## 测试账户

系统已创建测试账户和数据：

- **管理员账户**: admin / admin
- **测试用户**: test / test123
- **测试项目**: "测试思维导图项目" (ID: 2)

## API 文档

### 用户认证
- `GET /api/csrf/` - 获取 CSRF Token
- `POST /api/users/login/` - 用户登录
- `POST /api/users/logout/` - 用户登出
- `GET /api/users/me/` - 获取当前用户信息
- `GET /api/users/dashboard/` - 获取用户仪表板

### 项目管理
- `GET /api/projects/` - 获取项目列表
- `POST /api/projects/` - 创建项目
- `GET /api/projects/{id}/` - 获取项目详情
- `PUT /api/projects/{id}/` - 更新项目
- `DELETE /api/projects/{id}/` - 删除项目

### 思维导图
- `GET /api/projects/{id}/nodes/` - 获取项目所有节点
- `POST /api/projects/{id}/nodes/` - 创建新节点
- `GET /api/projects/{id}/nodes/tree/` - 获取树形结构
- `GET /api/projects/{id}/nodes/simple-mind-map/` - 获取 simple-mind-map 格式数据

## 数据库模型

### 核心模型关系
```
User (用户)
├── Project (项目创建者)
├── ProjectMember (项目成员)
└── MindMapNode (节点创建者)

Project (项目)
├── ProjectMember (成员关系)
├── MindMapNode (项目节点)
└── NodeEditLog (编辑日志)

MindMapNode (思维导图节点)
├── 父子关系 (self-referencing)
├── 创建者关系
└── 编辑日志
```

### 权限系统
- **项目级权限**: read（只读）、edit（编辑）、admin（管理）
- **节点级权限**: 用户只能编辑自己创建的节点，但可以为任何节点添加子节点

## 开发状态

### 当前里程碑: MVP 核心功能 ✅

#### 已完成
1. ✅ 用户认证和会话管理
2. ✅ 项目 CRUD 和成员管理
3. ✅ 思维导图节点 CRUD
4. ✅ 基础权限控制
5. ✅ RESTful API 完整实现
6. ✅ 前端 Vue 应用框架
7. ✅ Simple Mind Map 集成
8. ✅ CSRF 和 CORS 配置

### 下一个里程碑: 实时协作

#### 待完成
1. 🚧 WebSocket 实时同步逻辑
2. 🚧 冲突检测和解决
3. 🚧 用户光标和选择同步
4. 🚧 操作历史和撤销功能

### 未来功能
- 📋 文件上传和图片支持
- 📋 多种导出格式（PDF、PNG、SVG）
- 📋 模板系统
- 📋 评论和标注功能
- 📋 移动端应用
- 📋 部署和 DevOps 配置

## 贡献指南

1. Fork 项目
2. 创建功能分支: `git checkout -b feature/AmazingFeature`
3. 提交更改: `git commit -m 'Add some AmazingFeature'`
4. 推送到分支: `git push origin feature/AmazingFeature`
5. 创建 Pull Request

## 许可证

[MIT License](LICENSE)

## 更新日志

### v0.1.0 (2025-07-02)
- 🎉 初始版本发布
- ✅ 完成核心 MVP 功能
- ✅ 前后端分离架构
- ✅ 基础思维导图编辑
- ✅ 用户认证和项目管理
