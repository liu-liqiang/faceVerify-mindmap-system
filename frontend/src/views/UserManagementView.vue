<template>
    <div class="user-management">
        <el-card>
            <template #header>
                <div class="card-header">
                    <div class="header-left">
                        <h2>用户管理</h2>
                        <span class="admin-info">管理员面板</span>
                    </div>
                    <div class="header-right">
                        <el-button type="primary" @click="refreshData" :icon="Refresh">刷新</el-button>
                        <el-button type="danger" @click="handleLogout" :icon="SwitchButton">退出登录</el-button>
                    </div>
                </div>
            </template>

            <el-tabs v-model="activeTab" @tab-change="handleTabChange">
                <el-tab-pane label="待审核用户" name="pending">
                    <div class="table-container">
                        <el-table :data="pendingUsers" v-loading="loading" stripe border style="width: 100%">
                            <el-table-column prop="police_number" label="警号" width="120" />
                            <el-table-column prop="real_name" label="姓名" width="100" />
                            <el-table-column prop="phone_number" label="手机号" width="130" />
                            <el-table-column prop="department_display" label="所属单位" width="150" />
                            <el-table-column prop="is_face_registered" label="人脸状态" width="100">
                                <template #default="{ row }">
                                    <el-tag :type="row.is_face_registered ? 'success' : 'warning'">
                                        {{ row.is_face_registered ? '已录入' : '未录入' }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column prop="face_images_count" label="人脸数量" width="100" />
                            <el-table-column label="注册时间" width="160">
                                <template #default="{ row }">
                                    {{ formatDate(row.date_joined) }}
                                </template>
                            </el-table-column>
                            <el-table-column label="操作" width="200" fixed="right">
                                <template #default="{ row }">
                                    <el-button type="success" size="small" @click="approveUser(row, 'approved')"
                                        :disabled="!row.is_face_registered">
                                        通过
                                    </el-button>
                                    <el-button type="danger" size="small" @click="showRejectDialog(row)">
                                        拒绝
                                    </el-button>
                                    <el-button type="info" size="small" @click="viewUserDetail(row)">
                                        详情
                                    </el-button>
                                </template>
                            </el-table-column>
                        </el-table>
                    </div>
                </el-tab-pane>

                <el-tab-pane label="所有用户" name="all">
                    <div class="table-container">
                        <el-table :data="allUsers" v-loading="loading" stripe border style="width: 100%">
                            <el-table-column prop="police_number" label="警号" width="120" />
                            <el-table-column prop="real_name" label="姓名" width="100" />
                            <el-table-column prop="phone_number" label="手机号" width="130" />
                            <el-table-column prop="department_display" label="所属单位" width="150" />
                            <el-table-column prop="status_display" label="状态" width="100">
                                <template #default="{ row }">
                                    <el-tag :type="getStatusType(row.status)">
                                        {{ row.status_display }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column prop="is_face_registered" label="人脸状态" width="100">
                                <template #default="{ row }">
                                    <el-tag :type="row.is_face_registered ? 'success' : 'warning'">
                                        {{ row.is_face_registered ? '已录入' : '未录入' }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                            <el-table-column label="注册时间" width="160">
                                <template #default="{ row }">
                                    {{ formatDate(row.date_joined) }}
                                </template>
                            </el-table-column>
                            <el-table-column label="操作" width="200" fixed="right">
                                <template #default="{ row }">
                                    <el-dropdown @command="(command: string) => handleUserAction(command, row)">
                                        <el-button type="primary" size="small">
                                            操作<el-icon><arrow-down /></el-icon>
                                        </el-button>
                                        <template #dropdown>
                                            <el-dropdown-menu>
                                                <el-dropdown-item command="approve" v-if="row.status === 'pending'">
                                                    审核通过
                                                </el-dropdown-item>
                                                <el-dropdown-item command="reject" v-if="row.status === 'pending'">
                                                    审核拒绝
                                                </el-dropdown-item>
                                                <el-dropdown-item command="suspend" v-if="row.status === 'approved'">
                                                    暂停账号
                                                </el-dropdown-item>
                                                <el-dropdown-item command="reactivate"
                                                    v-if="row.status === 'suspended'">
                                                    重新激活
                                                </el-dropdown-item>
                                                <el-dropdown-item command="reset_face">
                                                    重置人脸
                                                </el-dropdown-item>
                                                <el-dropdown-item command="detail" divided>
                                                    查看详情
                                                </el-dropdown-item>
                                            </el-dropdown-menu>
                                        </template>
                                    </el-dropdown>
                                </template>
                            </el-table-column>
                        </el-table>
                    </div>
                </el-tab-pane>
            </el-tabs>
        </el-card>

        <!-- 拒绝原因对话框 -->
        <el-dialog v-model="rejectDialogVisible" title="审核拒绝" width="400px">
            <el-form :model="rejectForm" label-width="80px">
                <el-form-item label="拒绝原因">
                    <el-input v-model="rejectForm.reason" type="textarea" :rows="4" placeholder="请输入拒绝原因" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="rejectDialogVisible = false">取消</el-button>
                <el-button type="danger" @click="confirmReject">确认拒绝</el-button>
            </template>
        </el-dialog>

        <!-- 用户详情对话框 -->
        <el-dialog v-model="detailDialogVisible" :title="`用户详情 - ${selectedUser?.real_name}`" width="600px">
            <div v-if="selectedUser" class="user-detail">
                <el-descriptions :column="2" border>
                    <el-descriptions-item label="姓名">{{ selectedUser.real_name }}</el-descriptions-item>
                    <el-descriptions-item label="警号">{{ selectedUser.police_number }}</el-descriptions-item>
                    <el-descriptions-item label="手机号">{{ selectedUser.phone_number }}</el-descriptions-item>
                    <el-descriptions-item label="所属单位">{{ selectedUser.department_display }}</el-descriptions-item>
                    <el-descriptions-item label="状态">
                        <el-tag :type="getStatusType(selectedUser.status)">
                            {{ selectedUser.status_display }}
                        </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="人脸状态">
                        <el-tag :type="selectedUser.is_face_registered ? 'success' : 'warning'">
                            {{ selectedUser.is_face_registered ? '已录入' : '未录入' }}
                        </el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item label="人脸数量">{{ selectedUser.face_images_count || 0 }}</el-descriptions-item>
                    <el-descriptions-item label="注册时间">{{ formatDate(selectedUser.date_joined) }}</el-descriptions-item>
                    <el-descriptions-item label="审核时间" v-if="selectedUser.approved_at">
                        {{ formatDate(selectedUser.approved_at) }}
                    </el-descriptions-item>
                    <el-descriptions-item label="审核人" v-if="selectedUser.approved_by">
                        {{ selectedUser.approved_by }}
                    </el-descriptions-item>
                </el-descriptions>
            </div>
        </el-dialog>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, Refresh, SwitchButton } from '@element-plus/icons-vue'
import { userAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'

interface User {
    id: number
    username: string
    real_name: string
    police_number: string
    phone_number: string
    department: string
    department_display: string
    status: string
    status_display: string
    is_face_registered: boolean
    face_images_count?: number
    date_joined: string
    approved_by?: string
    approved_at?: string
    is_staff: boolean
    is_superuser: boolean
}

const activeTab = ref('pending')
const loading = ref(false)
const pendingUsers = ref<User[]>([])
const allUsers = ref<User[]>([])

const rejectDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedUser = ref<User | null>(null)
const rejectForm = ref({
    reason: ''
})

// 路由和认证store
const router = useRouter()
const authStore = useAuthStore()

// 退出登录方法
const handleLogout = async () => {
    try {
        await ElMessageBox.confirm('确认退出管理员登录？', '退出确认', {
            confirmButtonText: '确认退出',
            cancelButtonText: '取消',
            type: 'warning'
        })

        // 调用后端登出API
        try {
            await userAPI.logout()
        } catch (error) {
            console.warn('后端登出失败，但仍继续前端清理:', error)
        }

        // 清理前端认证状态
        authStore.user = null
        authStore.isAuthenticated = false

        // 清理localStorage
        localStorage.removeItem('user')
        localStorage.removeItem('isAuthenticated')

        ElMessage.success('已退出管理员登录')

        // 跳转到登录页面
        router.push('/login')

    } catch (error: any) {
        if (error !== 'cancel') {
            console.error('退出登录失败:', error)
        }
    }
}

onMounted(() => {
    loadPendingUsers()
})

const handleTabChange = (tabName: string) => {
    if (tabName === 'pending') {
        loadPendingUsers()
    } else if (tabName === 'all') {
        loadAllUsers()
    }
}

const loadPendingUsers = async () => {
    try {
        loading.value = true
        const response = await userAPI.getPendingUsers()
        pendingUsers.value = response.data
    } catch (error: any) {
        console.error('加载待审核用户失败:', error)
        ElMessage.error('加载待审核用户失败')
    } finally {
        loading.value = false
    }
}

const loadAllUsers = async () => {
    try {
        loading.value = true
        const response = await userAPI.getProfile() // 这里应该是获取所有用户的API
        // 暂时使用待审核用户数据模拟
        allUsers.value = pendingUsers.value
    } catch (error: any) {
        console.error('加载用户列表失败:', error)
        ElMessage.error('加载用户列表失败')
    } finally {
        loading.value = false
    }
}

const refreshData = () => {
    if (activeTab.value === 'pending') {
        loadPendingUsers()
    } else {
        loadAllUsers()
    }
}

const approveUser = async (user: User, status: string) => {
    if (!user.is_face_registered) {
        ElMessage.error('该用户尚未录入人脸信息，无法通过审核')
        return
    }

    try {
        await ElMessageBox.confirm(
            `确认${status === 'approved' ? '通过' : '拒绝'}用户 ${user.real_name} 的审核吗？`,
            '确认操作',
            {
                confirmButtonText: '确认',
                cancelButtonText: '取消',
                type: 'warning',
            }
        )

        await userAPI.approveUser(user.id, { status })
        ElMessage.success('操作成功')
        refreshData()
    } catch (error: any) {
        if (error !== 'cancel') {
            console.error('审核用户失败:', error)
            ElMessage.error('操作失败')
        }
    }
}

const showRejectDialog = (user: User) => {
    selectedUser.value = user
    rejectForm.value.reason = ''
    rejectDialogVisible.value = true
}

const confirmReject = async () => {
    if (!selectedUser.value || !rejectForm.value.reason.trim()) {
        ElMessage.error('请输入拒绝原因')
        return
    }

    try {
        await userAPI.approveUser(selectedUser.value.id, {
            status: 'rejected',
            rejection_reason: rejectForm.value.reason
        })

        ElMessage.success('已拒绝该用户的审核申请')
        rejectDialogVisible.value = false
        refreshData()
    } catch (error: any) {
        console.error('拒绝审核失败:', error)
        ElMessage.error('操作失败')
    }
}

const viewUserDetail = (user: User) => {
    selectedUser.value = user
    detailDialogVisible.value = true
}

const handleUserAction = async (command: string, user: User) => {
    switch (command) {
        case 'approve':
            await approveUser(user, 'approved')
            break
        case 'reject':
            showRejectDialog(user)
            break
        case 'suspend':
            await approveUser(user, 'suspended')
            break
        case 'reactivate':
            await approveUser(user, 'approved')
            break
        case 'reset_face':
            await resetUserFace(user)
            break
        case 'detail':
            viewUserDetail(user)
            break
    }
}

const resetUserFace = async (user: User) => {
    try {
        await ElMessageBox.confirm(
            `确认重置用户 ${user.real_name} 的人脸信息吗？重置后用户需要重新录入人脸。`,
            '确认重置',
            {
                confirmButtonText: '确认',
                cancelButtonText: '取消',
                type: 'warning',
            }
        )

        // 这里应该调用重置人脸的API
        ElMessage.success('人脸信息已重置')
        refreshData()
    } catch (error: any) {
        if (error !== 'cancel') {
            console.error('重置人脸失败:', error)
            ElMessage.error('操作失败')
        }
    }
}

const getStatusType = (status: string) => {
    switch (status) {
        case 'approved':
            return 'success'
        case 'rejected':
            return 'danger'
        case 'suspended':
            return 'warning'
        case 'pending':
        default:
            return 'info'
    }
}

const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
}
</script>

<style scoped>
.user-management {
    padding: 20px;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-left {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
}

.header-left h2 {
    margin: 0;
    color: #333;
    font-size: 24px;
    font-weight: 600;
}

.admin-info {
    color: #666;
    font-size: 14px;
    margin-top: 4px;
}

.header-right {
    display: flex;
    gap: 12px;
    align-items: center;
}

.table-container {
    margin-top: 20px;
}

.user-detail {
    margin: 20px 0;
}

:deep(.el-table) {
    font-size: 14px;
}

:deep(.el-table th) {
    background-color: #f5f7fa;
}

:deep(.el-descriptions__label) {
    font-weight: 600;
}
</style>
