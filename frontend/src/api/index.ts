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

  // 第一步：账号密码登录
  login: async (data: { police_number: string; password: string }) => {
    // 确保在登录前已经获取了CSRF token
    await initializeCSRF()
    return api.post('/users/login/', data)
  },

  // 第二步：人脸识别验证
  faceVerify: async (data: { session_token: string; verification_result: { success: boolean; confidence?: number; reason?: string } }) => {
    return api.post('/users/face_verify/', data)
  },

  // 人脸录入
  registerFace: async (data: { user_id: number; face_encodings: number[][] }) => {
    return api.post('/users/register_face/', data)
  },

  logout: () =>
    api.post('/users/logout/'),
  register: (data: {
    real_name: string;
    police_number: string;
    phone_number: string;
    department: string;
    password: string
  }) =>
    api.post('/users/', data),
  getProfile: () =>
    api.get('/users/me/'),
  getDashboard: () =>
    api.get('/users/dashboard/'),
  // 用户管理相关API
  getPendingUsers: () =>
    api.get('/users/pending_users/'),
  approveUser: (userId: number, data: { status: string; rejection_reason?: string }) =>
    api.post(`/users/${userId}/approve_user/`, data),
  registerFaceForUser: (userId: number, data: { face_encodings: number[][]; temp_token?: string }) =>
    api.post(`/users/${userId}/register-face/`, data),
  // 人脸补录相关API
  verifyIdentityForFaceSupplement: (data: { police_number: string; password: string; phone_number: string }) =>
    api.post('/users/verify-identity-supplement/', data),
  supplementFaceData: (data: { user_id: number; face_encodings: number[][] }) =>
    api.post('/users/supplement-face/', data),
  // 获取用户人脸特征用于前端比对
  getFaceEncodings: (data: { police_number: string }) =>
    api.post('/users/get_face_encodings/', data),
  // 管理员登录API
  adminLogin: (data: { username: string; password: string }) =>
    api.post('/users/admin-login/', data),
  // 管理员用户管理API
  getAdminUsers: (params?: { status?: string; search?: string }) =>
    api.get('/users/admin_users/', { params }),
  updateUserStatus: (userId: number, data: { status: string; rejection_reason?: string }) =>
    api.post(`/users/${userId}/approve_user/`, data),
  // 根据单位获取用户列表
  getUsersByDepartment: (department: string) =>
    api.get(`/users/users_by_department/?department=${department}`),
  // 根据警号获取用户信息
  getUserByPoliceNumber: async (policeNumber: string) => {
    await initializeCSRF()
    return api.get(`/users/by-police-number/${policeNumber}/`)
  },
}

// 项目相关API
export const projectAPI = {
  list: () =>
    api.get('/projects/'),
  create: (data: FormData | { name: string; case_number: string; filing_unit: string; case_summary: string }) => {
    if (data instanceof FormData) {
      return api.post('/projects/', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      })
    }
    return api.post('/projects/', data)
  },
  get: (id: number) =>
    api.get(`/projects/${id}/`),
  update: (id: number, data: Partial<{ name: string; case_number: string; filing_unit: string; case_summary: string }>) =>
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
  uploadAttachment: (id: number, file: any, description?: string) => {
    const formData = new FormData()

    // 确保文件是有效的
    if (!(file instanceof File) && typeof file === 'object') {
      // 如果不是File实例但是有类似文件的属性，尝试创建一个Blob
      if (file && 'type' in file && 'name' in file && 'size' in file) {
        const fileType = file.type as string;
        const fileName = file.name as string;

        // 如果有arrayBuffer或blob属性，使用它来创建Blob
        if ('arrayBuffer' in file) {
          const blob = new Blob([file as BlobPart], { type: fileType });
          formData.append('file', blob, fileName);
        } else {
          // 否则直接尝试作为文件附加
          formData.append('file', file as Blob, fileName);
        }
      } else {
        console.error('提供的文件对象无效:', file);
        return Promise.reject(new Error('无效的文件对象'));
      }
    } else {
      // 正常的File对象
      formData.append('file', file as File);
    }

    // 添加描述（如果有）
    if (description) {
      formData.append('description', description);
    }

    // 安全地记录文件信息
    const fileName = file.name ? file.name : '未知文件';
    const fileSize = file.size ? file.size : '未知大小';
    const fileType = file.type ? file.type : '未知类型';

    console.log(`准备上传文件到项目(${id})，文件名: ${fileName}, 大小: ${fileSize}, 类型: ${fileType}`);

    return api.post(`/projects/${id}/upload_attachment/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      // 添加上传进度回调
      onUploadProgress: (progressEvent: any) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
        console.log(`文件上传进度: ${percentCompleted}%`);
      }
    });
  },
  getAttachments: (id: number) =>
    api.get(`/projects/${id}/attachments/`),
  downloadAttachment: (projectId: number, attachmentId: number) =>
    api.get(`/projects/${projectId}/attachments/${attachmentId}/download/`, {
      responseType: 'blob'
    }),
  deleteAttachment: (projectId: number, attachmentId: number) =>
    api.delete(`/projects/${projectId}/attachments/${attachmentId}/`),
}

// 思维导图相关API
export const mindmapAPI = {
  // 原有的基于项目的API路径
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

  // 新增的直接操作API（匹配前端需求）
  // 创建节点 - 支持文件上传
  createNodeWithProjectId: async (data: {
    projectId: number;
    data: any;
    parent_uid?: string;
    image?: File;
    attachment?: File;
  }) => {
    // 确保CSRF token已初始化
    await initializeCSRF()

    // 创建 FormData 对象用于文件上传
    const formData = new FormData()
    formData.append('projectId', data.projectId.toString())
    formData.append('data', JSON.stringify(data.data))

    if (data.parent_uid) {
      formData.append('parent_uid', data.parent_uid)
    }

    // 添加图片文件（如果有）
    if (data.image && data.image instanceof File) {
      formData.append('image', data.image)
    }

    // 添加附件文件（如果有）
    if (data.attachment && data.attachment instanceof File) {
      formData.append('attachment', data.attachment)
    }

    // 获取CSRF token
    const csrfToken = getCSRFToken()

    return axios.post('http://localhost:8000/api/mindmaps/nodes/create/', formData, {
      withCredentials: true,
      headers: {
        'X-CSRFToken': csrfToken || '',
        // 注意：不要设置 Content-Type，让浏览器自动设置 multipart/form-data
      }
    })
  },

  // 更新节点
  updateNodeByUid: async (data: {
    node_uid: string;
    projectId: number;
    data: any;
  }) => {
    await initializeCSRF()
    const csrfToken = getCSRFToken()

    return axios.put('http://localhost:8000/api/mindmaps/nodes/update/', data, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || '',
      }
    })
  },

  // 删除节点
  deleteNodeByUid: async (nodeUid: string, projectId: number) => {
    await initializeCSRF()
    const csrfToken = getCSRFToken()

    return axios.delete(`http://localhost:8000/api/mindmaps/nodes/${nodeUid}/`, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || '',
      },
      data: {
        projectId: projectId
      }
    })
  },

  // 移动节点
  moveNode: async (data: {
    node_uid: string;
    new_parent_uid?: string;
    old_parent_uid?: string;
    projectId: number;
  }) => {
    await initializeCSRF()
    const csrfToken = getCSRFToken()

    return axios.put('http://localhost:8000/api/mindmaps/nodes/move/', data, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || '',
      }
    })
  },

  // 批量更新节点
  batchUpdate: async (data: {
    projectId: number;
    changes: Array<{
      action: string;
      node_uid?: string;
      node_data?: any;
    }>;
  }) => {
    await initializeCSRF()
    const csrfToken = getCSRFToken()

    return axios.post('http://localhost:8000/api/mindmaps/batch-update/', data, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || '',
      }
    })
  },

  // 批量更新节点（优化版本）
  batchUpdateOptimized: async (data: {
    projectId: number;
    changes: Array<{
      action: string;
      node_uid?: string;
      node_data?: any;
      parent_uid?: string;
    }>;
  }) => {
    await initializeCSRF()
    const csrfToken = getCSRFToken()

    return axios.post('http://localhost:8000/api/mindmaps/batch-update-optimized/', data, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || '',
      }
    })
  },

  // 创建默认结构
  createDefaultStructure: async (projectId: number) => {
    await initializeCSRF()
    const csrfToken = getCSRFToken()

    return axios.post('http://localhost:8000/api/mindmaps/create-default-structure/', {
      projectId: projectId
    }, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || '',
      }
    })
  },

  // 获取 Simple Mind Map 格式数据（新路径）
  getSimpleMindMapFormatNew: async (projectId: number) => {
    await initializeCSRF()

    return axios.get(`http://localhost:8000/api/projects/${projectId}/nodes/simple-mind-map-format/`, {
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      }
    })
  },
}

// 导出初始化函数供外部调用
export { initializeCSRF }

export default api
