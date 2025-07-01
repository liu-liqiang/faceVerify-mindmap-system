<template>
  <div class="project-members">
    <AppLayout>
      <template #header>
        <div class="page-header">
          <h1>成员管理</h1>
          <div class="header-actions">
            <el-button type="primary">
              <el-icon><Plus /></el-icon>
              邀请成员
            </el-button>
            <el-button @click="$router.back()">
              <el-icon><ArrowLeft /></el-icon>
              返回
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="content">
        <el-card>
          <h3>成员管理页面开发中...</h3>
          <p>项目ID: {{ $route.params.id }}</p>
        </el-card>
      </div>
    </AppLayout>
  </div>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import { Plus, ArrowLeft } from '@element-plus/icons-vue'
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
