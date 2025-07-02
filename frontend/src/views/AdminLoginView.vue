<template>
    <div class="admin-login-container">
        <div class="admin-login-card">
            <div class="card-header">
                <div class="admin-logo">
                    <el-icon :size="48">
                        <Setting />
                    </el-icon>
                </div>
                <h2>管理员后台登录</h2>
                <p>Django Admin 管理系统</p>
            </div>

            <el-form :model="formData" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
                <el-form-item prop="username">
                    <el-input v-model="formData.username" placeholder="管理员用户名" size="large" :prefix-icon="User" />
                </el-form-item>

                <el-form-item prop="password">
                    <el-input v-model="formData.password" type="password" placeholder="管理员密码" size="large"
                        :prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
                </el-form-item>

                <el-form-item>
                    <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="login-button">
                        <span v-if="!loading">登录管理后台</span>
                        <span v-else>正在验证...</span>
                    </el-button>
                </el-form-item>
            </el-form>

            <div class="admin-footer">
                <p>
                    <el-link @click="$router.push('/login')" type="primary">
                        <el-icon>
                            <ArrowLeft />
                        </el-icon>
                        返回用户登录
                    </el-link>
                </p>
                <p class="admin-note">
                    <el-icon>
                        <Warning />
                    </el-icon>
                    仅限系统管理员使用
                </p>
            </div>
        </div>

        <!-- 管理员功能说明 -->
        <div class="admin-features">
            <h3>管理员功能</h3>
            <ul>
                <li><el-icon>
                        <User />
                    </el-icon> 用户管理和审核</li>
                <li><el-icon>
                        <Document />
                    </el-icon> 数据库管理</li>
                <li><el-icon>
                        <Setting />
                    </el-icon> 系统配置</li>
                <li><el-icon>
                        <Monitor />
                    </el-icon> 系统监控</li>
            </ul>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Setting, ArrowLeft, Warning, Document, Monitor } from '@element-plus/icons-vue'
import { userAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const formData = reactive({
    username: '',
    password: ''
})

const rules = {
    username: [
        { required: true, message: '请输入管理员用户名', trigger: 'blur' }
    ],
    password: [
        { required: true, message: '请输入管理员密码', trigger: 'blur' }
    ]
}

const handleLogin = async () => {
    if (!formRef.value) return

    try {
        await formRef.value.validate()
        loading.value = true

        // 调用管理员登录API
        const response = await userAPI.adminLogin({
            username: formData.username,
            password: formData.password
        })

        if (response.data.success) {
            ElMessage.success('管理员验证成功，正在验证session状态...')

            // 测试认证状态
            try {
                const testResponse = await axios.get('http://localhost:8000/api/test-auth/', {
                    withCredentials: true,
                    headers: {
                        'Accept': 'application/json',
                    }
                })
                console.log('认证状态测试结果:', testResponse.data)

                if (testResponse.data.is_authenticated) {
                    ElMessage.success('Session建立成功，正在跳转...')

                    // 设置管理员用户信息到store
                    const adminUser = response.data.user
                    authStore.user = adminUser
                    authStore.isAuthenticated = true

                    // 初始化CSRF token
                    try {
                        await userAPI.initCSRF()
                    } catch (error) {
                        console.warn('CSRF token initialization failed:', error)
                    }

                    // 跳转到用户管理界面
                    setTimeout(() => {
                        router.push('/user-management')
                    }, 1000)
                } else {
                    ElMessage.error('Session建立失败，请重试')
                }
            } catch (testError) {
                console.error('认证状态测试失败:', testError)
                ElMessage.error('认证状态验证失败')
            }
        }

    } catch (error: any) {
        const errorMessage = error.response?.data?.error || '登录失败'
        ElMessage.error(errorMessage)
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.admin-login-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    gap: 40px;
}

.admin-login-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    padding: 40px;
    width: 100%;
    max-width: 400px;
}

.card-header {
    text-align: center;
    margin-bottom: 32px;
}

.admin-logo {
    color: #1e3c72;
    margin-bottom: 16px;
}

.card-header h2 {
    color: #1e3c72;
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 600;
}

.card-header p {
    color: #666;
    margin: 0;
    font-size: 14px;
}

.login-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 500;
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    border: none;
}

.login-button:hover {
    background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
}

.admin-footer {
    text-align: center;
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #eee;
}

.admin-footer p {
    margin: 8px 0;
}

.admin-note {
    color: #f56c6c;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
}

.admin-features {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 32px;
    color: white;
    max-width: 300px;
}

.admin-features h3 {
    margin: 0 0 20px 0;
    font-size: 20px;
    font-weight: 600;
}

.admin-features ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.admin-features li {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    font-size: 14px;
}

.admin-features li:last-child {
    margin-bottom: 0;
}

:deep(.el-form-item__label) {
    font-weight: 500;
    color: #1e3c72;
}

:deep(.el-input__wrapper) {
    border-radius: 8px;
    height: 48px;
}

:deep(.el-button) {
    border-radius: 8px;
}
</style>
