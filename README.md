# 🧠 协作思维导图系统

<div align="center">

![Vue.js](https://img.shields.io/badge/Vue.js-3.x-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![Element Plus](https://img.shields.io/badge/Element_Plus-409EFF?style=for-the-badge&logo=element&logoColor=white)

一个功能强大的协作思维导图系统，支持多用户实时协作编辑、项目管理和直观的思维导图创建。

[在线演示](https://your-demo-link.com) · [报告问题](https://github.com/YOUR_USERNAME/collaborative-mindmap-system/issues) · [功能请求](https://github.com/YOUR_USERNAME/collaborative-mindmap-system/issues)

</div>

## ✨ 功能特性

### 🎯 核心功能
- **🔄 实时协作**: WebSocket 支持多用户同时编辑思维导图
- **📊 项目管理**: 创建、管理和分享思维导图项目
- **🎨 可视化编辑**: 基于 `simple-mind-map` 的直观编辑器
- **👥 用户管理**: 完整的用户认证和权限系统
- **📱 响应式设计**: 支持桌面和移动设备

### 🛠 技术特性
- **全屏编辑体验**: 沉浸式的思维导图编辑界面
- **属性面板**: 动态显示的节点属性编辑面板
- **自动保存**: 实时保存编辑内容
- **导出功能**: 支持多种格式导出
- **主题系统**: 多种思维导图主题选择

## 🚀 快速开始

### 📋 环境要求

- **后端**: Python 3.8+, Django 4.2+
- **前端**: Node.js 16+, npm 或 yarn
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis (可选，用于 WebSocket)

### 🔧 本地开发

1. **克隆项目**
```bash
git clone https://github.com/YOUR_USERNAME/collaborative-mindmap-system.git
cd collaborative-mindmap-system
```

2. **启动后端**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

3. **启动前端**
```bash
cd frontend
npm install
npm run dev
```

4. **访问应用**
- 前端: http://localhost:5173
- 后端 API: http://localhost:8000

### 🐳 Docker 部署

```bash
# 一键启动整个系统
docker-compose up -d

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 📸 功能预览

### 🏠 项目管理界面
- 创建和管理思维导图项目
- 邀请团队成员协作
- 项目权限管理

### 🧠 思维导图编辑器
- 全屏沉浸式编辑体验
- 实时节点属性编辑
- 多种布局和主题选择
- 快捷键支持

### 👥 实时协作
- 多用户同时在线编辑
- 实时同步节点变更
- 在线用户状态显示

## 🏗 项目架构

```
collaborative-mindmap-system/
├── backend/                 # Django 后端
│   ├── collaboration_system/   # 项目配置
│   ├── users/                  # 用户管理
│   ├── projects/               # 项目管理
│   ├── mindmaps/              # 思维导图功能
│   └── requirements.txt       # Python 依赖
├── frontend/                # Vue.js 前端
│   ├── src/
│   │   ├── components/         # 组件
│   │   ├── views/             # 页面
│   │   ├── stores/            # 状态管理
│   │   └── api/               # API 接口
│   └── package.json          # Node.js 依赖
├── docker-compose.yml       # Docker 编排
└── DEPLOYMENT.md           # 部署文档
```

## 🔧 技术栈

### 后端技术
- **[Django](https://djangoproject.com/)** - Web 框架
- **[Django REST Framework](https://www.django-rest-framework.org/)** - API 开发
- **[Django Channels](https://channels.readthedocs.io/)** - WebSocket 支持
- **[Redis](https://redis.io/)** - 缓存和消息队列

### 前端技术
- **[Vue 3](https://vuejs.org/)** - 前端框架
- **[TypeScript](https://www.typescriptlang.org/)** - 类型安全
- **[Element Plus](https://element-plus.org/)** - UI 组件库
- **[Pinia](https://pinia.vuejs.org/)** - 状态管理
- **[Simple Mind Map](https://github.com/wanglin2/mind-map)** - 思维导图组件
- **[Vite](https://vitejs.dev/)** - 构建工具

## 📖 API 文档

### 认证接口
```http
POST /api/auth/register/     # 用户注册
POST /api/auth/login/        # 用户登录
GET  /api/auth/me/          # 获取用户信息
```

### 项目管理
```http
GET    /api/projects/        # 获取项目列表
POST   /api/projects/        # 创建项目
GET    /api/projects/{id}/   # 获取项目详情
PUT    /api/projects/{id}/   # 更新项目
DELETE /api/projects/{id}/   # 删除项目
```

### 思维导图节点
```http
GET    /api/projects/{id}/nodes/  # 获取项目节点
POST   /api/projects/{id}/nodes/  # 创建节点
PUT    /api/nodes/{id}/          # 更新节点
DELETE /api/nodes/{id}/          # 删除节点
```

详细的 API 文档请参考 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 🤝 贡献指南

我们欢迎各种形式的贡献！

1. **Fork** 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 **Pull Request**

### 🐛 问题反馈

如果您发现了 bug 或有功能建议，请：
1. 查看 [已有 Issues](https://github.com/YOUR_USERNAME/collaborative-mindmap-system/issues)
2. 创建新的 [Issue](https://github.com/YOUR_USERNAME/collaborative-mindmap-system/issues/new)

## 📋 开发计划

- [ ] **实时协作增强**
  - [ ] 完整的 WebSocket 实时同步
  - [ ] 多用户光标显示
  - [ ] 冲突解决机制

- [ ] **功能扩展**
  - [ ] 思维导图模板库
  - [ ] 更多导出格式 (PDF, SVG, XMind)
  - [ ] 评论和标注系统
  - [ ] 版本历史和回滚

- [ ] **用户体验**
  - [ ] 移动端优化
  - [ ] 离线编辑支持
  - [ ] 快捷键自定义
  - [ ] 主题编辑器

- [ ] **集成功能**
  - [ ] 第三方登录 (Google, GitHub)
  - [ ] 云存储集成
  - [ ] API 开放平台

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE) - 详见 LICENSE 文件。

## 👥 贡献者

感谢所有为这个项目做出贡献的开发者！

<div align="center">
<a href="https://github.com/YOUR_USERNAME/collaborative-mindmap-system/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=YOUR_USERNAME/collaborative-mindmap-system" />
</a>
</div>

## 📞 联系我们

- 项目地址: [GitHub](https://github.com/YOUR_USERNAME/collaborative-mindmap-system)
- 问题反馈: [Issues](https://github.com/YOUR_USERNAME/collaborative-mindmap-system/issues)
- 邮箱: your-email@example.com

---

<div align="center">

**[⬆ 回到顶部](#-协作思维导图系统)**

Made with ❤️ by [Your Name](https://github.com/YOUR_USERNAME)

</div>
