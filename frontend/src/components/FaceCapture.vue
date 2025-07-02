<template>
  <div class="face-capture">
    <div class="camera-container">
      <video
        ref="videoRef"
        autoplay
        playsinline
        :width="videoWidth"
        :height="videoHeight"
        class="video-stream"
      ></video>
      
      <canvas
        ref="canvasRef"
        :width="videoWidth"
        :height="videoHeight"
        class="capture-canvas"
        v-show="false"
      ></canvas>
      
      <!-- 人脸检测框 -->
      <div
        v-if="faceDetected"
        class="face-overlay"
        :style="{
          left: faceBox.x + 'px',
          top: faceBox.y + 'px',
          width: faceBox.width + 'px',
          height: faceBox.height + 'px'
        }"
      ></div>
    </div>
    
    <div class="capture-info">
      <div class="status-info">
        <el-tag
          :type="faceDetected ? 'success' : 'warning'"
          size="large"
        >
          {{ faceDetected ? '已检测到人脸' : '请将人脸对准摄像头' }}
        </el-tag>
      </div>
      
      <div class="timer-info" v-if="isCapturing">
        <el-progress
          type="circle"
          :percentage="(captureTime / maxCaptureTime) * 100"
          :width="80"
          :stroke-width="6"
          :color="progressColor"
        >
          <span class="timer-text">{{ remainingTime }}s</span>
        </el-progress>
      </div>
      
      <div class="capture-actions">
        <el-button
          v-if="!isCapturing"
          type="primary"
          size="large"
          :disabled="!faceDetected"
          @click="startCapture"
        >
          开始识别
        </el-button>
        
        <el-button
          v-if="isCapturing"
          type="danger"
          size="large"
          @click="stopCapture"
        >
          停止识别
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  maxCaptureTime?: number // 最大捕获时间（秒）
  autoCapture?: boolean   // 是否自动捕获
}

const props = withDefaults(defineProps<Props>(), {
  maxCaptureTime: 20,
  autoCapture: false
})

const emit = defineEmits<{
  faceData: [data: string]
  captureComplete: [success: boolean, data?: string]
  error: [error: string]
}>()

const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const videoWidth = 640
const videoHeight = 480

// 状态
const faceDetected = ref(false)
const isCapturing = ref(false)
const captureTime = ref(0)
const faceBox = ref({ x: 0, y: 0, width: 0, height: 0 })

// 计算属性
const remainingTime = computed(() => props.maxCaptureTime - captureTime.value)
const progressColor = computed(() => {
  const percentage = (captureTime.value / props.maxCaptureTime) * 100
  if (percentage < 50) return '#67C23A'
  if (percentage < 80) return '#E6A23C'
  return '#F56C6C'
})

// 定时器
let stream: MediaStream | null = null
let faceDetectionInterval: number | null = null
let captureTimer: number | null = null
let faceRecognition: any = null

onMounted(async () => {
  await initCamera()
  await loadFaceDetection()
  startFaceDetection()
})

onUnmounted(() => {
  cleanup()
})

const initCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: videoWidth,
        height: videoHeight,
        facingMode: 'user'
      }
    })
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream
    }
  } catch (error) {
    console.error('Error accessing camera:', error)
    emit('error', '无法访问摄像头，请检查权限设置')
  }
}

const loadFaceDetection = async () => {
  try {
    // 这里可以集成face-api.js或其他人脸检测库
    // 为了简化，我们使用模拟的人脸检测
    console.log('Face detection loaded')
  } catch (error) {
    console.error('Error loading face detection:', error)
    emit('error', '人脸检测库加载失败')
  }
}

const startFaceDetection = () => {
  faceDetectionInterval = window.setInterval(() => {
    detectFace()
  }, 100) // 每100ms检测一次
}

const detectFace = () => {
  if (!videoRef.value || !canvasRef.value) return
  
  const canvas = canvasRef.value
  const context = canvas.getContext('2d')
  const video = videoRef.value
  
  if (!context) return
  
  // 将视频帧绘制到canvas
  context.drawImage(video, 0, 0, videoWidth, videoHeight)
  
  // 简化的人脸检测（实际应该使用专业的人脸检测库）
  // 这里模拟检测到人脸
  const mockFaceDetected = Math.random() > 0.3 // 70% 概率检测到人脸
  
  if (mockFaceDetected) {
    faceDetected.value = true
    faceBox.value = {
      x: videoWidth * 0.3,
      y: videoHeight * 0.2,
      width: videoWidth * 0.4,
      height: videoHeight * 0.5
    }
    
    if (props.autoCapture && !isCapturing.value) {
      startCapture()
    }
  } else {
    faceDetected.value = false
  }
}

const startCapture = () => {
  if (!faceDetected.value) {
    ElMessage.warning('请先将人脸对准摄像头')
    return
  }
  
  isCapturing.value = true
  captureTime.value = 0
  
  captureTimer = window.setInterval(() => {
    captureTime.value++
    
    if (captureTime.value >= props.maxCaptureTime) {
      // 时间到，尝试捕获人脸
      captureFace()
    }
  }, 1000)
}

const stopCapture = () => {
  if (captureTimer) {
    clearInterval(captureTimer)
    captureTimer = null
  }
  
  isCapturing.value = false
  captureTime.value = 0
}

const captureFace = () => {
  if (!videoRef.value || !canvasRef.value) {
    emit('error', '摄像头未准备就绪')
    return
  }
  
  const canvas = canvasRef.value
  const context = canvas.getContext('2d')
  const video = videoRef.value
  
  if (!context) {
    emit('error', '无法获取Canvas上下文')
    return
  }
  
  // 绘制当前视频帧
  context.drawImage(video, 0, 0, videoWidth, videoHeight)
  
  // 转换为Base64数据
  const faceData = canvas.toDataURL('image/jpeg', 0.8)
  
  stopCapture()
  
  // 发送人脸数据
  emit('faceData', faceData)
  emit('captureComplete', true, faceData)
  
  ElMessage.success('人脸捕获成功')
}

const cleanup = () => {
  if (faceDetectionInterval) {
    clearInterval(faceDetectionInterval)
  }
  
  if (captureTimer) {
    clearInterval(captureTimer)
  }
  
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
  }
}

// 暴露给父组件的方法
defineExpose({
  startCapture,
  stopCapture,
  captureFace
})
</script>

<style scoped>
.face-capture {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px;
}

.camera-container {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.video-stream {
  display: block;
  border-radius: 12px;
}

.capture-canvas {
  position: absolute;
  top: 0;
  left: 0;
}

.face-overlay {
  position: absolute;
  border: 3px solid #67C23A;
  border-radius: 8px;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.3);
  transition: all 0.3s ease;
}

.capture-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-width: 200px;
}

.status-info {
  text-align: center;
}

.timer-info {
  display: flex;
  justify-content: center;
}

.timer-text {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.capture-actions {
  display: flex;
  gap: 12px;
}

:deep(.el-progress-circle) {
  width: 80px !important;
  height: 80px !important;
}
</style>
