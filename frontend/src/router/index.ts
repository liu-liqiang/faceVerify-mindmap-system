import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guest: true }
    },
    {
      path: '/projects',
      name: 'projects',
      component: () => import('../views/ProjectListView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/projects/:id',
      name: 'project-detail',
      component: () => import('../views/ProjectDetailView.vue'),
      meta: { requiresAuth: true }
    },
    {
      // 思维导图在projects之下
      path: '/projects/:id/mindmap',
      name: 'mindmap',
      component: () => import('../views/MindMapView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/projects/:id/members',
      name: 'project-members',
      component: () => import('../views/ProjectMembersView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/debug',
      name: 'debug',
      component: () => import('../views/DebugView.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFoundView.vue')
    },
    {
      path: '/face-verify/:user',
      name: 'face-verify',
      component: () => import('../views/FaceVerifyView.vue'),
      meta: { guest: true }
    },
    {
      path: '/face-register',
      name: 'FaceRegister',
      component: () => import('../views/FaceRegisterView.vue'),
      meta: { guest: true }
    },
    {
      path: '/face-supplement',
      name: 'FaceSupplement',
      component: () => import('../views/FaceSupplementView.vue'),
      meta: { guest: true }
    },
    {
      path: '/user-management',
      name: 'UserManagement',
      component: () => import('../views/UserManagementView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin-login',
      name: 'AdminLogin',
      component: () => import('../views/AdminLoginView.vue'),
      meta: { guest: true, title: '管理员登录' }
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // 尝试恢复认证状态
      try {
        await authStore.initAuth()
        if (authStore.isAuthenticated) {
          // 检查管理员权限
          if (to.meta.requiresAdmin) {
            if (!authStore.user?.is_superuser && !authStore.user?.is_staff) {
              next('/dashboard')
              return
            }
          }
          next()
        } else {
          next('/login')
        }
      } catch {
        next('/login')
      }
    } else {
      // 检查管理员权限
      if (to.meta.requiresAdmin) {
        if (!authStore.user?.is_superuser && !authStore.user?.is_staff) {
          next('/dashboard')
          return
        }
      }
      next()
    }
  }
  // 如果是访客页面且已登录
  else if (to.meta.guest && authStore.isAuthenticated) {
    next('/dashboard')
  }
  // 其他情况直接通过
  else {
    next()
  }
})

export default router
