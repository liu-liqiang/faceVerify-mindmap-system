<template>
  <div class="face-register-container">
    <el-card class="face-register-card">
      <template #header>
        <div class="card-header">
          <h2>人脸信息录入</h2>
          <p>请录入您的人脸信息以完成注册</p>
        </div>
      </template>

      <div class="face-capture-section">
        <div class="camera-container">
          <video ref="videoRef" autoplay playsinline :style="{ display: showVideo ? 'block' : 'none' }"></video>
          <canvas ref="canvasRef" :style="{ display: showVideo ? 'none' : 'block' }"></canvas>
        </div>

        <div class="capture-controls">
          <el-button v-if="!cameraStarted" type="primary" @click="startCamera" :loading="loading">
            启动摄像头
          </el-button>

          <div v-else class="control-buttons">
            <el-button type="success" @click="captureImage" :disabled="captureCount >= 3">
              拍摄人脸 ({{ captureCount }}/3)
            </el-button>

            <el-button v-if="captureCount > 0" type="warning" @click="resetCapture">
              重新拍摄
            </el-button>

            <el-button v-if="captureCount >= 3" type="primary" @click="submitFaceData" :loading="submitting">
              提交人脸信息
            </el-button>
          </div>
        </div>

        <div class="capture-preview" v-if="capturedImages.length > 0">
          <h4>已拍摄的人脸图片：</h4>
          <div class="preview-images">
            <div v-for="(image, index) in capturedImages" :key="index" class="preview-item">
              <img :src="image" :alt="`人脸图片 ${index + 1}`" />
              <span>第{{ index + 1 }}张</span>
            </div>
          </div>
        </div>

        <div class="tips">
          <el-alert title="拍摄提示" type="info" show-icon :closable="false">
            <p>1. 请确保光线充足，面部清晰可见</p>
            <p>2. 正面拍摄，眼睛直视摄像头</p>
            <p>3. 需要拍摄3张不同角度的照片</p>
            <p>4. 避免佩戴帽子、墨镜等遮挡物</p>
          </el-alert>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { userAPI } from '@/api'
import * as faceapi from 'face-api.js'

const route = useRoute()
const router = useRouter()

const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const loading = ref(false)
const submitting = ref(false)
const cameraStarted = ref(false)
const showVideo = ref(true)
const captureCount = ref(0)
const capturedImages = ref<string[]>([])
const faceDataList = ref<number[][]>([])  // 存储人脸特征向量数组
const modelsLoaded = ref(false)

let mediaStream: MediaStream | null = null

const userId = ref(route.query.userId as string)
const tempToken = ref(route.query.tempToken as string)

onMounted(async () => {
  if (!userId.value || !tempToken.value) {
    ElMessage.error('无效的访问链接')
    router.push('/register')
    return
  }

  // 加载 face-api.js 模型
  await loadFaceApiModels()
})

onUnmounted(() => {
  stopCamera()
})

const loadFaceApiModels = async () => {
  try {
    loading.value = true
    ElMessage.info('正在加载人脸识别模型...')

    // 逐个加载模型并提供进度反馈
    console.log('开始加载 SSD MobileNet v1 模型...')
    await faceapi.nets.ssdMobilenetv1.loadFromUri('/models')
    console.log('SSD MobileNet v1 模型加载完成')

    console.log('开始加载面部关键点模型...')
    await faceapi.nets.faceLandmark68Net.loadFromUri('/models')
    console.log('面部关键点模型加载完成')

    console.log('开始加载人脸识别模型...')
    await faceapi.nets.faceRecognitionNet.loadFromUri('/models')
    console.log('人脸识别模型加载完成')

    modelsLoaded.value = true
    ElMessage.success('人脸识别模型加载成功！')
    console.log('所有人脸识别模型加载成功')
  } catch (error) {
    console.error('加载模型失败:', error)
    modelsLoaded.value = false
    ElMessage.error('加载人脸识别模型失败，请检查网络连接或刷新页面重试')
  } finally {
    loading.value = false
  }
}

const startCamera = async () => {
  if (!modelsLoaded.value) {
    ElMessage.error('请等待人脸识别模型加载完成')
    return
  }

  try {
    loading.value = true

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
      showVideo.value = true
    }
  } catch (error) {
    console.error('启动摄像头失败:', error)
    ElMessage.error('无法访问摄像头，请检查权限设置')
  } finally {
    loading.value = false
  }
}

const stopCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  cameraStarted.value = false
}

const captureImage = async () => {
  if (!videoRef.value || !canvasRef.value) return

  const video = videoRef.value
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')

  if (!ctx) return

  try {
    // 首先使用 face-api.js 提取人脸特征
    const faceFeatures = await extractFaceFeatures(video)

    // 如果特征提取成功，再进行图片拍摄
    // 设置画布尺寸
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // 绘制当前帧
    ctx.drawImage(video, 0, 0)

    // 获取图片数据
    const imageData = canvas.toDataURL('image/jpeg', 0.8)
    capturedImages.value.push(imageData)
    faceDataList.value.push(faceFeatures)

    captureCount.value++
    ElMessage.success(`第${captureCount.value}张人脸图片拍摄成功`)

    if (captureCount.value >= 3) {
      // 拍摄完3张照片后立即停止摄像头
      stopCamera()
      showVideo.value = false
      ElMessage.info('已完成3张照片拍摄，摄像头已关闭，可以提交人脸信息了')
    }
  } catch (error) {
    console.error('人脸特征提取失败:', error)
    ElMessage.error(`人脸特征提取失败：${error instanceof Error ? error.message : '请重新拍摄'}`)
  }
}

const extractFaceFeatures = async (videoElement: HTMLVideoElement): Promise<number[]> => {
  try {
    // 使用 face-api.js 检测人脸和提取特征
    const detection = await faceapi
      .detectSingleFace(videoElement)
      .withFaceLandmarks()
      .withFaceDescriptor()

    if (!detection) {
      throw new Error('未检测到人脸，请确保面部正对摄像头')
    }

    // 检查特征向量的维度
    const descriptor = detection.descriptor
    if (descriptor.length !== 128) {
      throw new Error(`特征向量维度错误：期望128维，实际${descriptor.length}维`)
    }

    // 转换为普通数组
    return Array.from(descriptor) as number[]

  } catch (error) {
    console.error('人脸特征提取失败:', error)
    throw error
  }
}

const resetCapture = async () => {
  captureCount.value = 0
  capturedImages.value = []
  faceDataList.value = []
  showVideo.value = true

  // 如果摄像头被关闭了，重新启动
  if (!cameraStarted.value) {
    await startCamera()
  }

  ElMessage.info('已重置，请重新拍摄')
}

const submitFaceData = async () => {
  if (faceDataList.value.length < 3) {
    ElMessage.error('请先拍摄3张人脸照片')
    return
  }

  try {
    submitting.value = true

    // 提交所有人脸特征数据
    await userAPI.registerFaceForUser(parseInt(userId.value), {
      face_encodings: faceDataList.value,  // 直接发送特征向量数组
      temp_token: tempToken.value
    })

    ElMessage.success('人脸信息录入成功！请等待管理员审核')

    // 停止摄像头
    stopCamera()

    // 跳转到登录页面
    setTimeout(() => {
      router.push('/login')
    }, 2000)

  } catch (error: any) {
    console.error('人脸录入失败:', error)

    if (error.response?.data?.error) {
      ElMessage.error(error.response.data.error)
    } else {
      ElMessage.error('人脸录入失败，请重试')
    }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.face-register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.face-register-card {
  width: 100%;
  max-width: 600px;
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

.face-capture-section {
  text-align: center;
}

.camera-container {
  margin-bottom: 20px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  background: #f9f9f9;
}

.camera-container video,
.camera-container canvas {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.capture-controls {
  margin-bottom: 20px;
}

.control-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.capture-preview {
  margin-bottom: 20px;
}

.capture-preview h4 {
  margin-bottom: 10px;
  color: #333;
}

.preview-images {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.preview-item {
  text-align: center;
}

.preview-item img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid #ddd;
}

.preview-item span {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #666;
}

.tips {
  margin-top: 20px;
}

:deep(.el-button) {
  border-radius: 8px;
}
</style>
