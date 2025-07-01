<template>
  <div class="mindmap-view">
    <AppLayout>
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <h1>{{ projectInfo?.name || '思维导图编辑器' }}</h1>
            <span class="project-info">{{ projectInfo?.description }}</span>
          </div>
          <div class="header-actions">
            <el-button-group>
              <el-button @click="exportMindMap" type="primary">
                <el-icon><Download /></el-icon>
                导出
              </el-button>
              <el-button @click="saveMindMap" type="success" :loading="saving">
                <el-icon><Select /></el-icon>
                保存
              </el-button>
              <el-button @click="$router.back()">
                <el-icon><ArrowLeft /></el-icon>
                返回
              </el-button>
            </el-button-group>
          </div>
        </div>
      </template>
      
      <!-- 工具栏 -->
      <div class="toolbar">
        <el-space>
          <el-button size="small" @click="addNode">
            <el-icon><Plus /></el-icon>
            添加节点
          </el-button>
          <el-button size="small" @click="deleteNode" :disabled="!selectedNode">
            <el-icon><Delete /></el-icon>
            删除节点
          </el-button>
          <el-divider direction="vertical" />
          <el-button size="small" @click="zoomIn">
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button size="small" @click="zoomOut">
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button size="small" @click="resetZoom">
            适应画布
          </el-button>
          <el-divider direction="vertical" />
          <span class="online-users">
            在线用户: {{ onlineUsers.length }}
          </span>
        </el-space>
      </div>
      
      <!-- 思维导图容器 -->
      <div class="mindmap-container" :class="{ 'has-property-panel': selectedNode }">
        <div 
          ref="mindMapContainer" 
          id="mindMapContainer"
          class="mindmap-canvas"
        ></div>
        
        <!-- 属性面板 -->
        <div v-if="selectedNode" class="property-panel">
          <h4>节点属性</h4>
          
          <!-- 节点文本 -->
          <div class="property-item">
            <label>节点文本</label>
            <el-input 
              v-model="nodeText" 
              @blur="updateNodeText"
              @keyup.enter="updateNodeText"
              placeholder="输入节点文本"
            />
          </div>
          
          <!-- 节点颜色 -->
          <div class="property-item">
            <label>背景颜色</label>
            <el-color-picker 
              v-model="nodeColor" 
              @change="updateNodeColor"
              size="default"
            />
          </div>
          
          <!-- 节点备注 -->
          <div class="property-item">
            <label>备注</label>
            <el-input 
              v-model="nodeNote" 
              type="textarea" 
              @blur="updateNodeNote"
              placeholder="添加备注..."
              :rows="3"
            />
          </div>
          
          <!-- 标签管理 -->
          <div class="property-item">
            <label>标签</label>
            <div class="tags-container">
              <el-tag
                v-for="tag in nodeTags"
                :key="tag"
                closable
                @close="removeTag(tag)"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-if="inputVisible"
                ref="inputRef"
                v-model="inputValue"
                class="tag-input"
                size="small"
                @blur="handleInputConfirm"
                @keyup.enter="handleInputConfirm"
                placeholder="新标签"
              />
              <el-button
                v-else
                class="button-new-tag"
                size="small"
                @click="showInput"
              >
                + 添加标签
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 连接状态指示器 -->
      <div class="connection-status">
        <el-tag :type="connectionStatus === 'connected' ? 'success' : 'danger'">
          {{ connectionStatus === 'connected' ? '已连接' : '连接断开' }}
        </el-tag>
      </div>
    </AppLayout>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, 
  Download, 
  Select, 
  Plus, 
  Delete, 
  ZoomIn, 
  ZoomOut 
} from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import { useMindMapStore } from '@/stores/mindmap'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'

// 导入 simple-mind-map
import MindMap from 'simple-mind-map'
import 'simple-mind-map/dist/simpleMindMap.esm.css'

const route = useRoute()
const router = useRouter()
const mindmapStore = useMindMapStore()
const projectStore = useProjectStore()
const authStore = useAuthStore()

// 响应式数据
const mindMapContainer = ref<HTMLElement>()
const mindMapInstance = ref<any>()
const projectInfo = ref<any>()
const saving = ref(false)
const selectedNode = ref<any>()
const onlineUsers = ref<any[]>([])
const connectionStatus = ref<'connected' | 'disconnected'>('disconnected')

// 节点属性
const nodeText = ref('')
const nodeNote = ref('')
const nodeTags = ref<string[]>([])
const nodeColor = ref('#409EFF')

// 标签输入
const inputVisible = ref(false)
const inputValue = ref('')
const inputRef = ref()

// 获取项目ID
const projectId = parseInt(route.params.id as string)

// 初始化
onMounted(async () => {
  await initProject()
  await initMindMap()
  // 暂时注释掉 WebSocket 连接，先专注于基本功能
  // await connectWebSocket()
})

onUnmounted(() => {
  disconnectWebSocket()
  if (mindMapInstance.value) {
    mindMapInstance.value.destroy()
  }
})

// 初始化项目信息
const initProject = async () => {
  try {
    projectInfo.value = await projectStore.fetchProject(projectId)
  } catch (error) {
    ElMessage.error('获取项目信息失败')
    router.push('/projects')
  }
}

// 初始化思维导图
const initMindMap = async () => {
  // 等待DOM渲染完成
  await nextTick()
  
  // 多次检查容器元素是否存在
  let retryCount = 0
  const maxRetries = 10
  
  while (!mindMapContainer.value && retryCount < maxRetries) {
    await new Promise(resolve => setTimeout(resolve, 100))
    retryCount++
  }
  
  if (!mindMapContainer.value) {
    console.error('思维导图容器元素未找到，容器ref:', mindMapContainer.value)
    ElMessage.error('思维导图容器初始化失败')
    return
  }

  console.log('容器元素已找到:', mindMapContainer.value)

  // 检查容器元素的宽高是否有效
  const checkContainerSize = () => {
    const rect = mindMapContainer.value!.getBoundingClientRect()
    return rect.width > 0 && rect.height > 0
  }

  // 如果容器没有尺寸，手动设置
  if (!checkContainerSize()) {
    mindMapContainer.value!.style.width = '100%'
    mindMapContainer.value!.style.height = '100%'
    mindMapContainer.value!.style.minHeight = '600px'
    mindMapContainer.value!.style.minWidth = '800px'
    console.log('手动设置容器尺寸')
  }

  // 等待容器元素有宽高
  let sizeRetryCount = 0
  const maxSizeRetries = 20
  
  while (!checkContainerSize() && sizeRetryCount < maxSizeRetries) {
    await new Promise(resolve => setTimeout(resolve, 50))
    sizeRetryCount++
  }

  if (!checkContainerSize()) {
    console.error('容器元素宽高为0:', mindMapContainer.value!.getBoundingClientRect())
    ElMessage.error('思维导图容器尺寸异常')
    return
  }

  console.log('容器元素尺寸正常:', mindMapContainer.value!.getBoundingClientRect())

  try {
    // 获取思维导图数据
    const mindmapData = await mindmapStore.fetchSimpleMindMapData(projectId)
    
    console.log('获取的思维导图数据:', mindmapData)
    
    // 等待一下确保容器完全渲染
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // 再次检查容器尺寸
    const finalRect = mindMapContainer.value!.getBoundingClientRect()
    console.log('最终容器尺寸:', finalRect)
    
    // 创建思维导图实例
    mindMapInstance.value = new MindMap({
      el: mindMapContainer.value,
      data: mindmapData || {
        data: {
          text: '中心主题',
          expand: true,
          uid: 'root'
        },
        children: []
      },
      theme: 'default',
      layout: 'logicalStructure',
      enableFreeDrag: true,
      customNoteContentShow: {
        show: true
      }
    })

    console.log('思维导图实例创建成功:', mindMapInstance.value)

    // 绑定事件
    bindMindMapEvents()
    
    ElMessage.success('思维导图加载成功')
  } catch (error: any) {
    console.error('思维导图初始化失败:', error)
    ElMessage.error(`思维导图初始化失败: ${error?.message || '未知错误'}`)
  }
}

// 绑定思维导图事件
const bindMindMapEvents = () => {
  if (!mindMapInstance.value) return

  // 节点选中事件
  mindMapInstance.value.on('node_active', (node: any) => {
    selectedNode.value = node
    if (node) {
      nodeText.value = node.getData('text') || ''
      nodeNote.value = node.getData('note') || ''
      nodeTags.value = node.getData('tags') || []
      nodeColor.value = node.getStyle('fillColor') || '#409EFF'
    }
  })

  // 节点取消选中事件
  mindMapInstance.value.on('node_unactive', () => {
    selectedNode.value = null
    nodeText.value = ''
    nodeNote.value = ''
    nodeTags.value = []
    nodeColor.value = '#409EFF'
  })

  // 数据变化事件
  mindMapInstance.value.on('data_change', () => {
    // 自动保存或发送到WebSocket
    autoSaveOrSync()
  })
}

// 工具栏方法
const addNode = () => {
  if (!mindMapInstance.value || !selectedNode.value) {
    ElMessage.warning('请先选择一个节点')
    return
  }
  
  const newNodeData = {
    text: '新节点',
    expand: true,
    uid: Date.now().toString()
  }
  
  selectedNode.value.addChild(newNodeData)
  mindMapInstance.value.render()
}

const deleteNode = () => {
  if (!selectedNode.value) {
    ElMessage.warning('请先选择一个节点')
    return
  }
  
  if (selectedNode.value.isRoot) {
    ElMessage.warning('无法删除根节点')
    return
  }
  
  ElMessageBox.confirm('确定要删除这个节点吗？', '删除确认', {
    type: 'warning'
  }).then(() => {
    selectedNode.value.remove()
    mindMapInstance.value.render()
    selectedNode.value = null
  }).catch(() => {})
}

const zoomIn = () => {
  mindMapInstance.value?.view.enlarge()
}

const zoomOut = () => {
  mindMapInstance.value?.view.narrow()
}

const resetZoom = () => {
  mindMapInstance.value?.view.reset()
}

// 节点属性更新方法
const updateNodeText = () => {
  if (selectedNode.value && nodeText.value.trim()) {
    selectedNode.value.setText(nodeText.value.trim())
    mindMapInstance.value.render()
  }
}

const updateNodeNote = () => {
  if (selectedNode.value) {
    selectedNode.value.setData('note', nodeNote.value)
  }
}

const updateNodeColor = () => {
  if (selectedNode.value && nodeColor.value) {
    selectedNode.value.setStyle('fillColor', nodeColor.value)
    mindMapInstance.value.render()
  }
}

// 标签管理
const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value && !nodeTags.value.includes(inputValue.value)) {
    nodeTags.value.push(inputValue.value)
    if (selectedNode.value) {
      selectedNode.value.setData('tags', nodeTags.value)
    }
  }
  inputVisible.value = false
  inputValue.value = ''
}

const removeTag = (tag: string) => {
  const index = nodeTags.value.indexOf(tag)
  if (index > -1) {
    nodeTags.value.splice(index, 1)
    if (selectedNode.value) {
      selectedNode.value.setData('tags', nodeTags.value)
    }
  }
}

// 保存和导出
const saveMindMap = async () => {
  if (!mindMapInstance.value) {
    ElMessage.error('思维导图未初始化')
    return
  }
  
  saving.value = true
  try {
    // 简化版保存：只创建一个测试节点
    const testNodePayload = {
      node_id: `test_${Date.now()}`,
      text: '通过前端创建的测试节点',
      background_color: '#ff9999',
      font_color: '#000000',
      font_size: 14,
      font_weight: 'normal',
      position_x: Math.random() * 200,
      position_y: Math.random() * 200,
      extra_data: { source: 'frontend_test' }
    }
    
    console.log('正在保存测试节点:', testNodePayload)
    await mindmapStore.createNode(projectId, testNodePayload)
    
    ElMessage.success('测试节点保存成功')
  } catch (error: any) {
    console.error('保存失败:', error)
    if (error.response?.status === 403) {
      ElMessage.error('没有权限保存到此项目')
    } else if (error.response?.status === 500) {
      ElMessage.error('服务器错误，保存失败')
    } else {
      ElMessage.error(`保存失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
    }
  } finally {
    saving.value = false
  }
}

// 转换并保存节点数据
const convertAndSaveNodes = async (data: any) => {
  // 这里应该实现将simple-mind-map的数据转换为我们的节点格式
  // 然后调用相应的API保存
  console.log('保存数据:', data)
  
  // 示例：遍历节点数据并保存/更新
  const traverseAndSave = async (nodeData: any, parentId: number | null = null) => {
    try {
      // 检查节点是否已存在
      const existingNode = mindmapStore.nodes.find(n => n.node_id === nodeData.data.uid)
      
      const nodePayload = {
        node_id: nodeData.data.uid || Date.now().toString(),
        parent: parentId,
        text: nodeData.data.text || '新节点',
        note: nodeData.data.note || '',
        background_color: nodeData.data.backgroundColor || '#ffffff',
        font_color: nodeData.data.color || '#000000',
        font_size: nodeData.data.fontSize || 16,
        font_weight: nodeData.data.fontWeight || 'normal',
        position_x: nodeData.data.left || 0,
        position_y: nodeData.data.top || 0,
        extra_data: nodeData.data
      }
      
      if (existingNode) {
        await mindmapStore.updateNode(projectId, existingNode.id, nodePayload)
      } else {
        await mindmapStore.createNode(projectId, nodePayload)
      }
      
      // 递归处理子节点
      if (nodeData.children && nodeData.children.length > 0) {
        for (const child of nodeData.children) {
          await traverseAndSave(child, existingNode?.id || null)
        }
      }
    } catch (error: any) {
      console.error('保存节点失败:', error)
      if (error.response?.status === 403) {
        ElMessage.error('没有权限创建或更新节点')
      } else {
        console.error('节点保存错误详情:', error.response?.data)
      }
    }
  }
  
  await traverseAndSave(data)
}

const exportMindMap = () => {
  if (!mindMapInstance.value) {
    ElMessage.error('思维导图未初始化')
    return
  }
  
  // 导出为PNG
  mindMapInstance.value.export('png', '思维导图')
}

// 自动保存或同步
const autoSaveOrSync = () => {
  // 这里可以实现自动保存逻辑或WebSocket同步
  console.log('数据变化，准备同步...')
}

// WebSocket连接
const connectWebSocket = () => {
  // 实现WebSocket连接逻辑
  mindmapStore.connectWebSocket(projectId)
  connectionStatus.value = 'connected'
}

const disconnectWebSocket = () => {
  mindmapStore.disconnectWebSocket()
  connectionStatus.value = 'disconnected'
}

// 监听WebSocket状态变化
watch(() => mindmapStore.isConnected, (connected) => {
  connectionStatus.value = connected ? 'connected' : 'disconnected'
})

// 监听在线用户变化
watch(() => mindmapStore.onlineUsers, (users) => {
  onlineUsers.value = users
})

// 监听选中节点变化，调整思维导图大小
watch(selectedNode, async (newNode, oldNode) => {
  if (!mindMapInstance.value) return
  
  // 当属性面板显示/隐藏状态改变时，延迟调整思维导图大小
  await nextTick()
  setTimeout(() => {
    if (mindMapInstance.value) {
      // 触发思维导图重新计算容器大小
      mindMapInstance.value.resize()
    }
  }, 300) // 等待CSS过渡动画完成
})
</script>

<style scoped>
.mindmap-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 防止滚动条 */
  position: fixed; /* 固定定位确保全屏 */
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

/* 确保 AppLayout 内部的内容有正确的高度 */
.mindmap-view :deep(.app-main) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  height: calc(100vh - 60px); /* 减去头部高度 */
}

.mindmap-view :deep(.main-content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: none;
  margin: 0;
  padding: 0; /* 思维导图页面去掉内边距 */
  width: 100vw; /* 强制全屏宽度 */
  height: 100%; /* 确保高度充满 */
}

.mindmap-view :deep(.content-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%; /* 确保内容区域充满 */
}

.page-header {
  flex-shrink: 0; /* 防止头部被压缩 */
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px; /* 固定头部高度 */
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.project-info {
  font-size: 14px;
  color: #666;
  margin-left: 10px;
}

.toolbar {
  flex-shrink: 0; /* 防止工具栏被压缩 */
  padding: 10px 20px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  height: 60px; /* 固定工具栏高度 */
}

.online-users {
  font-size: 12px;
  color: #666;
}

.mindmap-container {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
  height: calc(100vh - 180px); /* 减去头部、页面标题和工具栏高度 */
  min-height: 600px; /* 确保最小高度 */
}

.mindmap-canvas {
  flex: 1;
  background: #fafafa;
  position: relative;
  height: 100%; /* 确保画布充满容器高度 */
  min-width: 0; /* 允许 flex 子元素收缩 */
  overflow: hidden; /* 防止内容溢出 */
}

.property-panel {
  width: 300px;
  flex-shrink: 0; /* 防止属性面板被压缩 */
  background: white;
  border-left: 1px solid #e0e0e0;
  overflow-y: auto;
  padding: 20px;
  transition: width 0.3s ease; /* 添加过渡动画 */
}

.property-panel h4 {
  margin: 0 0 20px 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
}

.property-item {
  margin-bottom: 20px;
}

.property-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #666;
  font-size: 14px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-item {
  margin: 0;
}

.tag-input {
  width: 80px;
}

.button-new-tag {
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
  border-style: dashed;
}

.connection-status {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

/* simple-mind-map 样式覆盖 */
:deep(.smm-node) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

:deep(.smm-node-text) {
  word-break: break-word;
}

/* 强制设置思维导图容器样式 */
#mindMapContainer {
  width: 100% !important;
  height: 100% !important;
  min-height: 600px !important;
  min-width: 0 !important; /* 允许收缩适应属性面板 */
}

/* 确保 simple-mind-map 的 SVG 容器有正确尺寸 */
:deep(.smm-svg-container) {
  width: 100% !important;
  height: 100% !important;
}

/* 当属性面板显示时的布局调整 */
.mindmap-container:has(.property-panel) .mindmap-canvas {
  width: calc(100% - 300px); /* 减去属性面板宽度 */
}

/* 如果浏览器不支持 :has 伪类，使用 JavaScript 类 */
.mindmap-container.has-property-panel .mindmap-canvas {
  width: calc(100% - 300px); /* 减去属性面板宽度 */
}

/* 工具栏响应式 */
@media (max-width: 768px) {
  .property-panel {
    width: 250px;
  }
  
  .toolbar {
    flex-wrap: wrap;
    gap: 5px;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
}
</style>
