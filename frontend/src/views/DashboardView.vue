<template>
  <div class="dashboard">
    <AppLayout>
      <template #header>
        <div class="dashboard-header">
          <h1>个人仪表板</h1>
          <p>欢迎回来，{{ authStore.user?.username }}！</p>
        </div>
      </template>
      
      <div class="dashboard-content">
        <!-- 统计卡片 -->
        <div class="stats-grid">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon projects">
                <el-icon><Folder /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ dashboardData?.total_projects || 0 }}</h3>
                <p>参与项目</p>
              </div>
            </div>
          </el-card>
          
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon nodes">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="stat-info">
                <h3>{{ dashboardData?.total_nodes_created || 0 }}</h3>
                <p>创建节点</p>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 项目列表 -->
        <el-card class="projects-card">
          <template #header>
            <div class="card-header">
              <h3>我的项目</h3>
              <el-button type="primary" @click="$router.push('/projects')">
                查看全部
              </el-button>
            </div>
          </template>
          
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="3" animated />
          </div>
          
          <div v-else-if="dashboardData?.projects?.length" class="projects-list">
            <div
              v-for="project in dashboardData.projects.slice(0, 5)"
              :key="project.id"
              class="project-item"
              @click="$router.push(`/projects/${project.id}`)"
            >
              <div class="project-info">
                <h4>{{ project.name }}</h4>
                <p class="project-permission">{{ getPermissionText(project.permission) }}</p>
                <div class="project-stats">
                  <span class="stat">
                    <el-icon><User /></el-icon>
                    我的节点: {{ project.user_nodes_count }}
                  </span>
                  <span class="stat">
                    <el-icon><Connection /></el-icon>
                    总节点: {{ project.total_nodes_count }}
                  </span>
                </div>
              </div>
              <div class="project-actions">
                <el-button
                  size="small"
                  @click.stop="$router.push(`/projects/${project.id}/mindmap`)"
                >
                  打开思维导图
                </el-button>
              </div>
            </div>
          </div>
          
          <el-empty v-else description="还没有参与任何项目">
            <el-button type="primary" @click="$router.push('/projects')">
              开始创建项目
            </el-button>
          </el-empty>
        </el-card>
      </div>
    </AppLayout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { userAPI } from '@/api'
import { ElMessage } from 'element-plus'
import { Folder, Connection, User } from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'

const authStore = useAuthStore()
const loading = ref(false)
const dashboardData = ref<any>(null)

const getPermissionText = (permission: string) => {
  const permissionMap: Record<string, string> = {
    'read': '只读',
    'edit': '编辑',
    'admin': '管理员'
  }
  return permissionMap[permission] || permission
}

const fetchDashboardData = async () => {
  // 确保用户已经通过认证
  if (!authStore.isAuthenticated) {
    console.log('User not authenticated, skipping dashboard data fetch')
    return
  }
  
  loading.value = true
  try {
    const response = await userAPI.getDashboard()
    dashboardData.value = response.data
  } catch (error: any) {
    console.error('Failed to fetch dashboard data:', error)
    
    // 如果是认证错误，重定向到登录页
    if (error.response?.status === 401 || error.response?.status === 403) {
      ElMessage.error('认证已过期，请重新登录')
      authStore.logout()
      window.location.href = '/login'
    } else {
      ElMessage.error('获取仪表板数据失败')
    }
  } finally {
    loading.value = false
  }
}

// 监听认证状态变化
watch(() => authStore.isAuthenticated, (authenticated: boolean) => {
  if (authenticated) {
    fetchDashboardData()
  }
}, { immediate: true })

onMounted(async () => {
  // 如果用户已经认证，直接获取数据
  if (authStore.isAuthenticated) {
    await fetchDashboardData()
  }
  // 否则等待路由守卫完成认证检查
})
</script>

<style scoped>
.dashboard-header {
  margin-bottom: 24px;
}

.dashboard-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.dashboard-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.stat-icon.projects {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.nodes {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-info h3 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.stat-info p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.projects-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.loading-container {
  padding: 20px 0;
}

.projects-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.project-item:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.project-info h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.project-permission {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #409EFF;
  background: #ecf5ff;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
}

.project-stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.project-actions {
  flex-shrink: 0;
}
</style>
