<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>公安案件协作系统</h2>
          <p v-if="loginStep === 'password'">第一步：输入账号密码</p>
          <p v-else-if="loginStep === 'face'">第二步：人脸识别验证</p>
          <p v-else>请登录</p>
        </div>
      </template>

      <!-- 第一步：账号密码登录 -->
      <div v-if="loginStep === 'password'">
        <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" label-width="80px"
          @submit.prevent="handlePasswordLogin">
          <el-form-item label="警号" prop="policeNumber">
            <el-input v-model="loginForm.policeNumber" placeholder="请输入警号" clearable />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password clearable
              @keyup.enter="handlePasswordLogin" />
          </el-form-item>

          <el-form-item>
            <el-alert title="登录说明" type="info" show-icon :closable="false" style="margin-bottom: 20px">
              <p>1. 先输入警号和密码进行第一步验证</p>
              <p>2. 验证通过后将进入人脸识别环节</p>
              <p>3. 如需补录人脸信息，请联系管理员</p>
            </el-alert>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" :loading="loading" @click="handlePasswordLogin" style="width: 100%">
              下一步：人脸识别
            </el-button>
          </el-form-item>

          <el-form-item>
            <div class="login-footer">
              <span>还没有账户？</span>
              <router-link to="/register" class="register-link">
                立即注册
              </router-link>
              <span style="margin: 0 8px;">|</span>
              <router-link :to="`/face-supplement?police_number=${loginForm.policeNumber}`" class="register-link">
                人脸补录
              </router-link>
              <span style="margin: 0 8px;">|</span>
              <router-link to="/admin-login" class="admin-link">
                管理员后台
              </router-link>
            </div>
          </el-form-item>
        </el-form>
      </div>

      <!-- 第二步：人脸识别 -->
      <div v-else-if="loginStep === 'face'">
        <div class="face-login-section">
          <div class="user-info">
            <el-tag size="large" type="success">{{ userInfo.real_name }} ({{ userInfo.police_number }})</el-tag>
            <p v-if="!autoRecognizing" style="margin: 10px 0; color: #666;">请进行人脸识别以完成登录</p>
            <p v-else style="margin: 10px 0; color: #409EFF;">
              自动识别中... 剩余时间: {{ recognitionCountdown }}秒
              <br>
              <small>第 {{ recognitionAttempts + 1 }} 次尝试 (最多 {{ maxAttempts }} 次)</small>
            </p>
          </div>

          <div class="camera-container">
            <video ref="videoRef" autoplay playsinline :style="{ display: showCamera ? 'block' : 'none' }"></video>
            <canvas ref="canvasRef" :style="{ display: showCamera ? 'none' : 'block' }"></canvas>
            
            <!-- 识别状态指示器 -->
            <div v-if="autoRecognizing" class="recognition-indicator">
              <el-progress 
                type="circle" 
                :percentage="Math.round((20 - recognitionCountdown) / 20 * 100)"
                :color="recognitionCountdown > 5 ? '#409EFF' : '#F56C6C'"
                :width="80">
                <template #default="{ percentage }">
                  <span class="countdown-text">{{ recognitionCountdown }}s</span>
                </template>
              </el-progress>
            </div>
          </div>

          <div class="face-controls">
            <el-button v-if="!cameraStarted" type="primary" @click="startCameraAndAutoRecognize" :loading="cameraLoading">
              开始人脸识别
            </el-button>
            
            <div v-else class="face-buttons">
              <el-button 
                v-if="!autoRecognizing" 
                type="success" 
                @click="startAutoRecognition" 
                :loading="verifying">
                开始自动识别
              </el-button>
              
              <el-button 
                v-if="autoRecognizing" 
                type="warning" 
                @click="stopAutoRecognition">
                停止识别
              </el-button>
              
              <el-button 
                v-if="!autoRecognizing" 
                type="info" 
                @click="captureFace" 
                :loading="verifying">
                手动识别
              </el-button>
              
              <el-button @click="restartPasswordLogin">
                重新输入密码
              </el-button>
            </div>
          </div>
        </div>
      </div>

    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { userAPI } from '@/api'
import * as faceapi from 'face-api.js'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref<FormInstance>()
const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()

const loading = ref(false)
const cameraLoading = ref(false)
const verifying = ref(false)
const cameraStarted = ref(false)
const showCamera = ref(true)
const loginStep = ref<'password' | 'face'>('password')
const modelsLoaded = ref(false)

// 自动识别相关状态
const autoRecognizing = ref(false)
const recognitionCountdown = ref(20)
const recognitionAttempts = ref(0)
const maxAttempts = 3
let recognitionTimer: NodeJS.Timeout | null = null
let countdownTimer: NodeJS.Timeout | null = null

const userInfo = ref<any>({})
const userFaceEncodings = ref<number[][]>([])
let mediaStream: MediaStream | null = null

const loginForm = reactive({
  policeNumber: '',
  password: ''
})

const loginRules: FormRules = {
  policeNumber: [
    { required: true, message: '请输入警号', trigger: 'blur' },
    { min: 3, max: 20, message: '警号长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ]
}

onMounted(async () => {
  // 加载 face-api.js 模型
  await loadFaceApiModels()

  // 检查是否有未完成的登录流程
  if (authStore.loginStep === 'face_verification') {
    loginStep.value = 'face'
    userInfo.value = authStore.user || {}
  }
})

onUnmounted(() => {
  stopCamera()
  clearTimers()
})

// 清理定时器
const clearTimers = () => {
  if (recognitionTimer) {
    clearInterval(recognitionTimer)
    recognitionTimer = null
  }
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

// 加载 face-api.js 模型
const loadFaceApiModels = async () => {
  try {
    ElMessage.info('正在加载人脸识别模型...')

    // 逐个加载模型并提供进度反馈
    await faceapi.nets.faceRecognitionNet.loadFromUri('/models');
    await faceapi.nets.faceLandmark68Net.loadFromUri('/models');
    await faceapi.nets.ssdMobilenetv1.loadFromUri('/models');
    // console.log('开始加载 SSD MobileNet v1 模型...')
    // await faceapi.loadSsdMobilenetv1Model('/')
    // console.log('SSD MobileNet v1 模型加载完成')

    // console.log('开始加载面部关键点模型...')
    // await faceapi.loadFaceLandmarkModel('/')

    // console.log('面部关键点模型加载完成')

    // console.log('开始加载人脸识别模型...')
    // await faceapi.loadFaceRecognitionModel('/')
    // console.log('人脸识别模型加载完成')

    modelsLoaded.value = true
    console.log('所有人脸识别模型加载成功')
  } catch (error) {
    console.error('加载模型失败:', error)
    modelsLoaded.value = false
    ElMessage.error('加载人脸识别模型失败，人脸登录功能不可用')
  }
}

// 第一步：密码验证
const handlePasswordLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true

    console.log('第一步密码验证，警号:', loginForm.policeNumber)

    const result = await authStore.login(loginForm.policeNumber, loginForm.password)

    if (result.step === 'face_verification_required') {
      // 需要人脸识别，获取用户的人脸特征数据
      try {
        const faceResponse = await userAPI.getFaceEncodings({ police_number: loginForm.policeNumber })
        userFaceEncodings.value = faceResponse.data.face_encodings

        if (!userFaceEncodings.value || userFaceEncodings.value.length === 0) {
          ElMessage.error('用户未录入人脸信息，请联系管理员补录')
          return
        }

        loginStep.value = 'face'
        userInfo.value = result.user
        ElMessage.success('密码验证通过，正在启动人脸识别...')
        
        // 自动启动摄像头和人脸识别
        setTimeout(() => {
          startCameraAndAutoRecognize()
        }, 1000) // 1秒后自动启动
      } catch (error: any) {
        console.error('获取人脸特征失败:', error)
        ElMessage.error('获取人脸特征失败，请联系管理员')
      }
    } else {
      // 直接登录成功（向后兼容）
      ElMessage.success('登录成功')
      router.push('/')
    }
  } catch (error: any) {
    console.error('密码验证失败:', error)
    handleLoginError(error)
  } finally {
    loading.value = false
  }
}

// 启动摄像头
const startCamera = async () => {
  if (!modelsLoaded.value) {
    ElMessage.error('人脸识别模型尚未加载完成，请稍后重试')
    return
  }

  try {
    cameraLoading.value = true

    const constraints = {
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user'
      }
    }

    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)

    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      cameraStarted.value = true
      showCamera.value = true
    }
  } catch (error) {
    console.error('启动摄像头失败:', error)
    ElMessage.error('无法访问摄像头，请检查权限设置')
  } finally {
    cameraLoading.value = false
  }
}

// 停止摄像头
const stopCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  cameraStarted.value = false
  stopAutoRecognition()
}

// 启动摄像头并开始自动识别
const startCameraAndAutoRecognize = async () => {
  await startCamera()
  if (cameraStarted.value) {
    // 等待摄像头稳定后开始自动识别
    setTimeout(() => {
      startAutoRecognition()
    }, 1000)
  }
}

// 开始自动识别
const startAutoRecognition = () => {
  if (!cameraStarted.value || !modelsLoaded.value) {
    ElMessage.error('请先启动摄像头并等待模型加载完成')
    return
  }

  autoRecognizing.value = true
  recognitionCountdown.value = 20
  recognitionAttempts.value++

  ElMessage.info(`开始第 ${recognitionAttempts.value} 次自动人脸识别，请保持面部正对摄像头`)

  // 开始倒计时
  countdownTimer = setInterval(() => {
    recognitionCountdown.value--
    if (recognitionCountdown.value <= 0) {
      handleRecognitionTimeout()
    }
  }, 1000)

  // 开始定期尝试识别
  recognitionTimer = setInterval(async () => {
    if (!autoRecognizing.value) return
    
    try {
      await attemptFaceRecognition()
    } catch (error) {
      console.log('识别尝试失败，继续重试...', error)
    }
  }, 2000) // 每2秒尝试一次识别
}

// 停止自动识别
const stopAutoRecognition = () => {
  autoRecognizing.value = false
  clearTimers()
}

// 处理识别超时
const handleRecognitionTimeout = () => {
  stopAutoRecognition()
  
  if (recognitionAttempts.value >= maxAttempts) {
    ElMessage.error(`人脸识别失败，已尝试 ${maxAttempts} 次。请检查光线条件或联系管理员`)
    // 可以选择回到密码登录或其他处理
  } else {
    ElMessage.warning(`第 ${recognitionAttempts.value} 次识别超时，准备重新尝试...`)
    // 3秒后自动重试
    setTimeout(() => {
      if (loginStep.value === 'face' && cameraStarted.value) {
        startAutoRecognition()
      }
    }, 3000)
  }
}

// 尝试人脸识别（自动模式）
const attemptFaceRecognition = async () => {
  if (!videoRef.value) return

  try {
    const video = videoRef.value
    
    // 使用 face-api.js 提取人脸特征
    const currentFeatures = await extractFaceFeatures(video)
    
    // 与用户存储的特征进行比对
    const comparisonResult = compareFaceFeatures(currentFeatures, userFaceEncodings.value)
    
    console.log('自动识别结果:', comparisonResult)
    
    if (comparisonResult.success) {
      // 识别成功，停止自动识别
      stopAutoRecognition()
      
      // 提交验证结果
      const result = await authStore.faceVerify({
        success: comparisonResult.success,
        confidence: comparisonResult.confidence,
        reason: comparisonResult.reason
      })
      
      ElMessage.success(`人脸识别成功！置信度: ${comparisonResult.confidence}%`)
      stopCamera()
      router.push('/')
    }
    // 如果识别失败，继续尝试直到超时
    
  } catch (error: any) {
    // 这里不显示错误消息，因为是自动尝试，失败是正常的
    console.log('自动识别尝试:', error.message)
  }
}

// 计算两个特征向量之间的欧几里得距离
const calculateDistance = (features1: number[], features2: number[]): number => {
  if (features1.length !== features2.length) {
    throw new Error('特征向量维度不匹配')
  }

  let sum = 0
  for (let i = 0; i < features1.length; i++) {
    const diff = features1[i] - features2[i]
    sum += diff * diff
  }

  return Math.sqrt(sum)
}

// 人脸特征比对
const compareFaceFeatures = (currentFeatures: number[], storedEncodings: number[][]): { success: boolean; confidence: number; reason?: string } => {
  if (!storedEncodings || storedEncodings.length === 0) {
    return { success: false, confidence: 0, reason: '用户未注册人脸信息' }
  }

  const threshold = 0.6 // face-api.js 推荐阈值
  let minDistance = Infinity

  // 与所有已存储的特征进行比对
  for (const storedFeatures of storedEncodings) {
    const distance = calculateDistance(currentFeatures, storedFeatures)
    if (distance < minDistance) {
      minDistance = distance
    }
  }

  const confidence = Math.max(0, (1 - minDistance) * 100) // 转换为置信度百分比
  const success = minDistance < threshold

  return {
    success,
    confidence: Math.round(confidence * 100) / 100,
    reason: success ? '人脸匹配成功' : `人脸不匹配，相似度过低 (${confidence.toFixed(2)}%)`
  }
}

// 提取人脸特征
const extractFaceFeatures = async (videoElement: HTMLVideoElement): Promise<number[]> => {
  try {
    const detection = await faceapi
      .detectSingleFace(videoElement)
      .withFaceLandmarks()
      .withFaceDescriptor()

    if (!detection) {
      throw new Error('未检测到人脸，请确保面部正对摄像头')
    }

    const descriptor = detection.descriptor
    if (descriptor.length !== 128) {
      throw new Error(`特征向量维度错误：期望128维，实际${descriptor.length}维`)
    }

    return Array.from(descriptor) as number[]

  } catch (error) {
    console.error('人脸特征提取失败:', error)
    throw error
  }
}

// 人脸识别
const captureFace = async () => {
  if (!videoRef.value || !canvasRef.value) return

  try {
    verifying.value = true

    const video = videoRef.value

    // 使用 face-api.js 提取人脸特征
    const currentFeatures = await extractFaceFeatures(video)

    // 与用户存储的特征进行比对
    const comparisonResult = compareFaceFeatures(currentFeatures, userFaceEncodings.value)

    console.log('人脸比对结果:', comparisonResult)

    // 将比对结果发送给后端
    const result = await authStore.faceVerify({
      success: comparisonResult.success,
      confidence: comparisonResult.confidence,
      reason: comparisonResult.reason
    })

    if (comparisonResult.success) {
      ElMessage.success(`人脸识别成功 (置信度: ${comparisonResult.confidence}%)，登录完成`)
      stopCamera()
      router.push('/')
    } else {
      ElMessage.error(`人脸识别失败: ${comparisonResult.reason}`)
    }

  } catch (error: any) {
    console.error('人脸识别失败:', error)

    const errorMessage = error.message || '人脸识别失败，请重试或联系管理员补录人脸信息'
    ElMessage.error(errorMessage)

    // 向后端报告失败
    try {
      await authStore.faceVerify({
        success: false,
        confidence: 0,
        reason: errorMessage
      })
    } catch (reportError) {
      console.error('报告人脸识别失败状态时出错:', reportError)
    }
  } finally {
    verifying.value = false
  }
}

// 提取人脸特征（模拟）
// 这个函数已经被上面的 extractFaceFeatures 替代，这里保留作为备用

// 重新开始密码登录
const restartPasswordLogin = () => {
  loginStep.value = 'password'
  stopCamera()
  authStore.loginStep = 'password'
  recognitionAttempts.value = 0
}

// 处理登录错误
const handleLoginError = (error: any) => {
  if (error.response?.status === 403) {
    if (error.response.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('账户审核状态异常，请联系管理员')
    }
  } else if (error.response?.status === 401) {
    ElMessage.error('警号或密码错误')
  } else if (error.response?.data?.error) {
    ElMessage.error(error.response.data.error)
  } else if (error.message) {
    ElMessage.error(`登录失败: ${error.message}`)
  } else {
    ElMessage.error('登录失败，请稍后重试')
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 450px;
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
  font-size: 14px;
}

.face-login-section {
  text-align: center;
}

.user-info {
  margin-bottom: 20px;
}

.camera-container {
  margin-bottom: 20px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  background: #f9f9f9;
  position: relative;
}

.camera-container video,
.camera-container canvas {
  max-width: 100%;
  max-height: 300px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.recognition-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  padding: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.countdown-text {
  font-size: 14px;
  font-weight: bold;
  color: #409EFF;
}

.face-controls {
  margin-bottom: 20px;
}

.face-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.login-footer {
  text-align: center;
  width: 100%;
}

.register-link {
  color: #409EFF;
  text-decoration: none;
  margin-left: 4px;
}

.register-link:hover {
  text-decoration: underline;
}

.admin-link {
  color: #E6A23C;
  text-decoration: none;
  margin-left: 4px;
  font-weight: 500;
}

.admin-link:hover {
  text-decoration: underline;
  color: #D0982C;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-button) {
  border-radius: 8px;
  height: 40px;
}
</style>
