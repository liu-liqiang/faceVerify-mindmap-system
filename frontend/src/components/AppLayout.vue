<template>
  <div class="app-layout">
    <el-container>
      <!-- 头部导航 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="header-left">
            <router-link to="/dashboard" class="logo">
              <h2>SMM协作系统</h2>
            </router-link>
          </div>

          <div class="header-nav">
            <el-menu mode="horizontal" :default-active="activeMenu" class="header-menu" @select="handleMenuSelect">
              <el-menu-item index="/dashboard">
                <el-icon>
                  <House />
                </el-icon>
                <span>仪表板</span>
              </el-menu-item>
              <el-menu-item index="/projects">
                <el-icon>
                  <Folder />
                </el-icon>
                <span>项目管理</span>
              </el-menu-item>
            </el-menu>
          </div>

          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-dropdown">
                <el-avatar :size="32">
                  {{ authStore.user?.username?.charAt(0).toUpperCase() }}
                </el-avatar>
                <span class="username">{{ authStore.user?.username }}</span>
                <el-icon>
                  <ArrowDown />
                </el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon>
                      <User />
                    </el-icon>
                    个人资料
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon>
                      <SwitchButton />
                    </el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <!-- 主内容区域 -->
      <el-main class="app-main">
        <div class="main-content">
          <div v-if="$slots.header" class="content-header">
            <slot name="header" />
          </div>
          <div class="content-body">
            <slot />
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  House,
  Folder,
  User,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/projects')) {
    return '/projects'
  }
  return '/dashboard'
})

const handleMenuSelect = (index: string) => {
  router.push(index)
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      // TODO: 实现个人资料页面
      ElMessage.info('个人资料功能开发中')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '确认退出',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await authStore.logout()
        ElMessage.success('退出成功')
        router.push('/login')
      } catch (error) {
        // 用户取消操作
      }
      break
  }
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  height: 100vh;
  /* 强制设置高度 */
  background-color: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  padding: 0;
  height: 60px !important;
  line-height: 60px;
}

.header-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  margin: 0;
  padding: 0 20px;
}

.header-left {
  flex-shrink: 0;
}

.logo {
  text-decoration: none;
  color: #333;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-nav {
  flex: 1;
  display: flex;
  justify-content: center;
}

.header-menu {
  border-bottom: none;
  background: transparent;
}

:deep(.el-menu--horizontal .el-menu-item) {
  border-bottom: 2px solid transparent;
  color: #606266;
  font-weight: 500;
}

:deep(.el-menu--horizontal .el-menu-item:hover),
:deep(.el-menu--horizontal .el-menu-item.is-active) {
  border-bottom-color: #409EFF;
  color: #409EFF;
  background-color: transparent;
}

.header-right {
  flex-shrink: 0;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.app-main {
  padding: 0;
  background-color: #f5f7fa;
  flex: 1;
  /* 确保主内容区域占据剩余空间 */
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  /* 减去header高度 */
  overflow: hidden;
}

/* 覆盖 Element Plus 的容器样式 */
:deep(.el-container) {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

:deep(.el-main) {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.main-content {
  width: 100%;
  margin: 0;
  padding: 20px;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-header {
  margin-bottom: 20px;
  flex-shrink: 0;
}

.content-body {
  background: transparent;
  flex: 1;
  overflow: hidden;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 15px;
  }

  .header-nav {
    display: none;
  }

  .logo h2 {
    font-size: 18px;
  }

  .main-content {
    padding: 15px;
  }
}
</style>
