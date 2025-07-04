<template>
  <div class="project-list">
    <AppLayout>
      <template #header>
        <div class="page-header">
          <h1>项目管理</h1>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon>
              <Plus />
            </el-icon>
            创建项目
          </el-button>
        </div>
      </template>

      <div class="projects-content">
        <div v-if="projectStore.loading" class="loading-container">
          <el-skeleton :rows="5" animated />
        </div>

        <div v-else-if="projectStore.projects.length" class="projects-grid">
          <el-card v-for="project in projectStore.projects" :key="project.id" class="project-card"
            @click="$router.push(`/projects/${project.id}`)">
            <div class="project-header">
              <h3>{{ project.name }}</h3>
              <div class="project-meta">
                <el-tag size="small" type="info">{{ project.case_number }}</el-tag>
                <el-tag size="small">{{ project.filing_unit_display }}</el-tag>
              </div>
              <el-dropdown @command="(command: string) => handleProjectAction(command, project)">
                <el-button text @click.stop>
                  <el-icon>
                    <MoreFilled />
                  </el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="mindmap">
                      <el-icon>
                        <Share />
                      </el-icon>
                      思维导图
                    </el-dropdown-item>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="members">成员管理</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <p class="project-description">{{ project.case_summary || '暂无案情描述' }}</p>

            <div class="project-stats">
              <div class="stat">
                <el-icon>
                  <User />
                </el-icon>
                <span>{{ project.member_count || 0 }} 成员</span>
              </div>
              <div class="stat">
                <el-icon>
                  <Connection />
                </el-icon>
                <span>{{ project.node_count || 0 }} 节点</span>
              </div>
            </div>

            <div class="project-footer">
              <div class="project-creator">
                创建者: {{ project.creator?.username || '未知' }}
              </div>
              <div class="project-actions">
                <el-button size="small" type="primary" @click.stop="$router.push(`/projects/${project.id}/mindmap`)">
                  <el-icon>
                    <Share />
                  </el-icon>
                  思维导图
                </el-button>
              </div>
              <div class="project-time">
                {{ formatDate(project.updated_at) }}
              </div>
            </div>
          </el-card>
        </div>

        <el-empty v-else description="还没有项目">
          <el-button type="primary" @click="showCreateDialog = true">
            创建第一个项目
          </el-button>
        </el-empty>
      </div>
    </AppLayout>

    <!-- 创建项目对话框 -->
    <CreateProjectDialog v-model="showCreateDialog" @created="handleProjectCreated" />

    <!-- 编辑项目对话框 -->
    <EditProjectDialog v-model="showEditDialog" :project="selectedProject" @updated="handleProjectUpdated" />

    <!-- 成员管理对话框 -->
    <ProjectMembersDialog v-model="showMembersDialog" :project-id="selectedProject?.id || null" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, MoreFilled, User, Connection, Share } from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import CreateProjectDialog from '@/components/CreateProjectDialog.vue'
import EditProjectDialog from '@/components/EditProjectDialog.vue'
import ProjectMembersDialog from '@/components/ProjectMembersDialog.vue'
import type { Project } from '@/stores/project'

const projectStore = useProjectStore()
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showMembersDialog = ref(false)
const selectedProject = ref<Project | null>(null)

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const handleProjectAction = async (command: string, project: Project) => {
  switch (command) {
    case 'mindmap':
      // 跳转到思维导图页面
      window.open(`/projects/${project.id}/mindmap`, '_blank')
      break
    case 'edit':
      selectedProject.value = project
      showEditDialog.value = true
      break
    case 'members':
      selectedProject.value = project
      showMembersDialog.value = true
      break
    case 'delete':
      try {
        await ElMessageBox.confirm(
          `确定要删除案件 "${project.name}" 吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await projectStore.deleteProject(project.id)
        ElMessage.success('案件删除成功')
      } catch (error) {
        // 用户取消操作
      }
      break
  }
}

const handleProjectCreated = () => {
  showCreateDialog.value = false
  projectStore.fetchProjects()
}

const handleProjectUpdated = () => {
  showEditDialog.value = false
  selectedProject.value = null
  projectStore.fetchProjects()
}

onMounted(() => {
  projectStore.fetchProjects()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #333;
}

.projects-content {
  max-width: 1200px;
  margin: 0 auto;
}

.loading-container {
  padding: 40px;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.project-card {
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.project-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  line-height: 1.4;
}

.project-description {
  margin: 0 0 16px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.project-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #999;
}

.project-creator {
  font-weight: 500;
  flex: 1;
}

.project-actions {
  display: flex;
  gap: 8px;
}

.project-time {
  white-space: nowrap;
}
</style>
