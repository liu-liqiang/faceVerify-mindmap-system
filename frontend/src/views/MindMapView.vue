<template>
  <div class="mindmap-view">
    <AppLayout>
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <h1>{{ projectInfo?.name || '思维导图编辑器' }}</h1>
          </div>
          <div class="header-actions">
            <el-button @click="$router.back()">
              <el-icon>
                <ArrowLeft />
              </el-icon>
              返回
            </el-button>
          </div>
        </div>
      </template>

      <!-- 思维导图容器 -->
      <div class="mindmap-container">
        <div ref="mindMapContainer" id="mindMapContainer" class="mindmap-canvas"></div>
      </div>
    </AppLayout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import { useMindMapStore } from '@/stores/mindmap'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { mindmapAPI, userAPI } from '@/api/index'

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
const mindMapInstance = ref<any>() // 使用 ref 包装 MindMap 实例
const projectInfo = ref<any>()

// 用户信息缓存
const userInfoCache = ref<Map<string, any>>(new Map())

// 获取项目ID
const projectId = parseInt(route.params.id as string)

// 当前激活的节点列表
const activeNodes = shallowRef([])

// 初始化
onMounted(async () => {
  await initProject()
  await initMindMap()
})

onUnmounted(() => {
  // 在组件卸载前保存数据
  saveToLocalStorage()

  if (mindMapInstance.value) {
    mindMapInstance.value.destroy()
  }

  // 清理提示框元素
  const tooltip = document.getElementById('node-tooltip')
  if (tooltip) {
    tooltip.remove()
  }

})

// 初始化项目信息
const initProject = async () => {
  try {
    projectInfo.value = await projectStore.fetchProject(projectId)
    console.log('项目信息:', projectInfo.value)
  } catch (error) {
    console.error('获取项目信息失败:', error)
    ElMessage.error('获取项目信息失败')
    router.push('/projects')
  }
}

// 初始化思维导图
const initMindMap = async () => {
  // 等待DOM渲染完成
  await nextTick()

  // 检查容器元素是否存在
  if (!mindMapContainer.value) {
    console.error('思维导图容器元素未找到')
    ElMessage.error('思维导图容器初始化失败')
    return
  }

  console.log('容器元素已找到:', mindMapContainer.value)

  try {
    let mindmapData

    console.log('从服务器获取思维导图数据')
    mindmapData = await mindmapStore.fetchSimpleMindMapData(projectId)

    console.log('获取的思维导图数据:', mindmapData)

    // 验证和清理数据
    const cleanData = (data: any): any => {
      if (!data || typeof data !== 'object') {
        return {
          data: {
            text: '中心主题',
            expand: true,
            uid: 'root'
          },
          children: []
        }
      }

      // 确保 data 属性存在且有效
      if (!data.data || typeof data.data !== 'object') {
        data.data = {
          text: '中心主题',
          expand: true,
          uid: 'root'
        }
      }

      // 确保基本属性存在
      if (!data.data.text) data.data.text = '中心主题'
      if (!data.data.uid) data.data.uid = 'root'
      if (data.data.expand === undefined) data.data.expand = true

      // 确保 children 是数组
      if (!Array.isArray(data.children)) {
        data.children = []
      }

      // 递归清理子节点
      data.children = data.children.map((child: any) => cleanData(child))

      return data
    }

    const cleanedData = cleanData(mindmapData)
    console.log('清理后的思维导图数据:', cleanedData)

    // 创建思维导图实例
    mindMapInstance.value = new MindMap({
      el: mindMapContainer.value,
      data: cleanedData,
      theme: 'default',
      layout: 'logicalStructure',
      enableFreeDrag: false,
      readonly: false,
      customNoteContentShow: {
        show: true
      },
      associativeLine: {
        isAlwaysShowLine: false
      },
      beforeTextEdit: (node: any) => {
        if (node.getData()._isSystemDefault || node.getData().is_system_default) {
          ElMessage.warning('系统默认节点不能编辑')
          return false // 阻止编辑
        }
        else if (node.getData()._creator || node.getData().creator) {
          // 如果是当前用户创建的节点，允许编辑
          if (node.getData()._creator === authStore.user?.police_number) {
            return true // 允许编辑
          }
          // 否则，阻止编辑
          ElMessage.warning('您只能编辑自己创建的节点')
          return false
        }
        return true // 允许编辑
      },
      beforeShortcutRun: (key: string, activeNodeList: any[]) => {
        // 处理快捷键事件
        for (const node of activeNodeList) {
          if (key === "Del" || key === "Backspace") {
            if (activeNodeList.length > 1) {
              ElMessage.warning('请先删除子节点')
              return true; // 阻止删除
            }
            else if (node.nodeData.children && node.nodeData.children.length > 0) {
              ElMessage.warning('请先删除子节点')
              return true; // 阻止删除
            }
            else if (node.nodeData.data && node.nodeData.data._isSystemDefault || node.nodeData.is_system_default) {
              ElMessage.warning('系统默认节点不能删除')
              return true; // 阻止删除
            }
            else if (node.nodeData.data._creator || node.nodeData.data.creator) {
              // 如果是当前用户创建的节点，允许删除
              if (node.nodeData.data._creator === authStore.user?.police_number) {
                return false // 允许删除
              }
              // 否则，阻止删除
              ElMessage.warning('您只能删除自己创建的节点')
              return true
            }
          }
          else if (key === "Control+x") {
            if (activeNodeList.length > 1) {
              ElMessage.warning('不能剪切多个节点')
              return true; // 阻止删除
            }
            else if (node.nodeData.children && node.nodeData.children.length > 0) {
              ElMessage.warning('请先剪切子节点')
              return true; // 阻止剪切
            }
            else if (node.nodeData.data._isSystemDefault || node.nodeData.data.is_system_default) {
              ElMessage.warning('系统默认节点不能剪切')
              return true; // 阻止剪切
            }
            else if (node.nodeData.data._creator || node.nodeData.data.creator) {
              // 如果是当前用户创建的节点，允许剪切
              if (node.nodeData.data._creator === authStore.user?.police_number) {
                return false // 允许剪切
              }
              // 否则，阻止剪切
              ElMessage.warning('您只能剪切自己创建的节点')
              return true
            }
          }
          else if (key === "Control+c" || key === "Cmd+c" || key === "Meta+c") {
            // 允许复制操作
            return false; // 允许复制
          }
          else if (key === "Control+v" || key === "Cmd+v" || key === "Meta+v") {
            // 允许粘贴操作
            ElMessage.warning('粘贴节点功能在开发中')
            return true; // 允许粘贴
          }
          else if (key === "Control+a" || key === "Cmd+a" || key === "Meta+a") {
            // 允许全选操作
            return false; // 允许全选
          }
          else if (key === "Control+z" || key === "Cmd+z" || key === "Meta+z") {
            // 允许撤销操作
            return false; // 允许撤销
          }
          else if (key === "Control+y" || key === "Cmd+y" || key === "Meta+y") {
            // 允许重做操作
            return false; // 允许重做
          }
        }

        // console.log('快捷键触发:', key, activeNodeList)
        // console.log(typeof (key))
        // if (key === "Del" || key === "Backspace") {
        //   console.log('删除节点:', activeNodeList)
        //   return true;
        // }
        // if (key === "Control+x") {

        // }

      }
    } as any)

    console.log('思维导图实例创建成功:', mindMapInstance.value)

    // 强制设置容器尺寸并重新渲染
    setTimeout(() => {
      if (mindMapInstance.value && mindMapContainer.value) {
        // 获取容器的实际尺寸
        const containerRect = mindMapContainer.value.getBoundingClientRect()
        console.log('容器尺寸:', containerRect)

        // 强制设置 SVG 容器尺寸
        const svgContainer = mindMapContainer.value.querySelector('.smm-svg-container') as HTMLElement
        const svg = mindMapContainer.value.querySelector('svg') as SVGElement

        if (svgContainer) {
          svgContainer.style.width = '100%'
          svgContainer.style.height = '100%'
          svgContainer.style.position = 'absolute'
          svgContainer.style.top = '0'
          svgContainer.style.left = '0'
          svgContainer.style.right = '0'
          svgContainer.style.bottom = '0'
        }

        if (svg) {
          svg.style.width = '100%'
          svg.style.height = '100%'
          svg.style.position = 'absolute'
          svg.style.top = '0'
          svg.style.left = '0'
          svg.setAttribute('width', '100%')
          svg.setAttribute('height', '100%')
        }

        // 重新渲染思维导图以确保正确显示
        mindMapInstance.value.resize()
        mindMapInstance.value.render()

        console.log('思维导图容器尺寸已强制同步')
      }
    }, 100)

    saveToLocalStorage()



    // 绑定鼠标悬浮事件
    bindHoverEvents()


    ElMessage.success('思维导图加载成功')



    mindMapInstance.value.on('data_change_detail', async (arr: any) => {
      // 处理节点数据变化事件
      console.log('节点数据变化:', arr);

      if (arr.length === 0) {
        console.log('没有节点数据变化')
        return
      }

      // 自动保存到本地存储
      setTimeout(() => {
        saveToLocalStorage()
      }, 500)

      // 批量处理变更，避免频繁请求
      const pendingChanges: any[] = []

      for (const item of arr) {
        try {
          // 检查是否为创建操作
          if (item.action === 'create') {
            console.log('创建节点:', item.data);
            await handleNodeCreate(arr)
          }
          // 检查是否为更新操作
          else if (item.action === 'update' && arr.length < 2) {
            console.log('更新节点:', item.data);
            await handleNodeUpdate(item)
          }
          // 检查是否为删除操作
          else if (item.action === 'delete') {
            console.log('删除节点:', item.data);

            await handleNodeDelete(item)
          }
          // 检查是否为移动操作
          else if (item.action === 'move') {
            console.log('移动节点:', item.data);
            await handleNodeMove(item)
          }
          else {
            console.log('其他变更类型:', item.action, item);
            pendingChanges.push(item)
          }

        } catch (error: any) {
          console.error(`处理节点变更失败 (${item.action}):`, error);
          ElMessage.error(`节点操作同步失败: ${error.message}`);
        }
      }

      // // 批量处理其他类型的变更
      // if (pendingChanges.length > 0) {
      //   try {
      //     await uploadBatchChanges(pendingChanges)
      //   } catch (error: any) {
      //     console.error('批量处理变更失败:', error);
      //   }
      // }
    })

  } catch (error: any) {
    console.error('思维导图初始化失败:', error)
    ElMessage.error(`思维导图初始化失败: ${error?.message || '未知错误'}`)
  }
}

// 根据警号获取用户信息
const getUserInfoByPoliceNumber = async (policeNumber: string) => {
  if (!policeNumber) return null

  // 检查缓存
  if (userInfoCache.value.has(policeNumber)) {
    return userInfoCache.value.get(policeNumber)
  }

  try {
    // 使用新的 API 方法
    const response = await userAPI.getUserByPoliceNumber(policeNumber)
    const userInfo = response.data

    // 缓存用户信息
    userInfoCache.value.set(policeNumber, userInfo)
    return userInfo

  } catch (error: any) {
    console.error('获取用户信息失败:', error)

    // 如果是 404 错误，API 可能返回了默认信息
    if (error.response?.status === 404 && error.response?.data) {
      const userInfo = error.response.data
      if (userInfo.real_name && userInfo.unit) {
        userInfoCache.value.set(policeNumber, userInfo)
        return userInfo
      }
    }
  }

  // 如果获取失败，返回默认信息
  const defaultInfo = {
    real_name: policeNumber, // 使用警号作为默认姓名
    unit: '未知单位'
  }
  userInfoCache.value.set(policeNumber, defaultInfo)
  return defaultInfo
}

// 绑定鼠标悬浮事件
const bindHoverEvents = () => {
  if (!mindMapInstance.value) return

  // 监听节点鼠标进入事件
  mindMapInstance.value.on('node_mouseenter', async (node: any, e: MouseEvent) => {
    await showNodeTooltip(node, e)
  })

  // 监听节点鼠标离开事件
  mindMapInstance.value.on('node_mouseleave', () => {
    hideNodeTooltip()
  })
}

// 显示节点悬浮提示
const showNodeTooltip = async (node: any, e: MouseEvent) => {
  const nodeData = node.getData()

  // 获取节点信息
  const policeNumber = nodeData._creator || nodeData.creator
  const updatedAt = nodeData._updatedAt || nodeData.updated_at
  const isSystemDefault = nodeData._isSystemDefault || nodeData.is_system_default

  // 格式化时间
  const formatTime = (timeStr: string) => {
    if (!timeStr) return '未知时间'
    try {
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return '未知时间'
    }
  }

  // 获取用户信息
  let userName = '未知用户'
  let userUnit = '未知单位'

  if (isSystemDefault) {
    userName = '系统默认创建'
    userUnit = '系统'
  } else if (policeNumber) {
    const userInfo = await getUserInfoByPoliceNumber(policeNumber)
    if (userInfo) {
      userName = userInfo.real_name || userInfo.name || policeNumber
      userUnit = userInfo.unit || userInfo.department || '未知单位'
    }
  }

  // 创建提示框内容
  let tooltipContent = `<div class="node-tooltip">
    <div class="tooltip-item">
      <span class="tooltip-label">创建者:</span>
      <span class="tooltip-value">${userName}</span>
    </div>
    <div class="tooltip-item">
      <span class="tooltip-label">单位:</span>
      <span class="tooltip-value">${userUnit}</span>
    </div>`

  if (updatedAt) {
    tooltipContent += `
    <div class="tooltip-item">
      <span class="tooltip-label">更新时间:</span>
      <span class="tooltip-value">${formatTime(updatedAt)}</span>
    </div>`
  }

  tooltipContent += '</div>'

  // 创建或更新提示框元素
  let tooltip = document.getElementById('node-tooltip')
  if (!tooltip) {
    tooltip = document.createElement('div')
    tooltip.id = 'node-tooltip'
    document.body.appendChild(tooltip)
  }

  tooltip.innerHTML = tooltipContent
  tooltip.style.display = 'block'

  // 定位提示框 - 让提示框更靠近鼠标
  const x = e.clientX + 5  // 向右偏移5px
  const y = e.clientY - 5  // 向上偏移5px

  tooltip.style.left = x + 'px'
  tooltip.style.top = y + 'px'

  // 检查边界，防止提示框超出屏幕
  const tooltipRect = tooltip.getBoundingClientRect()
  const screenWidth = window.innerWidth
  const screenHeight = window.innerHeight

  // 如果超出右边界，向左显示
  if (tooltipRect.right > screenWidth) {
    tooltip.style.left = (e.clientX - tooltipRect.width - 5) + 'px'
  }

  // 如果超出下边界，向上显示
  if (tooltipRect.bottom > screenHeight) {
    tooltip.style.top = (e.clientY - tooltipRect.height - 5) + 'px'
  }
}

// 隐藏节点悬浮提示
const hideNodeTooltip = () => {
  const tooltip = document.getElementById('node-tooltip')
  if (tooltip) {
    tooltip.style.display = 'none'
  }
}

// 全局键盘监听器变量
let globalKeyboardListener: ((e: KeyboardEvent) => void) | null = null

// 检查是否为系统默认节点
const isSystemDefaultNode = (node: any): boolean => {
  if (!node) return false
  return node.getData("_isSystemDefault") === true || node.getData("is_system_default") === true
}

// LocalStorage 相关功能
const getLocalStorageKey = () => {
  return `mindmap_project_${projectId}`
}

// 保存思维导图数据到 localStorage
const saveToLocalStorage = () => {
  if (!mindMapInstance.value) return

  try {
    const data = mindMapInstance.value.getData()
    const localStorageKey = getLocalStorageKey()

    const saveData = {
      data: data,
      lastSaved: new Date().toISOString(),
      projectId: projectId,
      projectName: projectInfo.value?.name || '未命名项目'
    }

    localStorage.setItem(localStorageKey, JSON.stringify(saveData))
    console.log('思维导图数据已保存到本地存储:', saveData)
  } catch (error) {
    console.error('保存到本地存储失败:', error)
  }
}

// 从 localStorage 加载思维导图数据
const loadFromLocalStorage = () => {
  try {
    const localStorageKey = getLocalStorageKey()
    const savedData = localStorage.getItem(localStorageKey)

    if (!savedData) {
      console.log('本地没有找到保存的数据')
      return null
    }

    const parsedData = JSON.parse(savedData)
    console.log('从本地加载的数据:', parsedData)

    return parsedData.data
  } catch (error) {
    console.error('从本地存储加载失败:', error)
    return null
  }
}

// 检查是否有本地保存的数据
const hasLocalData = () => {
  const localStorageKey = getLocalStorageKey()
  return localStorage.getItem(localStorageKey) !== null
}

// 清除本地保存的数据
const clearLocalData = () => {
  try {
    const localStorageKey = getLocalStorageKey()
    localStorage.removeItem(localStorageKey)
    console.log('本地数据已清除')
  } catch (error) {
    console.error('清除本地数据失败:', error)
  }
}

// 上传节点到服务器
const uploadNodeToServer = async (nodeData: any) => {
  try {
    console.log('准备上传节点到服务器:', nodeData)

    // 使用新的 API 方法
    const response = await mindmapAPI.createNodeWithProjectId({
      projectId: nodeData.projectId,
      data: nodeData.data,
      parent_uid: nodeData.parent_uid,
      image: nodeData.image,
      attachment: nodeData.attachment
    })

    const result = response.data
    console.log('节点上传成功:', result)

    // 可以在这里更新本地节点数据，比如添加服务器返回的 ID
    if (result.node_id) {
      updateLocalNodeWithServerId(nodeData.data.uid, result.node_id)
    }

    return result

  } catch (error: any) {
    // 处理网络错误或API错误
    if (error.response?.status === 404) {
      // API 端点不存在，先记录日志但不阻塞用户操作
      console.warn('API 端点不存在，节点创建将仅保存到本地存储')
      ElMessage.info('节点已保存到本地，服务器同步功能尚未配置')
      return { success: false, reason: 'api_not_found' }
    }

    if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
      console.warn('网络连接失败，节点创建将仅保存到本地存储')
      ElMessage.warning('网络连接失败，数据已保存到本地')
      return { success: false, reason: 'network_error' }
    }

    console.error('上传节点到服务器失败:', error)

    // 如果有响应数据，提取错误信息
    let errorMessage = error.message
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    }

    throw new Error(errorMessage)
  }
}

// 更新本地节点的服务器 ID
const updateLocalNodeWithServerId = (localUid: string, serverId: string) => {
  try {
    if (!mindMapInstance.value) return

    // 查找并更新节点数据
    const updateNodeData = (nodeData: any): boolean => {
      if (nodeData.data && nodeData.data.uid === localUid) {
        nodeData.data._serverId = serverId
        nodeData.data._synced = true
        console.log(`节点 ${localUid} 已关联服务器 ID: ${serverId}`)
        return true
      }

      if (nodeData.children && Array.isArray(nodeData.children)) {
        for (const child of nodeData.children) {
          if (updateNodeData(child)) return true
        }
      }

      return false
    }

    const currentData = mindMapInstance.value.getData()
    if (updateNodeData(currentData)) {
      // 静默更新，不触发 data_change_detail 事件
      mindMapInstance.value.setData(currentData, true)
    }

  } catch (error) {
    console.error('更新本地节点服务器 ID 失败:', error)
  }
}

// 批量上传节点变更
const uploadBatchChanges = async (changes: any[]) => {
  try {
    const batchData = {
      projectId: projectId,
      changes: changes.map(change => ({
        action: change.action,
        node_uid: change.data?.data?.uid,
        node_data: change.data?.data,
      }))
    }

    const response = await mindmapAPI.batchUpdate(batchData)
    console.log('批量更新成功:', response.data)
    return response.data

  } catch (error: any) {
    console.error('批量上传失败:', error)
    let errorMessage = error.message
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    }
    ElMessage.error(`批量同步失败: ${errorMessage}`)
    throw error
  }
}

// 处理不同类型的节点变更
const handleNodeChange = async (changeItem: any) => {
  try {
    switch (changeItem.action) {
      case 'create':
        await handleNodeCreate(changeItem)
        break
      case 'update':
        await handleNodeUpdate(changeItem)
        break
      case 'delete':
        await handleNodeDelete(changeItem)
        break
      case 'move':
        await handleNodeMove(changeItem)
        break
      default:
        console.log('未知的节点变更类型:', changeItem.action)
    }
  } catch (error: any) {
    console.error(`处理节点变更失败 (${changeItem.action}):`, error)
    ElMessage.error(`节点${changeItem.action}同步失败: ${error.message}`)
  }
}

// 处理节点创建
const handleNodeCreate = async (arr: any[]) => {
  try {
    const parent_uid = arr[0].data.data.uid
    const nodeData = {
      projectId: projectId,
      data: {
        ...arr[1].data.data,
      },
      parent_uid: parent_uid,
      image: null,
      attachment: null
    }

    const result = await uploadNodeToServer(nodeData)

    if (result && result.success === false) {
      // API 不可用，只保存到本地
      console.log('节点已保存到本地存储，等待服务器可用时同步')
      return
    }

    // 上传成功
    console.log('节点创建并上传成功')

  } catch (error: any) {
    console.error('节点创建失败:', error)
    ElMessage.error(`节点创建失败: ${error.message}`)
  }
}

// 处理节点更新
const handleNodeUpdate = async (changeItem: any) => {
  try {
    const nodeData = {
      node_uid: changeItem.data.data.uid,
      data: {
        ...changeItem.data.data,
        _updatedAt: new Date().toISOString(),
        _updatedBy: authStore.user?.police_number
      },
      projectId: projectId
    }

    const response = await mindmapAPI.updateNodeByUid(nodeData)
    console.log('节点更新成功:', response.data)
  } catch (error: any) {
    console.error('节点更新失败:', error)
    let errorMessage = error.message
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    }
    throw new Error(errorMessage)
  }
}

// 处理节点删除
const handleNodeDelete = async (changeItem: any) => {
  try {
    const nodeUid = changeItem.data.data.uid
    const response = await mindmapAPI.deleteNodeByUid(nodeUid, projectId)
    console.log('节点删除成功:', nodeUid)
  } catch (error: any) {
    console.error('节点删除失败:', error)
    let errorMessage = error.message
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    }
    throw new Error(errorMessage)
  }
}

// 处理节点移动
const handleNodeMove = async (changeItem: any) => {
  try {
    const moveData = {
      node_uid: changeItem.data.data.uid,
      new_parent_uid: changeItem.newParent?.data?.uid || 'root',
      old_parent_uid: changeItem.oldParent?.data?.uid || 'root',
      projectId: projectId,
      moved_by: authStore.user?.police_number
    }

    const response = await mindmapAPI.moveNode(moveData)
    console.log('节点移动成功:', response.data)
  } catch (error: any) {
    console.error('节点移动失败:', error)
    let errorMessage = error.message
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    }
    throw new Error(errorMessage)
  }
}
</script>

<style scoped>
.mindmap-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.header-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.mindmap-container {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
  height: calc(100vh - 120px);
  min-height: 600px;
  width: 100%;
}

.mindmap-canvas {
  flex: 1;
  background: #fafafa;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* 强制设置思维导图容器样式 */
#mindMapContainer {
  width: 100% !important;
  height: 100% !important;
  min-height: 600px !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
}

/* 确保 simple-mind-map 的 SVG 容器有正确尺寸 */
:deep(.smm-svg-container) {
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
}

/* 确保 SVG 元素本身也完全填满容器 */
:deep(.smm-svg-container svg) {
  width: 100% !important;
  height: 100% !important;
  display: block !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
}

/* 确保 SVG 内部的画布区域也正确设置 */
:deep(.smm-canvas) {
  width: 100% !important;
  height: 100% !important;
}

/* 强制覆盖任何可能的内联样式 */
:deep(.smm-svg-container) {
  box-sizing: border-box !important;
}

:deep(.smm-svg-container svg) {
  box-sizing: border-box !important;
  max-width: none !important;
  max-height: none !important;
  min-width: 100% !important;
  min-height: 100% !important;
}

:deep(.smm-node) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
}

:deep(.smm-node-text) {
  word-break: break-word;
}

/* 节点悬浮提示框样式 */
:global(#node-tooltip) {
  position: fixed;
  background: rgba(50, 50, 50, 0.95);
  color: white;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  pointer-events: none;
  display: none;
  max-width: 280px;
  word-wrap: break-word;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(5px);
}

:global(.node-tooltip) {
  min-width: 160px;
}

:global(.tooltip-item) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  gap: 12px;
}

:global(.tooltip-item:last-child) {
  margin-bottom: 0;
}

:global(.tooltip-label) {
  font-weight: 600;
  color: #bbb;
  white-space: nowrap;
  min-width: 60px;
}

:global(.tooltip-value) {
  color: #fff;
  text-align: right;
  flex: 1;
  font-weight: 500;
}
</style>
