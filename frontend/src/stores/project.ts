import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectAPI } from '@/api'

export interface Project {
  id: number
  name: string
  case_number: string
  filing_unit: string
  filing_unit_display: string
  case_summary: string
  creator: {
    id: number
    username: string
    real_name: string
  }
  members: ProjectMember[]
  member_count: number
  node_count: number
  my_node_count: number
  mindmap_attachment_count: number
  my_mindmap_attachment_count: number
  attachments: CaseAttachment[]
  created_at: string
  updated_at: string
}

export interface CaseAttachment {
  id: number
  file: string
  original_name: string
  file_size: number
  file_size_display: string
  file_type: string
  description: string
  uploader: {
    id: number
    username: string
    real_name: string
  }
  created_at: string
}

export interface ProjectMember {
  user: {
    id: number
    username: string
    real_name: string
    email?: string
    department?: string
  }
  permission: 'read' | 'edit' | 'admin'
  joined_at: string
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const projectMembers = ref<ProjectMember[]>([])
  const loading = ref(false)

  // 获取项目列表
  const fetchProjects = async () => {
    loading.value = true
    try {
      const response = await projectAPI.list()
      // 处理分页数据或直接数组
      const projectsData = response.data.results || response.data || []
      projects.value = Array.isArray(projectsData) ? projectsData.map(project => ({
        ...project,
        creator: project.creator || { id: 0, username: '未知', real_name: '未知' },
        member_count: project.member_count || 0,
        node_count: project.node_count || 0,
        attachments: project.attachments || [],
        members: project.members || []
      })) : []
      return projects.value
    } catch (error) {
      console.error('获取项目列表失败:', error)
      projects.value = []
      throw error
    } finally {
      loading.value = false
    }
  }

  // 创建项目
  const createProject = async (data: FormData | { name: string; case_number: string; filing_unit: string; case_summary: string }) => {
    try {
      const response = await projectAPI.create(data)
      projects.value.unshift(response.data)
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 获取项目详情
  const fetchProject = async (id: number) => {
    loading.value = true
    try {
      const response = await projectAPI.get(id)
      currentProject.value = response.data
      return response.data
    } catch (error) {
      throw error
    } finally {
      loading.value = false
    }
  }

  // 更新项目
  const updateProject = async (id: number, data: Partial<{ name: string; case_number: string; filing_unit: string; case_summary: string }>) => {
    try {
      const response = await projectAPI.update(id, data)
      currentProject.value = response.data

      // 更新列表中的项目
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = response.data
      }

      return response.data
    } catch (error) {
      throw error
    }
  }

  // 删除项目
  const deleteProject = async (id: number) => {
    try {
      await projectAPI.delete(id)
      projects.value = projects.value.filter(p => p.id !== id)
      if (currentProject.value?.id === id) {
        currentProject.value = null
      }
    } catch (error) {
      throw error
    }
  }

  // 获取项目成员
  const fetchProjectMembers = async (id: number) => {
    try {
      const response = await projectAPI.getMembers(id)
      projectMembers.value = response.data
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 邀请成员
  const inviteMember = async (projectId: number, data: { username: string; permission: string }) => {
    try {
      const response = await projectAPI.inviteMember(projectId, data)
      await fetchProjectMembers(projectId) // 重新获取成员列表
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 移除成员
  const removeMember = async (projectId: number, username: string) => {
    try {
      await projectAPI.removeMember(projectId, { username })
      await fetchProjectMembers(projectId) // 重新获取成员列表
    } catch (error) {
      throw error
    }
  }

  // 更新成员权限
  const updateMemberPermission = async (projectId: number, username: string, permission: string) => {
    try {
      const response = await projectAPI.updateMemberPermission(projectId, { username, permission })
      await fetchProjectMembers(projectId) // 重新获取成员列表
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 上传附件
  const uploadAttachment = async (projectId: number, file: File, description?: string) => {
    try {
      const response = await projectAPI.uploadAttachment(projectId, file, description)
      // 重新获取项目详情以更新附件列表
      if (currentProject.value?.id === projectId) {
        await fetchProject(projectId)
      }
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 获取附件列表
  const fetchAttachments = async (projectId: number) => {
    try {
      const response = await projectAPI.getAttachments(projectId)
      return response.data
    } catch (error) {
      throw error
    }
  }

  // 下载附件
  const downloadAttachment = async (projectId: number, attachmentId: number, filename: string) => {
    try {
      const response = await projectAPI.downloadAttachment(projectId, attachmentId)

      // 创建下载链接
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      return true
    } catch (error) {
      throw error
    }
  }

  // 删除附件
  const deleteAttachment = async (projectId: number, attachmentId: number) => {
    try {
      await projectAPI.deleteAttachment(projectId, attachmentId)
      return true
    } catch (error) {
      throw error
    }
  }

  return {
    projects,
    currentProject,
    projectMembers,
    loading,
    fetchProjects,
    createProject,
    fetchProject,
    updateProject,
    deleteProject,
    fetchProjectMembers,
    inviteMember,
    removeMember,
    updateMemberPermission,
    uploadAttachment,
    fetchAttachments,
    downloadAttachment,
    deleteAttachment
  }
})
