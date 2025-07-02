<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <div class="card-header">
          <h2>公安人员注册</h2>
          <p>请先填写基本信息，然后录入人脸信息</p>
        </div>
      </template>

      <el-form ref="registerFormRef" :model="registerForm" :rules="registerRules" label-width="100px"
        @submit.prevent="handleRegister">
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="registerForm.realName" placeholder="请输入真实姓名" clearable />
        </el-form-item>

        <el-form-item label="警号" prop="policeNumber">
          <el-input v-model="registerForm.policeNumber" placeholder="请输入警号（将作为登录用户名）" clearable />
        </el-form-item>

        <el-form-item label="手机号码" prop="phoneNumber">
          <el-input v-model="registerForm.phoneNumber" placeholder="请输入11位手机号码" clearable />
        </el-form-item>

        <el-form-item label="所属单位" prop="department">
          <el-select v-model="registerForm.department" placeholder="请选择所属单位" style="width: 100%">
            <el-option v-for="unit in unitOptions" :key="unit.value" :label="unit.label" :value="unit.value" />
          </el-select>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="请输入密码（至少6位）" show-password clearable />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password clearable
            @keyup.enter="handleRegister" />
        </el-form-item>

        <el-form-item>
          <el-alert title="注册说明" type="info" show-icon :closable="false" style="margin-bottom: 20px">
            <p>1. 填写完信息后将直接进入人脸录入环节</p>
            <p>2. 人脸录入完成后需要管理员审核才能使用系统</p>
            <p>3. 请确保填写信息真实有效</p>
          </el-alert>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleRegister" style="width: 100%" size="large">
            录入人脸
          </el-button>
        </el-form-item>

        <el-form-item>
          <div class="register-footer">
            <span>已有账户？</span>
            <router-link to="/login" class="login-link">
              立即登录
            </router-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const registerFormRef = ref<FormInstance>()
const loading = ref(false)

// 单位选项
const unitOptions = [
  { value: 'direct', label: '市局直属部门' },
  { value: 'tianyuan', label: '天元分局' },
  { value: 'lusong', label: '芦淞分局' },
  { value: 'hetang', label: '荷塘分局' },
  { value: 'shifeng', label: '石峰分局' },
  { value: 'dongjiabai', label: '董家塅分局' },
  { value: 'kaifaqu', label: '经开区分局' },
  { value: 'lukou', label: '渌口分局' },
  { value: 'liling', label: '醴陵市公安局' },
  { value: 'youxian', label: '攸县公安局' },
  { value: 'chaling', label: '茶陵县公安局' },
  { value: 'yanling', label: '炎陵县公安局' }
]

const registerForm = reactive({
  realName: '',
  policeNumber: '',
  phoneNumber: '',
  department: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const validatePhone = (rule: any, value: string, callback: any) => {
  const phoneReg = /^1[3-9]\d{9}$/
  if (!phoneReg.test(value)) {
    callback(new Error('请输入正确的手机号码'))
  } else {
    callback()
  }
}

const validatePoliceNumber = (rule: any, value: string, callback: any) => {
  const policeReg = /^[A-Za-z0-9]{3,20}$/
  if (!policeReg.test(value)) {
    callback(new Error('警号只能包含字母和数字，长度3-20位'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' },
    { min: 2, max: 50, message: '姓名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  policeNumber: [
    { required: true, message: '请输入警号', trigger: 'blur' },
    { validator: validatePoliceNumber, trigger: 'blur' }
  ],
  phoneNumber: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    { validator: validatePhone, trigger: 'blur' }
  ],
  department: [
    { required: true, message: '请选择所属单位', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()
    loading.value = true

    console.log('开始注册，数据:', {
      real_name: registerForm.realName,
      police_number: registerForm.policeNumber,
      phone_number: registerForm.phoneNumber,
      department: registerForm.department,
      password: registerForm.password
    })

    const response = await authStore.register({
      real_name: registerForm.realName,
      police_number: registerForm.policeNumber,
      phone_number: registerForm.phoneNumber,
      department: registerForm.department,
      password: registerForm.password
    })

    console.log('注册成功，响应数据:', response)

    ElMessage.success('信息提交成功，现在开始录入人脸')

    // 跳转到人脸录入页面，传递临时token
    console.log('即将跳转到人脸录入页面，参数:', {
      userId: response.user_id,
      tempToken: response.temp_token
    })

    router.push({
      name: 'FaceRegister',
      query: {
        userId: response.user_id,
        tempToken: response.temp_token
      }
    })
  } catch (error: any) {
    console.error('Register error:', error)

    if (error.response?.data) {
      const errorData = error.response.data
      if (errorData.police_number) {
        ElMessage.error(Array.isArray(errorData.police_number) ? errorData.police_number[0] : errorData.police_number)
      } else if (errorData.phone_number) {
        ElMessage.error(Array.isArray(errorData.phone_number) ? errorData.phone_number[0] : errorData.phone_number)
      } else if (errorData.error) {
        ElMessage.error(errorData.error)
      } else if (errorData.non_field_errors) {
        ElMessage.error(Array.isArray(errorData.non_field_errors) ? errorData.non_field_errors[0] : errorData.non_field_errors)
      } else {
        ElMessage.error('注册失败，请检查输入信息')
      }
    } else if (error.message) {
      ElMessage.error(`注册失败: ${error.message}`)
    } else {
      ElMessage.error('注册失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
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

.register-footer {
  text-align: center;
  width: 100%;
}

.login-link {
  color: #409EFF;
  text-decoration: none;
  margin-left: 4px;
}

.login-link:hover {
  text-decoration: underline;
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
