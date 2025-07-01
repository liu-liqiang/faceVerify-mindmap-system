<template>
  <div class="project-detail">
    <AppLayout>
      <template #header>
        <div class="page-header">
          <h1>项目详情</h1>
          <div class="header-actions">
            <el-button @click="$router.push(`/projects/${$route.params.id}/mindmap`)">
              <el-icon><Share /></el-icon>
              打开思维导图
            </el-button>
            <el-button @click="$router.push(`/projects/${$route.params.id}/members`)">
              <el-icon><User /></el-icon>
              成员管理
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="content">
        <el-card>
          <h3>项目详情页面开发中...</h3>
          <p>项目ID: {{ $route.params.id }}</p>
        </el-card>
      </div>
    </AppLayout>
  </div>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { Share, User } from '@element-plus/icons-vue'
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>
