import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userAPI } from '@/api'

export interface User {
  id: number
  username: string
  real_name: string
  police_number: string
  phone_number: string
  department: string
  department_display: string
  status: string
  status_display: string
  is_face_registered: boolean
  is_superuser?: boolean
  is_staff?: boolean
  approved_by?: string
  approved_at?: string
}

export interface RegisterData {
  real_name: string
  police_number: string
  phone_number: string
  department: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)
  const loginStep = ref<'password' | 'face_verification' | 'face_registration' | 'completed'>('password')
  const sessionToken = ref<string>('')

  // 第一步：账号密码登录
  const login = async (policeNumber: string, password: string) => {
    try {
      const response = await userAPI.login({ police_number: policeNumber, password })
      const data = response.data

      if (data.step === 'face_registration_required') {
        // 需要录入人脸
        loginStep.value = 'face_registration'
        return {
          step: 'face_registration_required',
          message: data.message,
          user_id: data.user_id,
          police_number: data.police_number
        }
      } else if (data.step === 'face_verification_required') {
        // 需要人脸识别验证
        loginStep.value = 'face_verification'
        sessionToken.value = data.session_token
        return {
          step: 'face_verification_required',
          message: data.message,
          user: data.user,
          session_token: data.session_token
        }
      } else {
        // 直接登录成功（向后兼容）
        user.value = data.user || data
        isAuthenticated.value = true
        loginStep.value = 'completed'
        return data
      }
    } catch (error) {
      loginStep.value = 'password'
      throw error
    }
  }

  // 第二步：人脸识别验证
  const faceVerify = async (verificationResult: { success: boolean; confidence?: number; reason?: string }) => {
    try {
      const response = await userAPI.faceVerify({
        session_token: sessionToken.value,
        verification_result: verificationResult
      })

      const userData = response.data.user
      user.value = userData
      isAuthenticated.value = true
      loginStep.value = 'completed'

      return response.data
    } catch (error) {
      throw error
    }
  }

  // 人脸录入
  const registerFace = async (userId: number, faceData: string) => {
    try {
      const response = await userAPI.registerFace({
        user_id: userId,
        face_data: faceData
      })
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 登出
  const logout = async () => {
    try {
      await userAPI.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      user.value = null
      isAuthenticated.value = false
      loginStep.value = 'password'
      sessionToken.value = ''
    }
  }

  // 注册
  const register = async (userData: RegisterData) => {
    try {
      const response = await userAPI.register(userData)
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 获取用户信息
  const fetchProfile = async () => {
    try {
      const response = await userAPI.getProfile()
      user.value = response.data
      isAuthenticated.value = true
      loginStep.value = 'completed'
      return response.data
    } catch (error) {
      // 如果获取失败，清除认证状态
      user.value = null
      isAuthenticated.value = false
      loginStep.value = 'password'
      throw error
    }
  }

  // 初始化认证状态
  const initAuth = async () => {
    try {
      await fetchProfile()
    } catch (error) {
      // 认证失效，清除状态
      logout()
    }
  }

  return {
    user,
    isAuthenticated,
    loginStep,
    sessionToken,
    login,
    faceVerify,
    registerFace,
    logout,
    register,
    fetchProfile,
    initAuth
  }
})
