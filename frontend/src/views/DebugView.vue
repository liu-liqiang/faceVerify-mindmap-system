<template>
  <div class="debug-container">
    <el-card>
      <template #header>
        <h2>系统调试工具</h2>
      </template>
      
      <el-space direction="vertical" size="large" style="width: 100%">
        <!-- CSRF 测试 -->
        <el-card>
          <template #header>
            <h3>CSRF Token 测试</h3>
          </template>
          <el-space>
            <el-button @click="testCSRF" type="primary">测试 CSRF 获取</el-button>
            <el-button @click="showCSRFToken">显示当前 CSRF Token</el-button>
          </el-space>
          <div v-if="csrfToken" class="token-display">
            <p><strong>CSRF Token:</strong> {{ csrfToken }}</p>
          </div>
        </el-card>

        <!-- API 测试 -->
        <el-card>
          <template #header>
            <h3>API 端点测试</h3>
          </template>
          <el-space>
            <el-button @click="testLogin" type="success">测试登录 (admin/admin)</el-button>
            <el-button @click="testDashboard" type="info">测试仪表板</el-button>
            <el-button @click="testProjects" type="warning">测试项目列表</el-button>
          </el-space>
        </el-card>

        <!-- 结果显示 -->
        <el-card>
          <template #header>
            <h3>测试结果</h3>
          </template>
          <div class="result-area">
            <pre>{{ testResults }}</pre>
          </div>
        </el-card>
      </el-space>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { userAPI, projectAPI, initializeCSRF } from '@/api'
import { ElMessage } from 'element-plus'

const csrfToken = ref('')
const testResults = ref('点击上方按钮开始测试...')

// 获取CSRF token的函数
const getCSRFToken = () => {
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      return decodeURIComponent(value)
    }
  }
  return null
}

const testCSRF = async () => {
  try {
    testResults.value = '正在获取 CSRF token...'
    await initializeCSRF()
    const token = getCSRFToken()
    csrfToken.value = token || 'No token found'
    testResults.value = `CSRF token 获取成功: ${token}`
    ElMessage.success('CSRF token 获取成功')
  } catch (error: any) {
    testResults.value = `CSRF token 获取失败: ${error.message}`
    ElMessage.error('CSRF token 获取失败')
  }
}

const showCSRFToken = () => {
  const token = getCSRFToken()
  csrfToken.value = token || 'No token found'
  testResults.value = `当前 CSRF token: ${token || 'No token found'}`
}

const testLogin = async () => {
  try {
    testResults.value = '正在测试登录...'
    const response = await userAPI.login({ username: 'admin', password: 'admin' })
    testResults.value = `登录测试成功:\n${JSON.stringify(response.data, null, 2)}`
    ElMessage.success('登录测试成功')
  } catch (error: any) {
    testResults.value = `登录测试失败:\n${JSON.stringify(error.response?.data || error.message, null, 2)}`
    ElMessage.error('登录测试失败')
  }
}

const testDashboard = async () => {
  try {
    testResults.value = '正在测试仪表板 API...'
    const response = await userAPI.getDashboard()
    testResults.value = `仪表板测试成功:\n${JSON.stringify(response.data, null, 2)}`
    ElMessage.success('仪表板测试成功')
  } catch (error: any) {
    testResults.value = `仪表板测试失败:\n${JSON.stringify(error.response?.data || error.message, null, 2)}`
    ElMessage.error('仪表板测试失败')
  }
}

const testProjects = async () => {
  try {
    testResults.value = '正在测试项目列表 API...'
    const response = await projectAPI.list()
    testResults.value = `项目列表测试成功:\n${JSON.stringify(response.data, null, 2)}`
    ElMessage.success('项目列表测试成功')
  } catch (error: any) {
    testResults.value = `项目列表测试失败:\n${JSON.stringify(error.response?.data || error.message, null, 2)}`
    ElMessage.error('项目列表测试失败')
  }
}
</script>

<style scoped>
.debug-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.token-display {
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 4px;
  word-break: break-all;
}

.result-area {
  max-height: 400px;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
}
</style>
