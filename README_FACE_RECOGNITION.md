# 公安案件协作系统 - 人脸识别版

基于 Vue 3 + Django 的公安案件协作思维导图系统，集成前端人脸识别技术。

## 🚀 项目特色

### 人脸识别系统重构
- **前端处理**: 使用 face-api.js 在浏览器端进行人脸检测和特征提取
- **隐私保护**: 仅存储128维特征向量，不保存人脸图片
- **高性能**: 无需后端GPU，降低服务器负载
- **离线能力**: 支持离线人脸识别模型

### 核心功能
- 👤 **用户注册与审核**: 警员信息注册、管理员审核
- 🔐 **双因子认证**: 密码 + 人脸识别登录
- 📷 **人脸录入**: 支持注册时录入和后期补录
- 🧠 **协作思维导图**: 实时协作的案件分析工具
- 👨‍💼 **管理员系统**: 用户管理、权限控制

## 🛠️ 技术栈

### 前端
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **人脸识别**: face-api.js
- **状态管理**: Pinia
- **路由**: Vue Router

### 后端  
- **框架**: Django + Django REST Framework
- **数据库**: SQLite (可扩展至 PostgreSQL)
- **认证**: Django Session + 自定义人脸验证
- **API设计**: RESTful API

## 📦 快速开始

### 环境要求
- Node.js 16+ 
- Python 3.8+
- 现代浏览器（支持 WebRTC）

### 1. 克隆项目
```bash
git clone <repository-url>
cd smmproj
```

### 2. 后端设置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 3. 前端设置
```bash
cd frontend
npm install
npm install face-api.js
node download_models.cjs  # 下载人脸识别模型
npm run dev
```

### 4. 访问系统
- 前端: http://localhost:5173
- 后端API: http://localhost:8000
- 管理后台: http://localhost:8000/admin

## 🎯 使用流程

### 用户注册流程
1. 填写基本信息（姓名、警号、手机号、所属单位）
2. 设置登录密码
3. 人脸信息录入（拍摄3张照片）
4. 等待管理员审核

### 登录流程
1. 输入警号和密码（第一步验证）
2. 人脸识别验证（第二步验证）
3. 登录成功，进入系统

### 人脸补录
1. 身份验证（警号 + 密码 + 手机号）
2. 重新录入人脸信息
3. 覆盖原有数据

## 🔧 核心技术实现

### 人脸识别数据流
```
前端采集 → face-api.js提取特征 → 128维向量 → 后端存储
     ↓
前端比对 ← 获取特征库 ← JSON数组 ← 数据库查询
```

### 数据结构
```python
# CustomUser.face_encodings 字段存储格式
[
  [0.1, -0.2, 0.3, ...],  # 特征向量1 (128维)
  [0.2, -0.1, 0.4, ...],  # 特征向量2 (128维)  
  [0.0, -0.3, 0.2, ...]   # 特征向量3 (128维)
]
```

### API接口
- `POST /api/users/` - 用户注册
- `POST /api/users/login/` - 密码登录
- `POST /api/users/face_verify/` - 人脸验证
- `POST /api/users/register_face/` - 人脸录入
- `POST /api/users/supplement-face/` - 人脸补录
- `GET /api/users/get_face_encodings/` - 获取特征库

## 📂 项目结构

```
smmproj/
├── backend/                    # Django后端
│   ├── users/                 # 用户管理应用
│   │   ├── models.py         # CustomUser模型
│   │   ├── views.py          # 人脸识别API
│   │   └── migrations/       # 数据库迁移
│   ├── projects/             # 项目管理
│   ├── mindmaps/             # 思维导图
│   └── collaboration_system/ # 主配置
├── frontend/                  # Vue前端
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   │   ├── LoginView.vue           # 登录页面
│   │   │   ├── FaceRegisterView.vue    # 人脸录入
│   │   │   ├── FaceSupplementView.vue  # 人脸补录
│   │   │   └── UserManagementView.vue  # 用户管理
│   │   ├── api/             # API调用
│   │   └── stores/          # 状态管理
│   ├── public/models/       # face-api.js模型文件
│   └── download_models.cjs  # 模型下载脚本
└── README.md
```

## 🔐 安全特性

- **数据加密**: 特征向量采用不可逆存储
- **权限控制**: 基于角色的访问控制
- **会话管理**: 安全的登录会话机制
- **CSRF防护**: 防止跨站请求伪造
- **输入验证**: 严格的数据验证机制

## 🚀 部署指南

### 生产环境部署
1. 配置 PostgreSQL 数据库
2. 设置 Nginx 反向代理
3. 使用 Gunicorn 运行 Django
4. 配置 SSL 证书
5. 设置静态文件服务

### Docker 部署
```bash
# 后端
docker build -t police-backend ./backend
docker run -p 8000:8000 police-backend

# 前端
docker build -t police-frontend ./frontend  
docker run -p 80:80 police-frontend
```

## 📋 开发计划

- [ ] 移动端适配
- [ ] 多级权限管理
- [ ] 审计日志功能
- [ ] 数据导出功能
- [ ] 系统监控面板
- [ ] 消息通知系统

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v2.0.0 (2025-07-02)
- ✨ 重构人脸识别系统，迁移至前端 face-api.js
- 🔥 删除后端人脸识别依赖
- 🎨 优化用户界面和交互体验
- 🚀 提升系统性能和隐私保护
- 📱 改进移动端兼容性

### v1.0.0
- 🎉 初始版本，基础协作思维导图功能

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目维护者: Police Collaboration System Team
- 邮箱: police.collaboration@system.com

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！
