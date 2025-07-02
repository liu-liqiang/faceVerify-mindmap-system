<template>
    <div class="face-supplement-container">
        <el-card class="supplement-card">
            <template #header>
                <div class="card-header">
                    <h2>人脸信息补录</h2>
                    <p>为已注册用户补录或更新人脸信息</p>
                </div>
            </template>

            <!-- 第一步：身份验证 -->
            <div v-if="step === 'verify'">
                <el-form ref="verifyFormRef" :model="verifyForm" :rules="verifyRules" label-width="100px">
                    <el-form-item label="警号" prop="policeNumber">
                        <el-input v-model="verifyForm.policeNumber" placeholder="请输入警号" clearable />
                    </el-form-item>

                    <el-form-item label="密码" prop="password">
                        <el-input v-model="verifyForm.password" type="password" placeholder="请输入密码" show-password
                            clearable />
                    </el-form-item>

                    <el-form-item label="手机号码" prop="phoneNumber">
                        <el-input v-model="verifyForm.phoneNumber" placeholder="请输入注册时的手机号码" clearable />
                    </el-form-item>

                    <el-form-item>
                        <el-alert title="身份验证说明" type="info" show-icon :closable="false" style="margin-bottom: 20px">
                            <p>1. 请输入您的警号、密码和注册手机号进行身份验证</p>
                            <p>2. 验证通过后即可重新录入人脸信息</p>
                            <p>3. 新的人脸信息将覆盖原有数据</p>
                        </el-alert>
                    </el-form-item>

                    <el-form-item>
                        <el-button type="primary" :loading="verifying" @click="handleVerify" style="width: 100%"
                            size="large">
                            验证身份
                        </el-button>
                    </el-form-item>

                    <el-form-item>
                        <div class="supplement-footer">
                            <router-link to="/login" class="back-link">
                                返回登录
                            </router-link>
                            <span style="margin: 0 8px;">|</span>
                            <router-link to="/register" class="back-link">
                                新用户注册
                            </router-link>
                        </div>
                    </el-form-item>
                </el-form>
            </div>

            <!-- 第二步：人脸录入 -->
            <div v-else-if="step === 'record'">
                <div class="user-verified">
                    <el-tag size="large" type="success">{{ userInfo.real_name }} ({{ userInfo.police_number }})</el-tag>
                    <p style="margin: 10px 0; color: #666;">身份验证成功，请重新录入人脸信息</p>
                </div>

                <div class="face-capture-section">
                    <div class="camera-container">
                        <video ref="videoRef" autoplay playsinline
                            :style="{ display: showVideo ? 'block' : 'none' }"></video>
                        <canvas ref="canvasRef" :style="{ display: showVideo ? 'none' : 'block' }"></canvas>
                    </div>

                    <div class="capture-controls">
                        <el-button v-if="!cameraStarted" type="primary" @click="startCamera" :loading="cameraLoading">
                            启动摄像头
                        </el-button>

                        <div v-else class="control-buttons">
                            <el-button type="success" @click="captureImage" :disabled="captureCount >= 3">
                                拍摄人脸 ({{ captureCount }}/3)
                            </el-button>

                            <el-button v-if="captureCount > 0" type="warning" @click="resetCapture">
                                重新拍摄
                            </el-button>

                            <el-button v-if="captureCount >= 3" type="primary" @click="submitFaceData"
                                :loading="submitting">
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
            </div>

        </el-card>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { userAPI } from '@/api'
import * as faceapi from 'face-api.js'

const route = useRoute()
const router = useRouter()

const verifyFormRef = ref<FormInstance>()
const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()

const step = ref<'verify' | 'record'>('verify')
const verifying = ref(false)
const cameraLoading = ref(false)
const submitting = ref(false)
const cameraStarted = ref(false)
const showVideo = ref(true)
const captureCount = ref(0)
const capturedImages = ref<string[]>([])
const faceDataList = ref<number[][]>([])  // 存储人脸特征向量数组
const modelsLoaded = ref(false)

const userInfo = ref<any>({})
let mediaStream: MediaStream | null = null

const verifyForm = reactive({
    policeNumber: '',
    password: '',
    phoneNumber: ''
})

const verifyRules: FormRules = {
    policeNumber: [
        { required: true, message: '请输入警号', trigger: 'blur' },
        { min: 3, max: 20, message: '警号长度在 3 到 20 个字符', trigger: 'blur' }
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
    ],
    phoneNumber: [
        { required: true, message: '请输入手机号码', trigger: 'blur' },
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
    ]
}

onMounted(async () => {
    // 加载 face-api.js 模型
    await loadFaceApiModels()

    // 从URL参数中获取警号
    const policeNumber = route.query.police_number as string
    if (policeNumber) {
        verifyForm.policeNumber = policeNumber
    }
})

onUnmounted(() => {
    stopCamera()
})

// 加载 face-api.js 模型
const loadFaceApiModels = async () => {
    try {
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
        ElMessage.error('加载人脸识别模型失败，人脸录入功能不可用。请检查网络连接或刷新页面重试。')
    }
}

// 身份验证
const handleVerify = async () => {
    if (!verifyFormRef.value) return

    try {
        await verifyFormRef.value.validate()
        verifying.value = true

        // 调用身份验证API
        const response = await userAPI.verifyIdentityForFaceSupplement({
            police_number: verifyForm.policeNumber,
            password: verifyForm.password,
            phone_number: verifyForm.phoneNumber
        })

        userInfo.value = response.data.user
        step.value = 'record'
        ElMessage.success('身份验证成功，请重新录入人脸信息')

    } catch (error: any) {
        console.error('身份验证失败:', error)

        if (error.response?.data?.error) {
            ElMessage.error(error.response.data.error)
        } else {
            ElMessage.error('身份验证失败，请检查输入信息')
        }
    } finally {
        verifying.value = false
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
            showVideo.value = true
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
}

// 拍摄图片
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

// 提取人脸特征
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

// 重置拍摄
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

// 提交人脸数据
const submitFaceData = async () => {
    if (faceDataList.value.length < 3) {
        ElMessage.error('请先拍摄3张人脸照片')
        return
    }

    try {
        submitting.value = true

        // 调用人脸补录API
        await userAPI.supplementFaceData({
            user_id: userInfo.value.id,
            face_encodings: faceDataList.value  // 直接发送特征向量数组
        })

        ElMessage.success('人脸信息补录成功！现在可以正常登录了')

        // 停止摄像头
        stopCamera()

        // 跳转到登录页面
        setTimeout(() => {
            router.push('/login')
        }, 2000)

    } catch (error: any) {
        console.error('人脸补录失败:', error)

        if (error.response?.data?.error) {
            ElMessage.error(error.response.data.error)
        } else {
            ElMessage.error('人脸补录失败，请重试')
        }
    } finally {
        submitting.value = false
    }
}
</script>

<style scoped>
.face-supplement-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
}

.supplement-card {
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

.user-verified {
    text-align: center;
    margin-bottom: 20px;
    padding: 20px;
    background: #f0f9ff;
    border-radius: 8px;
    border: 1px solid #e1f5fe;
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

.supplement-footer {
    text-align: center;
    width: 100%;
}

.back-link {
    color: #409EFF;
    text-decoration: none;
}

.back-link:hover {
    text-decoration: underline;
}

:deep(.el-button) {
    border-radius: 8px;
}
</style>
