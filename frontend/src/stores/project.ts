import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectAPI } from '@/api'

export interface Project {
  id: number
  name: string
  description: string
  creator: {
    id: number
    username: string
    email: string
  }
  member_count: number
  node_count: number
  created_at: string
  updated_at: string
}

export interface ProjectMember {
  user: {
    id: number
    username: string
    email: string
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
      // 确保返回的数据是数组，并且每个项目都有完整的creator信息
      const projectsData = Array.isArray(response.data) ? response.data : []
      projects.value = projectsData.map(project => ({
        ...project,
        creator: project.creator || { id: 0, username: '未知', email: '' },
        member_count: project.member_count || 0,
        node_count: project.node_count || 0
      }))
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
  const createProject = async (data: { name: string; description?: string }) => {
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
  const updateProject = async (id: number, data: Partial<{ name: string; description: string }>) => {
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
    updateMemberPermission
  }
})
