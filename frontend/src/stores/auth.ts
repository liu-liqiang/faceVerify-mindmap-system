import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userAPI } from '@/api'

export interface User {
  id: number
  username: string
  email: string
  avatar?: string
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)
  
  // 登录
  const login = async (username: string, password: string) => {
    try {
      const response = await userAPI.login({ username, password })
      const userData = response.data.user || response.data
      
      user.value = userData
      isAuthenticated.value = true
      
      return userData
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
    }
  }
  
  // 注册
  const register = async (userData: { username: string; email: string; password: string }) => {
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
      return response.data
    } catch (error) {
      // 如果获取失败，清除认证状态
      user.value = null
      isAuthenticated.value = false
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
    login,
    logout,
    register,
    fetchProfile,
    initAuth
  }
})
