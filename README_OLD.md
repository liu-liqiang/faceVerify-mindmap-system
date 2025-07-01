# 在线项目协作系统

基于Vue + Django的实时协作思维导图系统，支持多用户同时编辑，具备完整的权限管理和实时同步功能。

## 项目特性

- 🎯 **实时协作**: 基于WebSocket的实时多人协作编辑
- 🔐 **权限管理**: 灵活的项目权限控制（只读、编辑、管理员）
- 🌳 **思维导图**: 集成simple-mind-map，支持丰富的节点编辑功能
- 📊 **项目管理**: 完整的项目创建、管理和成员邀请功能
- 🎨 **现代UI**: 基于Element Plus的现代化界面设计
- 📱 **响应式**: 支持桌面和移动端访问

## 技术栈

### 后端
- **Django 5.2**: Python Web框架
- **Django REST Framework**: API开发框架
- **Django Channels**: WebSocket支持
- **SQLite3**: 数据库（开发环境）
- **Redis**: 缓存和消息队列

### 前端
- **Vue 3**: 前端框架
- **TypeScript**: 类型安全
- **Element Plus**: UI组件库
- **Pinia**: 状态管理
- **Vue Router**: 路由管理
- **Axios**: HTTP客户端
- **Simple Mind Map**: 思维导图组件

## 项目结构

```
smmprojects/
├── backend/                 # Django后端
│   ├── collaboration_system/   # 项目配置
│   ├── users/                  # 用户管理
│   ├── projects/              # 项目管理
│   ├── mindmaps/              # 思维导图管理
│   ├── manage.py
│   └── requirements.txt
├── frontend/               # Vue前端
│   ├── src/
│   │   ├── components/       # 组件
│   │   ├── views/           # 页面
│   │   ├── stores/          # Pinia状态管理
│   │   ├── api/             # API调用
│   │   └── router/          # 路由配置
│   ├── package.json
│   └── vite.config.ts
└── docs/                   # 文档
```

## 数据库设计

### 用户模型 (User)
- 扩展Django默认用户模型
- 支持头像、创建时间等额外字段

### 项目模型 (Project)
- 项目基本信息（名称、描述、创建者）
- 多对多关系管理项目成员

### 项目成员模型 (ProjectMember)
- 用户与项目的关联关系
- 权限级别：只读(read)、编辑(edit)、管理员(admin)

### 思维导图节点模型 (MindMapNode)
- 节点内容（文本、图片、链接、备注）
- 样式信息（颜色、字体等）
- 层级关系（父子节点）
- 创建者和时间戳

### 节点编辑日志 (NodeEditLog)
- 记录所有节点的变更历史
- 支持操作回溯和审计

## 权限设计

### 项目级权限
- **只读(read)**: 可查看项目和思维导图，不能编辑
- **编辑(edit)**: 可以创建和编辑自己的节点，可在他人节点后添加子节点
- **管理员(admin)**: 项目完全控制权，可管理成员和权限

### 节点级权限
- 用户只能编辑自己创建的节点
- 不能删除有子节点的节点
- 不能删除他人创建的节点
- 可以在任何节点后添加子节点

## API设计

### 用户API
- `POST /api/users/login/` - 用户登录
- `POST /api/users/logout/` - 用户登出
- `POST /api/users/` - 用户注册
- `GET /api/users/me/` - 获取当前用户信息
- `GET /api/users/dashboard/` - 获取用户仪表板数据

### 项目API
- `GET /api/projects/` - 获取项目列表
- `POST /api/projects/` - 创建项目
- `GET /api/projects/{id}/` - 获取项目详情
- `PUT /api/projects/{id}/` - 更新项目
- `DELETE /api/projects/{id}/` - 删除项目
- `POST /api/projects/{id}/invite_member/` - 邀请成员
- `DELETE /api/projects/{id}/remove_member/` - 移除成员

### 思维导图API
- `GET /api/projects/{id}/nodes/` - 获取节点列表
- `POST /api/projects/{id}/nodes/` - 创建节点
- `PUT /api/projects/{id}/nodes/{node_id}/` - 更新节点
- `DELETE /api/projects/{id}/nodes/{node_id}/` - 删除节点
- `GET /api/projects/{id}/nodes/tree/` - 获取树形结构
- `GET /api/projects/{id}/nodes/simple-mind-map/` - 获取思维导图格式数据

### WebSocket API
- `ws://localhost:8000/ws/mindmap/{project_id}/` - 思维导图实时协作

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- Redis Server

### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 访问地址
- 前端应用: http://localhost:5173
- 后端API: http://localhost:8000
- 管理后台: http://localhost:8000/admin

## 开发进度

### 已完成 ✅
- [x] 项目基础架构搭建
- [x] 用户认证系统
- [x] 项目管理功能
- [x] 数据库模型设计
- [x] REST API开发
- [x] WebSocket实时通信框架
- [x] 前端基础页面和组件
- [x] 状态管理和路由配置

### 进行中 🚧
- [ ] 思维导图编辑器集成
- [ ] WebSocket实时协作功能
- [ ] 成员管理界面
- [ ] 权限控制完善

### 待开发 📋
- [ ] 文件上传功能
- [ ] 导出功能（PDF、图片等）
- [ ] 操作历史回放
- [ ] 移动端适配优化
- [ ] 性能优化
- [ ] 单元测试
- [ ] 部署配置

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。
