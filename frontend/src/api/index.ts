import axios from 'axios'

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

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  withCredentials: true, // 允许携带 cookies
  headers: {
    'Content-Type': 'application/json',
  }
})

// 初始化CSRF token
let csrfInitialized = false

const initializeCSRF = async () => {
  if (!csrfInitialized) {
    try {
      // 首先尝试获取CSRF token
      await axios.get('http://localhost:8000/api/csrf/', { 
        withCredentials: true,
        headers: {
          'Accept': 'application/json',
        }
      })
      csrfInitialized = true
      console.log('CSRF token initialized successfully')
    } catch (error) {
      console.warn('Failed to initialize CSRF token:', error)
    }
  }
}

// 请求拦截器
api.interceptors.request.use(
  async (config) => {
    // 对于所有请求，确保已经初始化CSRF token
    await initializeCSRF()
    
    // 对于需要CSRF保护的方法，添加CSRF token到请求头
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase() || '')) {
      const csrfToken = getCSRFToken()
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken
        console.log('Added CSRF token to request:', csrfToken.substring(0, 8) + '...')
      } else {
        console.warn('No CSRF token found in cookies')
      }
    }
    
    // 对于GET请求到需要认证的端点，也确保有session cookie
    if (config.method?.toLowerCase() === 'get' && config.url?.includes('/users/')) {
      console.log('GET request to authenticated endpoint')
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权错误
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 用户相关API
export const userAPI = {
  // 获取CSRF token
  initCSRF: () => axios.get('http://localhost:8000/api/csrf/', { withCredentials: true }),
  
  login: async (data: { username: string; password: string }) => {
    // 确保在登录前已经获取了CSRF token
    await initializeCSRF()
    return api.post('/users/login/', data)
  },
  
  logout: () => 
    api.post('/users/logout/'),
  register: (data: { username: string; email: string; password: string }) => 
    api.post('/users/', data),
  getProfile: () => 
    api.get('/users/me/'),
  getDashboard: () => 
    api.get('/users/dashboard/'),
}

// 项目相关API
export const projectAPI = {
  list: () => 
    api.get('/projects/'),
  create: (data: { name: string; description?: string }) => 
    api.post('/projects/', data),
  get: (id: number) => 
    api.get(`/projects/${id}/`),
  update: (id: number, data: Partial<{ name: string; description: string }>) => 
    api.put(`/projects/${id}/`, data),
  delete: (id: number) => 
    api.delete(`/projects/${id}/`),
  getMembers: (id: number) => 
    api.get(`/projects/${id}/members/`),
  inviteMember: (id: number, data: { username: string; permission: string }) => 
    api.post(`/projects/${id}/invite_member/`, data),
  removeMember: (id: number, data: { username: string }) => 
    api.delete(`/projects/${id}/remove_member/`, { data }),
  updateMemberPermission: (id: number, data: { username: string; permission: string }) => 
    api.put(`/projects/${id}/update_member_permission/`, data),
}

// 思维导图相关API
export const mindmapAPI = {
  getNodes: (projectId: number) => 
    api.get(`/projects/${projectId}/nodes/`),
  createNode: (projectId: number, data: any) => 
    api.post(`/projects/${projectId}/nodes/`, data),
  updateNode: (projectId: number, nodeId: number, data: any) => 
    api.put(`/projects/${projectId}/nodes/${nodeId}/`, data),
  deleteNode: (projectId: number, nodeId: number) => 
    api.delete(`/projects/${projectId}/nodes/${nodeId}/`),
  getTree: (projectId: number) => 
    api.get(`/projects/${projectId}/nodes/tree/`),
  getSimpleMindMapFormat: (projectId: number) => 
    api.get(`/projects/${projectId}/nodes/simple-mind-map/`),
  getLogs: (projectId: number) => 
    api.get(`/projects/${projectId}/nodes/logs/`),
  getUserStats: (projectId: number) => 
    api.get(`/projects/${projectId}/nodes/stats/`),
}

// 导出初始化函数供外部调用
export { initializeCSRF }

export default api
