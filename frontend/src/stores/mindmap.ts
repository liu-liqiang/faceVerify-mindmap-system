import { defineStore } from 'pinia'
import { ref } from 'vue'
import { mindmapAPI } from '@/api'

export interface MindMapNode {
  id: number
  node_id: string
  parent: number | null
  creator: {
    id: number
    username: string
    email: string
  }
  text: string
  image?: string
  hyperlink?: string
  note?: string
  background_color: string
  font_color: string
  font_size: number
  font_weight: string
  position_x: number
  position_y: number
  extra_data: any
  children_count: number
  can_delete: boolean
  created_at: string
  updated_at: string
}

export interface NodeEditLog {
  id: number
  user: {
    id: number
    username: string
    email: string
  }
  action: 'create' | 'update' | 'delete'
  node_text: string
  old_data?: any
  new_data?: any
  timestamp: string
}

export interface UserStats {
  total_nodes: number
  recent_nodes: MindMapNode[]
  project_total_nodes: number
  user_percentage: number
}

export const useMindMapStore = defineStore('mindmap', () => {
  const nodes = ref<MindMapNode[]>([])
  const treeData = ref<any[]>([])
  const editLogs = ref<NodeEditLog[]>([])
  const userStats = ref<UserStats | null>(null)
  const loading = ref(false)
  
  // WebSocket 连接
  let websocket: WebSocket | null = null
  const isConnected = ref(false)
  const onlineUsers = ref<string[]>([])
  
  // 获取节点列表
  const fetchNodes = async (projectId: number) => {
    loading.value = true
    try {
      const response = await mindmapAPI.getNodes(projectId)
      nodes.value = response.data
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取树形结构数据
  const fetchTreeData = async (projectId: number) => {
    try {
      const response = await mindmapAPI.getTree(projectId)
      treeData.value = response.data
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  // 获取Simple Mind Map格式数据
  const fetchSimpleMindMapData = async (projectId: number) => {
    try {
      const response = await mindmapAPI.getSimpleMindMapFormat(projectId)
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  // 创建节点
  const createNode = async (projectId: number, nodeData: any) => {
    try {
      const response = await mindmapAPI.createNode(projectId, nodeData)
      nodes.value.push(response.data)
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  // 更新节点
  const updateNode = async (projectId: number, nodeId: number, nodeData: any) => {
    try {
      const response = await mindmapAPI.updateNode(projectId, nodeId, nodeData)
      const index = nodes.value.findIndex(n => n.id === nodeId)
      if (index !== -1) {
        nodes.value[index] = response.data
      }
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  // 删除节点
  const deleteNode = async (projectId: number, nodeId: number) => {
    try {
      await mindmapAPI.deleteNode(projectId, nodeId)
      nodes.value = nodes.value.filter(n => n.id !== nodeId)
    } catch (error) {
      throw error
    }
  }
  
  // 获取编辑日志
  const fetchEditLogs = async (projectId: number) => {
    try {
      const response = await mindmapAPI.getLogs(projectId)
      editLogs.value = response.data
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  // 获取用户统计
  const fetchUserStats = async (projectId: number) => {
    try {
      const response = await mindmapAPI.getUserStats(projectId)
      userStats.value = response.data
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  // WebSocket 连接
  const connectWebSocket = (projectId: number) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.close()
    }
    
    const wsUrl = `ws://localhost:8000/ws/mindmap/${projectId}/`
    websocket = new WebSocket(wsUrl)
    
    websocket.onopen = () => {
      isConnected.value = true
      console.log('WebSocket connected')
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }
    
    websocket.onclose = () => {
      isConnected.value = false
      console.log('WebSocket disconnected')
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }
  
  // 处理WebSocket消息
  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'node_created':
        // 添加新节点到列表
        if (!nodes.value.find(n => n.node_id === data.node.id)) {
          nodes.value.push(data.node)
        }
        break
      case 'node_updated':
        // 更新节点
        const updateIndex = nodes.value.findIndex(n => n.node_id === data.node.id)
        if (updateIndex !== -1) {
          nodes.value[updateIndex] = { ...nodes.value[updateIndex], ...data.node }
        }
        break
      case 'node_deleted':
        // 删除节点
        nodes.value = nodes.value.filter(n => n.node_id !== data.node_id)
        break
      case 'online_users':
        onlineUsers.value = data.users
        break
      case 'cursor_moved':
        // 处理其他用户的光标移动
        break
      case 'user_selected':
        // 处理其他用户的选择
        break
      case 'error':
        console.error('WebSocket error:', data.message)
        break
    }
  }
  
  // 发送WebSocket消息
  const sendWebSocketMessage = (message: any) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify(message))
    }
  }
  
  // 断开WebSocket连接
  const disconnectWebSocket = () => {
    if (websocket) {
      websocket.close()
      websocket = null
    }
    isConnected.value = false
  }
  
  return {
    nodes,
    treeData,
    editLogs,
    userStats,
    loading,
    isConnected,
    onlineUsers,
    fetchNodes,
    fetchTreeData,
    fetchSimpleMindMapData,
    createNode,
    updateNode,
    deleteNode,
    fetchEditLogs,
    fetchUserStats,
    connectWebSocket,
    sendWebSocketMessage,
    disconnectWebSocket
  }
})
