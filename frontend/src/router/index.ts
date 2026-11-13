import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '@/layouts/AppShell.vue'
import FocusShell from '@/layouts/FocusShell.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { title: '创建账号' },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('@/views/ForgotPasswordView.vue'),
      meta: { title: '找回密码' },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: () => import('@/views/ResetPasswordView.vue'),
      meta: { title: '重置密码' },
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: () => import('@/views/VerifyEmailView.vue'),
      meta: { title: '验证邮箱' },
    },
    {
      path: '/',
      component: AppShell,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: '仪表盘', requiresAuth: true },
        },
        {
          path: 'library',
          name: 'library',
          component: () => import('@/views/LibraryView.vue'),
          meta: { title: '算法库', requiresAuth: true },
        },
        {
          path: 'library/algorithms/:algorithmSlug',
          name: 'algorithm',
          component: () => import('@/views/AlgorithmView.vue'),
          meta: { title: '算法详情', requiresAuth: true },
        },
        {
          path: 'library/skills/:skillSlug',
          name: 'skill',
          component: () => import('@/views/SkillView.vue'),
          meta: { title: '技能详情', requiresAuth: true },
        },
        {
          path: 'review',
          name: 'review',
          component: () => import('@/views/ReviewView.vue'),
          meta: { title: '智能复习', requiresAuth: true },
        },
        {
          path: 'practice',
          name: 'practice',
          component: () => import('@/views/PracticeView.vue'),
          meta: { title: '自由练习', requiresAuth: true },
        },
        {
          path: 'practice/user-tasks',
          name: 'user-tasks',
          component: () => import('@/views/UserTasksView.vue'),
          meta: { title: '我的题目', requiresAuth: true },
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('@/views/AnalyticsView.vue'),
          meta: { title: '分析', requiresAuth: true },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
          meta: { title: '设置', requiresAuth: true },
        },
      ],
    },
    {
      path: '/practice/sessions/:sessionId',
      component: FocusShell,
      children: [
        {
          path: '',
          name: 'workspace',
          component: () => import('@/views/WorkspaceView.vue'),
          meta: { title: '训练工作区', requiresAuth: true },
        },
        {
          path: 'result',
          name: 'result',
          component: () => import('@/views/ResultView.vue'),
          meta: { title: '训练结果', requiresAuth: true },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
      meta: { title: '页面不存在' },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  const shouldProbeSession =
    to.meta.requiresAuth || to.name === 'login' || to.name === 'register'
  if (!auth.initialized && shouldProbeSession) {
    await auth.fetchMe()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if ((to.name === 'login' || to.name === 'register') && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
