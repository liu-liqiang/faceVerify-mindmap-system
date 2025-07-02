# 部署说明

## 当前状态
项目已完成人脸识别系统重构，所有代码已提交到本地Git仓库。

## 如何创建新的GitHub仓库

### 方法1: 在GitHub网站创建
1. 登录 GitHub
2. 点击右上角的 "+" → "New repository"
3. 填写仓库名称，如: `police-collaboration-face-recognition`
4. 选择 "Public" 或 "Private"
5. 不要初始化 README, .gitignore 或 license (因为本地已有)
6. 点击 "Create repository"

### 方法2: 使用GitHub CLI (如果已安装)
```bash
gh repo create police-collaboration-face-recognition --public
```

## 推送到新仓库

获取新仓库的URL后，执行以下命令：

```bash
# 更改远程仓库地址 (替换 YOUR_USERNAME 和 REPO_NAME)
git remote set-url origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 推送代码
git push -u origin main
```

## 首次部署检查清单

### 服务器环境
- [ ] Python 3.8+ 已安装
- [ ] Node.js 16+ 已安装  
- [ ] 数据库服务 (PostgreSQL 推荐)
- [ ] Nginx 或其他Web服务器

### 安全配置
- [ ] 修改 Django SECRET_KEY
- [ ] 设置正确的 ALLOWED_HOSTS
- [ ] 配置数据库连接
- [ ] 设置HTTPS证书
- [ ] 配置防火墙规则

### 模型文件下载
用户需要手动执行：
```bash
cd frontend
node download_models.cjs
```

## 注意事项

1. **模型文件**: face-api.js 模型文件较大 (约8MB)，已添加到 .gitignore
2. **环境变量**: 生产环境需要设置适当的环境变量
3. **数据库迁移**: 首次部署时记得运行 `python manage.py migrate`
4. **静态文件**: 生产环境需要收集静态文件 `python manage.py collectstatic`

## 项目特色

✅ 前端人脸识别 (face-api.js)
✅ 隐私保护 (仅存储特征向量)  
✅ 双因子认证 (密码 + 人脸)
✅ 完整的用户管理流程
✅ 协作思维导图功能
