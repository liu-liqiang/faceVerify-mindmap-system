<template>
  <div class="face-verify-container">
    <el-card class="verify-card">
      <template #header>
        <div class="card-header">
          <h2>人脸识别验证</h2>
          <p>{{ user?.real_name }}（{{ user?.police_number }}），请进行人脸识别</p>
        </div>
      </template>
      
      <div class="verify-content">
        <FaceCapture
          :max-capture-time="20"
          :auto-capture="false"
          @face-data="handleFaceData"
          @capture-complete="handleCaptureComplete"
          @error="handleError"
        />
        
        <div class="verify-status">
          <el-alert
            v-if="verifying"
            title="正在进行人脸识别验证..."
            type="info"
            show-icon
            :closable="false"
          />
          
          <el-alert
            v-if="errorMessage"
            :title="errorMessage"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
        
        <div class="verify-actions">
          <el-button @click="goBack" size="large">
            返回登录
          </el-button>
          
          <el-button
            type="primary"
            size="large"
            :loading="verifying"
            @click="retryVerification"
            v-if="!verifying"
          >
            重新识别
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import FaceCapture from '@/components/FaceCapture.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const user = ref<any>(null)
const verifying = ref(false)
const errorMessage = ref('')

onMounted(() => {
  // 检查是否有传递的用户信息
  if (route.params.user) {
    try {
      user.value = JSON.parse(route.params.user as string)
    } catch (error) {
      console.error('Error parsing user data:', error)
      goBack()
    }
  } else {
    // 如果没有用户信息，返回登录页
    goBack()
  }
})

const handleFaceData = async (faceData: string) => {
  verifying.value = true
  errorMessage.value = ''
  
  try {
    const result = await authStore.faceVerify(faceData)
    
    ElMessage.success(`人脸识别成功！置信度：${result.face_confidence}%`)
    
    // 登录成功，跳转到首页
    router.push('/')
  } catch (error: any) {
    console.error('Face verification error:', error)
    
    if (error.response?.data?.error) {
      errorMessage.value = error.response.data.error
    } else {
      errorMessage.value = '人脸识别失败，请重试'
    }
  } finally {
    verifying.value = false
  }
}

const handleCaptureComplete = (success: boolean, data?: string) => {
  if (success && data) {
    // 人脸捕获完成，开始验证
    // handleFaceData 会自动被调用
  }
}

const handleError = (error: string) => {
  errorMessage.value = error
  ElMessage.error(error)
}

const retryVerification = () => {
  errorMessage.value = ''
  verifying.value = false
}

const goBack = () => {
  router.push('/login')
}
</script>

<style scoped>
.face-verify-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.verify-card {
  width: 100%;
  max-width: 800px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  border: none;
}

.card-header {
  text-align: center;
  margin-bottom: 20px;
}

.card-header h2 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.card-header p {
  margin: 0;
  color: #666;
  font-size: 16px;
}

.verify-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.verify-status {
  width: 100%;
  max-width: 400px;
}

.verify-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}
</style>
