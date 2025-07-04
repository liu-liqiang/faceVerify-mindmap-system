<template>
  <div class="project-detail">
    <AppLayout>
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button text @click="$router.back()" class="back-btn">
              <el-icon>
                <ArrowLeft />
              </el-icon>
              返回
            </el-button>
            <h1>{{ project?.name || '项目详情' }}</h1>
          </div>
          <div class="header-actions">
            <el-button type="success" @click="$router.push(`/projects/${$route.params.id}/mindmap`)">
              <el-icon>
                <Share />
              </el-icon>
              思维导图
            </el-button>
            <el-button v-if="isProjectCreator" @click="showMembersDialog = true">
              <el-icon>
                <User />
              </el-icon>
              成员管理
            </el-button>
            <el-button v-if="isProjectCreator" @click="showEditDialog = true">
              <el-icon>
                <Edit />
              </el-icon>
              编辑项目
            </el-button>
          </div>
        </div>
      </template>

      <div class="content">
        <div v-if="loading" class="loading-container">
          <el-skeleton :rows="8" animated />
        </div>

        <div v-else-if="project" class="project-content">
          <!-- 基本信息 -->
          <el-card class="info-card" shadow="never">
            <template #header>
              <div class="card-header">
                <el-icon>
                  <InfoFilled />
                </el-icon>
                <span>基本信息</span>
              </div>
            </template>

            <div class="info-grid">
              <div class="info-item">
                <label>案件名称：</label>
                <span>{{ project.name }}</span>
              </div>
              <div class="info-item">
                <label>案件编号：</label>
                <span>{{ project.case_number }}</span>
              </div>
              <div class="info-item">
                <label>立案单位：</label>
                <span>{{ project.filing_unit_display }}</span>
              </div>
              <div class="info-item">
                <label>创建者：</label>
                <span>{{ project.creator?.real_name || project.creator?.username }}</span>
              </div>
              <div class="info-item">
                <label>创建时间：</label>
                <span>{{ formatDateTime(project.created_at) }}</span>
              </div>
              <div class="info-item">
                <label>更新时间：</label>
                <span>{{ formatDateTime(project.updated_at) }}</span>
              </div>
            </div>

            <div class="case-summary" v-if="project.case_summary">
              <label>案情简述：</label>
              <p>{{ project.case_summary }}</p>
            </div>
          </el-card>

          <!-- 统计信息 -->
          <el-row :gutter="20" class="stats-row">
            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-item">
                  <el-icon class="stat-icon member-icon">
                    <User />
                  </el-icon>
                  <div class="stat-content">
                    <div class="stat-value">{{ project.member_count || 0 }}</div>
                    <div class="stat-label">参与协作人员</div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-item">
                  <el-icon class="stat-icon node-icon">
                    <Connection />
                  </el-icon>
                  <div class="stat-content">
                    <div class="stat-value">{{ project.node_count || 0 }}</div>
                    <div class="stat-label">节点总数</div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-item">
                  <el-icon class="stat-icon my-node-icon">
                    <Edit />
                  </el-icon>
                  <div class="stat-content">
                    <div class="stat-value">{{ myNodeCount || 0 }}</div>
                    <div class="stat-label">我贡献的节点数</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="20" class="stats-row">
            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-item">
                  <el-icon class="stat-icon mindmap-attachment-icon">
                    <Document />
                  </el-icon>
                  <div class="stat-content">
                    <div class="stat-value">{{ mindmapAttachmentCount || 0 }}</div>
                    <div class="stat-label">思维导图附件数</div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-item">
                  <el-icon class="stat-icon my-attachment-icon">
                    <UploadFilled />
                  </el-icon>
                  <div class="stat-content">
                    <div class="stat-value">{{ myMindmapAttachmentCount || 0 }}</div>
                    <div class="stat-label">我上传至思维导图的附件数</div>
                  </div>
                </div>
              </el-card>
            </el-col>
            <el-col :span="8">
              <el-card class="stat-card">
                <div class="stat-item">
                  <el-icon class="stat-icon case-attachment-icon">
                    <Paperclip />
                  </el-icon>
                  <div class="stat-content">
                    <div class="stat-value">{{ attachments.length }}</div>
                    <div class="stat-label">案件附件数</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 附件列表 -->
          <el-card class="attachments-card" shadow="never">
            <template #header>
              <div class="card-header with-actions">
                <div>
                  <el-icon>
                    <Paperclip />
                  </el-icon>
                  <span>案件附件</span>
                </div>
                <el-button v-if="isProjectCreator" type="primary" size="small" @click="showUploadDialog = true">
                  <el-icon>
                    <Plus />
                  </el-icon>
                  上传附件
                </el-button>
              </div>
            </template>

            <div v-if="attachmentsLoading" class="loading-container">
              <el-skeleton :rows="3" animated />
            </div>

            <div v-else-if="attachments.length === 0" class="empty-state">
              <el-empty description="暂无附件">
                <el-button v-if="isProjectCreator" type="primary" @click="showUploadDialog = true">上传第一个附件</el-button>
              </el-empty>
            </div>

            <div v-else class="attachments-list">
              <div v-for="attachment in attachments" :key="attachment.id" class="attachment-item">
                <div class="attachment-info">
                  <el-icon class="file-icon"
                    :class="`file-icon-${getFileIcon(attachment.file_type, attachment.original_name)}`">
                    <component :is="getFileIcon(attachment.file_type, attachment.original_name)" />
                  </el-icon>
                  <div class="attachment-details">
                    <div class="attachment-name">{{ attachment.original_name || '未知文件' }}</div>
                    <div class="attachment-meta">
                      <span>{{ formatFileSize(attachment.file_size) }}</span>
                      <span>·</span>
                      <span>{{ formatDateTime(attachment.created_at) }}</span>
                      <span>·</span>
                      <span>{{ attachment.uploader?.real_name || attachment.uploader?.username || '未知用户' }}</span>
                    </div>
                    <div v-if="attachment.description" class="attachment-description">
                      {{ attachment.description }}
                    </div>
                  </div>
                </div>
                <div class="attachment-actions">
                  <el-button type="primary" size="small" :loading="downloadingAttachments.has(attachment.id)"
                    @click="downloadAttachment(attachment)">
                    <el-icon v-if="!downloadingAttachments.has(attachment.id)">
                      <Download />
                    </el-icon>
                    {{ downloadingAttachments.has(attachment.id) ? '下载中...' : '下载' }}
                  </el-button>
                  <el-button v-if="isProjectCreator" type="danger" size="small" plain
                    :loading="deletingAttachments.has(attachment.id)" @click="deleteAttachment(attachment)">
                    <el-icon v-if="!deletingAttachments.has(attachment.id)">
                      <Delete />
                    </el-icon>
                    {{ deletingAttachments.has(attachment.id) ? '删除中...' : '删除' }}
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 成员列表 -->
          <el-card class="members-card" shadow="never">
            <template #header>
              <div class="card-header with-actions">
                <div>
                  <el-icon>
                    <User />
                  </el-icon>
                  <span>思维导图成员</span>
                </div>
                <el-button v-if="isProjectCreator" type="primary" size="small" @click="showMembersDialog = true">
                  <el-icon>
                    <Plus />
                  </el-icon>
                  邀请成员
                </el-button>
              </div>
            </template>

            <div v-if="membersLoading" class="loading-container">
              <el-skeleton :rows="3" animated />
            </div>

            <div v-else class="members-list">
              <div v-for="member in members" :key="member.user.id" class="member-item">
                <div class="member-info">
                  <div class="member-avatar">
                    {{ (member.user.real_name || member.user.username).charAt(0).toUpperCase() }}
                  </div>
                  <div class="member-details">
                    <div class="member-name">{{ member.user.real_name || member.user.username }}</div>
                    <div class="member-meta">
                      <span>{{ getUnitDisplay(member.user.department || '') }}</span>
                      <span>·</span>
                      <span>{{ formatDateTime(member.joined_at) }} 加入</span>
                    </div>
                  </div>
                </div>
                <div class="member-permission">
                  <el-tag :type="getPermissionTagType(member.permission)">
                    {{ getPermissionText(member.permission) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <el-empty v-else description="项目不存在或已被删除">
          <el-button @click="$router.push('/projects')">返回项目列表</el-button>
        </el-empty>
      </div>
    </AppLayout>

    <!-- 编辑项目对话框 -->
    <EditProjectDialog v-model="showEditDialog" :project="project" @updated="handleProjectUpdated" />

    <!-- 成员管理对话框 -->
    <ProjectMembersDialog v-model="showMembersDialog" :project-id="project?.id || null" />

    <!-- 上传附件对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传附件" width="500px">
      <el-form :model="uploadForm" label-width="80px">
        <el-form-item label="选择文件">
          <el-upload ref="uploadRef" :auto-upload="false" :show-file-list="true" :limit="10"
            :on-change="handleFileChange" :on-remove="handleFileRemove"
            :on-exceed="() => ElMessage.warning('最多只能上传10个文件')" :on-error="(err: any) => console.error('上传错误:', err)"
            :file-list="[]" multiple drag>
            <el-icon class="el-icon--upload">
              <UploadFilled />
            </el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持多文件上传，单个文件不超过300MB。<br />
                支持上传任何类型的文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="请输入附件描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCancel">取消</el-button>
          <el-button type="primary" :loading="uploadLoading" @click="handleUpload">
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore, type Project, type ProjectMember } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Share,
  User,
  Edit,
  ArrowLeft,
  InfoFilled,
  Connection,
  Paperclip,
  Plus,
  Document,
  Download,
  Delete,
  UploadFilled,
  Picture,
  VideoPlay,
  Microphone,
  Folder
} from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import EditProjectDialog from '@/components/EditProjectDialog.vue'
import ProjectMembersDialog from '@/components/ProjectMembersDialog.vue'

interface Attachment {
  id: number
  original_name: string
  file_size: number
  file_size_display: string
  file_type: string
  description?: string
  created_at: string
  uploader?: {
    username: string
    real_name?: string
  }
}

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(true)
const attachmentsLoading = ref(false)
const membersLoading = ref(false)
const uploadLoading = ref(false)
const downloadingAttachments = ref<Set<number>>(new Set())
const deletingAttachments = ref<Set<number>>(new Set())
const showEditDialog = ref(false)
const showMembersDialog = ref(false)
const showUploadDialog = ref(false)

const project = ref<Project | null>(null)
const attachments = ref<Attachment[]>([])
const members = ref<ProjectMember[]>([])
const uploadRef = ref()

const uploadForm = ref({
  description: ''
})

const projectId = computed(() => {
  const id = route.params.id
  return Array.isArray(id) ? parseInt(id[0]) : parseInt(id as string)
})

// 检查是否为项目创建者（只有创建者可以编辑项目基本信息）
const authStore = useAuthStore()
const isProjectCreator = computed(() => {
  if (!project.value || !project.value.creator || !authStore.user) return false
  return project.value.creator.id === authStore.user.id
})

// 检查是否可以管理思维导图（思维导图管理员权限）
const canManageMindmap = computed(() => {
  if (!project.value || !members.value || !authStore.user) return false

  // 项目创建者自动拥有思维导图管理权限
  if (isProjectCreator.value) {
    return true
  }

  // 检查是否为思维导图管理员
  const currentMember = members.value.find(member => member.user.id === authStore.user!.id)
  return currentMember?.permission === 'admin'
})

// 检查是否可以编辑思维导图
const canEditMindmap = computed(() => {
  if (!project.value || !members.value || !authStore.user) return false

  // 项目创建者和思维导图管理员都可以编辑
  if (isProjectCreator.value || canManageMindmap.value) {
    return true
  }

  // 检查是否有编辑权限
  const currentMember = members.value.find(member => member.user.id === authStore.user!.id)
  return currentMember?.permission === 'edit'
})

// 检查是否可以查看思维导图（至少有只读权限）
const canViewMindmap = computed(() => {
  if (!project.value || !members.value || !authStore.user) return false

  // 项目创建者可以查看
  if (isProjectCreator.value) {
    return true
  }

  // 检查是否为项目成员
  const currentMember = members.value.find(member => member.user.id === authStore.user!.id)
  return !!currentMember // 只要是成员就可以查看
})

// 计算我贡献的节点数
const myNodeCount = computed(() => {
  return project.value?.my_node_count || 0
})

// 计算思维导图附件数
const mindmapAttachmentCount = computed(() => {
  return project.value?.mindmap_attachment_count || 0
})

// 计算我上传至思维导图的附件数
const myMindmapAttachmentCount = computed(() => {
  return project.value?.my_mindmap_attachment_count || 0
})

// 获取项目详情
const fetchProject = async () => {
  try {
    loading.value = true
    project.value = await projectStore.fetchProject(projectId.value)
    // 如果项目数据中包含附件，直接使用
    if (project.value?.attachments) {
      attachments.value = project.value.attachments
    }
  } catch (error) {
    ElMessage.error('获取项目详情失败')
    project.value = null
  } finally {
    loading.value = false
  }
}

// 获取附件列表
const fetchAttachments = async () => {
  try {
    attachmentsLoading.value = true
    const response = await projectStore.fetchAttachments(projectId.value)
    attachments.value = response || []
  } catch (error) {
    console.error('获取附件列表失败:', error)
    attachments.value = []
  } finally {
    attachmentsLoading.value = false
  }
}

// 获取成员列表
const fetchMembers = async () => {
  try {
    membersLoading.value = true
    members.value = await projectStore.fetchProjectMembers(projectId.value)
  } catch (error) {
    console.error('获取成员列表失败:', error)
    members.value = []
  } finally {
    membersLoading.value = false
  }
}

const selectedFiles = ref<any[]>([])

// 处理文件选择变化
const handleFileChange = (file: any, fileList: any[]) => {
  console.log('文件选择变化:', file.name, '当前文件列表长度:', fileList.length)

  // 文件大小限制 (300MB)
  const maxSize = 300 * 1024 * 1024 // 300MB
  if (file.size > maxSize) {
    ElMessage.error(`文件大小不能超过300MB，当前文件大小: ${(file.size / (1024 * 1024)).toFixed(2)}MB`)
    return false
  }

  // 更新选中的文件列表
  selectedFiles.value = fileList
  console.log('已选择文件数量:', selectedFiles.value.length)

  // 移除文件类型限制，允许上传任何类型的文件
  return true
}

// 处理文件移除
const handleFileRemove = (file: any, fileList: any[]) => {
  console.log('文件移除:', file.name, '剩余文件数量:', fileList.length)
  // 更新选中的文件列表
  selectedFiles.value = fileList
}  // 调试辅助函数
const logFileInfo = (file: any) => {
  if (!file) {
    console.log('文件对象为空')
    return
  }

  console.log('文件信息:', {
    name: file.name,
    size: file.size,
    type: file.type,
    lastModified: file.lastModified,
    isFile: file instanceof File,
    isBlob: file instanceof Blob,
    constructor: file.constructor?.name,
    properties: Object.keys(file)
  })
}

// 处理文件上传
const handleUpload = async () => {
  const uploadComponent = uploadRef.value
  if (!uploadComponent) {
    ElMessage.warning('上传组件未初始化')
    return
  }

  // 尝试多种方式获取文件列表
  let uploadFiles = []

  // 优先使用我们维护的文件列表
  if (selectedFiles.value && selectedFiles.value.length > 0) {
    console.log('使用维护的文件列表:', selectedFiles.value.length)
    uploadFiles = selectedFiles.value
  }
  // 方法1: 尝试从 uploadFiles 属性获取
  else if (uploadComponent.uploadFiles && uploadComponent.uploadFiles.length > 0) {
    console.log('从 uploadFiles 获取文件列表:', uploadComponent.uploadFiles.length)
    uploadFiles = uploadComponent.uploadFiles
  }
  // 方法2: 尝试从 fileList 属性获取
  else if (uploadComponent.fileList && uploadComponent.fileList.length > 0) {
    console.log('从 fileList 获取文件列表:', uploadComponent.fileList.length)
    uploadFiles = uploadComponent.fileList
  }
  // 方法3: 检查是否有其他可能的属性
  else if (uploadComponent.$refs && uploadComponent.$refs.upload) {
    const innerUpload = uploadComponent.$refs.upload
    if (innerUpload.uploadFiles && innerUpload.uploadFiles.length > 0) {
      console.log('从内部 uploadFiles 获取文件列表:', innerUpload.uploadFiles.length)
      uploadFiles = innerUpload.uploadFiles
    }
  }

  console.log('Upload组件调试信息:', {
    hasUploadFiles: !!uploadComponent.uploadFiles,
    uploadFilesLength: uploadComponent.uploadFiles?.length || 0,
    hasFileList: !!uploadComponent.fileList,
    fileListLength: uploadComponent.fileList?.length || 0,
    componentKeys: Object.keys(uploadComponent),
  })

  if (uploadFiles.length === 0) {
    ElMessage.warning('请先选择要上传的文件')
    return
  }

  // 记录找到的文件
  console.log('找到文件列表:', uploadFiles.length, '个文件')
  uploadFiles.forEach((file: any, index: number) => {
    console.log(`文件 ${index + 1}:`, file.name)
  })

  if (uploadFiles.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  try {
    uploadLoading.value = true
    let successCount = 0
    let errorCount = 0
    const errors = []    // 遍历所有选择的文件进行上传
    for (const file of uploadFiles) {
      // Element Plus Upload 组件中，原始文件对象存储在 raw 属性中
      const fileToUpload = file.raw

      if (!fileToUpload || !(fileToUpload instanceof File)) {
        console.error('无效的文件对象:', file)
        errorCount++
        errors.push(`${file.name || '未知文件'}: 无效的文件格式`)
        continue
      }

      try {
        console.log('准备上传文件:', fileToUpload.name, '类型:', fileToUpload.type, '大小:', fileToUpload.size)
        // 使用调试辅助函数记录详细信息
        logFileInfo(fileToUpload)

        // 确认文件对象是有效的 File 实例
        console.log('文件对象类型检查:', {
          isFile: fileToUpload instanceof File,
          constructor: fileToUpload.constructor.name,
          hasSlice: typeof fileToUpload.slice === 'function'
        })

        // 确保传递原始文件名
        await projectStore.uploadAttachment(
          projectId.value,
          fileToUpload,
          uploadForm.value.description,
          fileToUpload.name // 显式传递原始文件名
        )
        successCount++
      } catch (err: any) {
        errorCount++
        console.error('文件上传失败:', err)

        // 记录详细的错误信息
        if (err.response) {
          console.error('响应状态:', err.response.status)
          console.error('响应标头:', err.response.headers)
          console.error('响应数据:', err.response.data)
        }

        // 提取错误消息
        let errorMsg = '未知错误'
        if (err.response?.data?.error) {
          errorMsg = err.response.data.error
        } else if (err.response?.data?.message) {
          errorMsg = err.response.data.message
        } else if (err.response?.data?.detail) {
          errorMsg = err.response.data.detail
        } else if (err.message) {
          errorMsg = err.message
        }

        // 对特定错误类型提供更清晰的信息
        if (err.response?.status === 400) {
          if (errorMsg.includes('file')) {
            errorMsg = '文件参数错误，请检查文件是否正常'
          } else {
            errorMsg = `请求格式错误: ${errorMsg}`
          }
        }

        errors.push(`${fileToUpload.name || '未知文件'}: ${errorMsg}`)
      }
    }

    // 根据上传结果显示不同消息
    if (successCount > 0 && errorCount === 0) {
      ElMessage.success(`成功上传 ${successCount} 个附件`)
      showUploadDialog.value = false
      uploadForm.value.description = ''

      // 清理文件列表
      selectedFiles.value = []
      if (uploadComponent.clearFiles) {
        uploadComponent.clearFiles()
      }
    } else if (successCount > 0 && errorCount > 0) {
      ElMessage.warning(`已上传 ${successCount} 个附件，${errorCount} 个文件上传失败`)
      // 部分上传成功，清理已上传的文件，保留失败的文件
      // 注意：这里可以进一步优化，只移除成功的文件
    } else {
      ElMessage.error('所有文件上传失败')
      // 显示详细错误信息
      if (errors.length > 0) {
        ElMessage.error(errors[0])
      }
    }

    // 重新获取附件列表
    await fetchAttachments()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.error || error.message || '附件上传失败，请稍后重试')
  } finally {
    uploadLoading.value = false
  }
}

// 下载附件
const downloadAttachment = async (attachment: Attachment) => {
  if (downloadingAttachments.value.has(attachment.id)) {
    ElMessage.warning('该文件正在下载中...')
    return
  }

  let downloadNotification: any = null

  try {
    downloadingAttachments.value.add(attachment.id)

    // 对于大文件，显示加载通知
    if (attachment.file_size > 5 * 1024 * 1024) { // 大于5MB显示进度通知
      downloadNotification = ElMessage({
        message: `正在下载 ${attachment.original_name}...`,
        type: 'info',
        duration: 0,
        showClose: true,
      })
    }

    await projectStore.downloadAttachment(
      projectId.value,
      attachment.id,
      attachment.original_name || '未知文件'
    )

    // 关闭原通知（如果存在）
    if (downloadNotification) {
      downloadNotification.close()
    }

    ElMessage.success(`文件 ${attachment.original_name} 下载成功`)
  } catch (error: any) {
    // 关闭原通知（如果存在）
    if (downloadNotification) {
      downloadNotification.close()
    }

    if (error.response?.status === 404) {
      ElMessage.error('文件不存在或已被删除')
      // 文件不存在时可以刷新附件列表，确保UI与后端数据一致
      await fetchAttachments()
    } else if (error.response?.status === 403) {
      ElMessage.error('没有权限下载该文件')
    } else if (error.response?.status === 500) {
      ElMessage.error('服务器错误，下载失败')
    } else if (error.message?.includes('Network') || error.message?.includes('network')) {
      ElMessage.error('网络错误，请检查您的网络连接')
    } else {
      ElMessage.error('下载失败，请稍后重试')
    }
  } finally {
    downloadingAttachments.value.delete(attachment.id)
  }
}

// 删除附件
const deleteAttachment = async (attachment: Attachment) => {
  if (deletingAttachments.value.has(attachment.id)) {
    ElMessage.warning('该文件正在删除中...')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${attachment.original_name}" 吗？此操作不可撤销。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )

    deletingAttachments.value.add(attachment.id)

    await projectStore.deleteAttachment(projectId.value, attachment.id)

    // 检查是否删除的是最后一个附件
    const isLastAttachment = attachments.value.length === 1

    // 删除成功后刷新附件列表
    await fetchAttachments()

    // 根据删除结果提供不同的提示
    if (isLastAttachment) {
      ElMessage.success('附件删除成功，项目现在没有附件')

      // 如果当前视图中已无附件，重置状态
      if (attachments.value.length === 0) {
        // 更新页面状态，显示上传第一个附件的提示
        // 注意：fetchAttachments 已经更新了 attachments.value
      }
    } else {
      ElMessage.success('附件删除成功')
    }

  } catch (error: any) {
    if (error === 'cancel') {
      // 用户取消删除
      return
    }

    if (error.response?.status === 404) {
      ElMessage.error('文件不存在或已被删除')
      // 文件不存在，也刷新列表
      await fetchAttachments()
    } else if (error.response?.status === 403) {
      ElMessage.error('没有权限删除该文件')
    } else {
      const errorMessage = error.response?.data?.error || '删除失败，请稍后重试'
      ElMessage.error(errorMessage)
    }
  } finally {
    deletingAttachments.value.delete(attachment.id)
  }
}

// 处理项目更新
const handleProjectUpdated = () => {
  showEditDialog.value = false
  fetchProject()
}

// 格式化日期时间
const formatDateTime = (dateString: string | undefined) => {
  if (!dateString) return '未知时间'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '无效日期'
  return date.toLocaleString('zh-CN')
}

// 格式化文件大小
const formatFileSize = (bytes: number | undefined) => {
  if (!bytes || bytes === 0) return '0 Bytes'
  if (isNaN(bytes)) return '未知大小'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 获取权限文本
const getPermissionText = (permission: string) => {
  const map = {
    read: '只读权限',
    edit: '编辑权限',
    admin: '管理员权限'
  }
  return map[permission as keyof typeof map] || permission
}

// 获取权限标签类型
const getPermissionTagType = (permission: string) => {
  const map = {
    read: '',
    edit: 'warning',
    admin: 'danger'
  }
  return map[permission as keyof typeof map] || ''
}

// 获取文件类型图标
const getFileIcon = (fileType: string, fileName: string) => {
  // 优先检查MIME类型
  if (fileType) {
    if (fileType.startsWith('image/')) {
      return 'Picture'
    } else if (fileType.includes('pdf')) {
      return 'Document'
    } else if (fileType.includes('msword') || fileType.includes('wordprocessing')) {
      return 'Document'
    } else if (fileType.includes('excel') || fileType.includes('spreadsheet')) {
      return 'Document'
    } else if (fileType.includes('powerpoint') || fileType.includes('presentation')) {
      return 'Document'
    } else if (fileType.includes('video/')) {
      return 'VideoPlay'
    } else if (fileType.includes('audio/')) {
      return 'Microphone'
    } else if (fileType.includes('zip') || fileType.includes('rar') || fileType.includes('7z') || fileType.includes('compressed')) {
      return 'Folder'
    } else if (fileType.includes('text/')) {
      return 'Document'
    }
  }

  // 如果没有MIME类型或无法判断，则通过文件扩展名判断
  if (fileName) {
    const ext = fileName.split('.').pop()?.toLowerCase()

    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'].includes(ext || '')) {
      return 'Picture'
    } else if (ext === 'pdf') {
      return 'Document'
    } else if (['doc', 'docx', 'odt', 'rtf'].includes(ext || '')) {
      return 'Document'
    } else if (['xls', 'xlsx', 'csv', 'ods'].includes(ext || '')) {
      return 'Document'
    } else if (['ppt', 'pptx', 'odp'].includes(ext || '')) {
      return 'Document'
    } else if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'].includes(ext || '')) {
      return 'VideoPlay'
    } else if (['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac'].includes(ext || '')) {
      return 'Microphone'
    } else if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext || '')) {
      return 'Folder'
    } else if (['txt', 'md', 'json', 'xml', 'html', 'css', 'js'].includes(ext || '')) {
      return 'Document'
    }
  }

  // 默认图标
  return 'Document'
}

// 检查是否为图片文件
const isImageFile = (fileType: string) => {
  return fileType?.startsWith('image/')
}

// 获取单位显示名称
const getUnitDisplay = (department: string) => {
  const unitMap: { [key: string]: string } = {
    'direct': '市局直属部门',
    'tianyuan': '天元分局',
    'lusong': '芦淞分局',
    'hetang': '荷塘分局',
    'shifeng': '石峰分局',
    'dongjiabai': '董家塅分局',
    'kaifaqu': '经开区分局',
    'lukou': '渌口分局',
    'liling': '醴陵市公安局',
    'youxian': '攸县公安局',
    'chaling': '茶陵县公安局',
    'yanling': '炎陵县公安局'
  }
  return unitMap[department] || department
}

onMounted(async () => {
  await fetchProject()
  if (project.value) {
    // 如果项目数据中没有附件或附件为空，则单独获取
    const tasks = []
    if (!project.value.attachments || project.value.attachments.length === 0) {
      tasks.push(fetchAttachments())
    }
    tasks.push(fetchMembers())

    await Promise.all(tasks)
  }
})

// 处理取消上传
const handleCancel = () => {
  showUploadDialog.value = false
  selectedFiles.value = []
  uploadForm.value.description = ''

  // 清理上传组件的文件列表
  const uploadComponent = uploadRef.value
  if (uploadComponent && uploadComponent.clearFiles) {
    uploadComponent.clearFiles()
  }
}
</script>

<style scoped>
.project-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  font-size: 14px;
  color: #666;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.content {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0 16px;
  box-sizing: border-box;
}

/* 自定义滚动条样式 */
.content::-webkit-scrollbar {
  width: 8px;
}

.content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 确保项目内容可以滚动 */
.project-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 20px;
}

.loading-container {
  padding: 40px;
}

.info-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: #303133;
}

.card-header el-icon {
  margin-right: 0;
  flex-shrink: 0;
}

.card-header span {
  margin-left: 2px;
  line-height: 1;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px 24px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  min-height: 28px;
}

.info-item label {
  font-weight: 500;
  color: #666;
  min-width: 90px;
  margin-right: 12px;
  flex-shrink: 0;
  line-height: 1.5;
}

.info-item span {
  color: #333;
  flex: 1;
  word-wrap: break-word;
  word-break: break-all;
  line-height: 1.5;
}

.case-summary {
  border-top: 1px solid #f0f0f0;
  padding-top: 20px;
}

.case-summary label {
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
  display: block;
}

.case-summary p {
  margin: 0;
  color: #333;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap;
  max-width: 100%;
}

.stats-row {
  margin: 24px 0;
}

.stat-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
  padding: 12px;
  border-radius: 8px;
}

.member-icon {
  color: #409eff;
  background-color: #ecf5ff;
}

.node-icon {
  color: #67c23a;
  background-color: #f0f9ff;
}

.my-node-icon {
  color: #e6a23c;
  background-color: #fdf6ec;
}

.mindmap-attachment-icon {
  color: #409eff;
  background-color: #ecf5ff;
}

.my-attachment-icon {
  color: #f56c6c;
  background-color: #fef0f0;
}

.case-attachment-icon {
  color: #e6a23c;
  background-color: #fdf6ec;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.attachments-card,
.members-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header.with-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header.with-actions>div:first-child {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-header.with-actions>div:first-child el-icon {
  margin-right: 0;
  flex-shrink: 0;
}

.card-header.with-actions>div:first-child span {
  margin-left: 2px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}

.attachment-item:hover {
  background-color: #fafafa;
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  font-size: 24px;
  color: #409eff;
}

.file-icon-Picture {
  color: #67c23a;
}

.file-icon-VideoPlay {
  color: #e6a23c;
}

.file-icon-Microphone {
  color: #f56c6c;
}

.file-icon-Document {
  color: #409eff;
}

.file-icon-Folder {
  color: #e6a23c;
}

.attachment-details {
  flex: 1;
}

.attachment-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.attachment-meta {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}

.attachment-description {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.attachment-actions {
  display: flex;
  gap: 8px;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.member-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  transition: background-color 0.2s ease;
}

.member-item:hover {
  background-color: #fafafa;
}

.member-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
}

.member-details {
  flex: 1;
}

.member-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.member-meta {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-permission {
  display: flex;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .stats-row .el-col {
    margin-bottom: 16px;
  }

  .attachment-item,
  .member-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .attachment-actions,
  .member-permission {
    align-self: flex-end;
  }
}
</style>
