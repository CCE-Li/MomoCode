<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import GalaxyPullDown from '@/components/GalaxyPullDown.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { settingsApi } from '@/api/settings'
import { useTheme } from '@/composables/useTheme'

interface NavItem {
  label: string
  to: string
  hint: string
}

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { mode: themeMode, setTheme } = useTheme()
const isNavOpen = ref(false)
const isLoggingOut = ref(false)
const galaxyOpen = ref(false)

onMounted(async () => {
  if (!auth.isAuthenticated) return
  try {
    const preferences = await settingsApi.getPreferences()
    if (
      preferences.theme === 'dark' ||
      preferences.theme === 'light' ||
      preferences.theme === 'system'
    ) {
      setTheme(preferences.theme)
    }
  } catch {
    // Theme sync is best-effort; local theme remains available.
  }
})

watch(themeMode, async (value) => {
  if (!auth.isAuthenticated) return
  try {
    await settingsApi.updatePreferences({ theme: value })
  } catch {
    // Theme sync is best-effort.
  }
})

const navItems: NavItem[] = [
  { label: '仪表盘', to: '/', hint: '今日状态与主操作' },
  { label: '算法库', to: '/library', hint: '浏览算法与技能' },
  { label: '智能复习', to: '/review', hint: '到期复习队列' },
  { label: '自由练习', to: '/practice', hint: '自选任务练习' },
  { label: '我的题目', to: '/practice/user-tasks', hint: '添加自己的 OJ 题与训练题' },
  { label: '分析', to: '/analytics', hint: '训练表现分析' },
  { label: '设置', to: '/settings', hint: '账号与偏好' },
]

const pageTitle = computed(() => {
  const title = route.meta.title
  return typeof title === 'string' ? title : 'MomoCode'
})

const userInitial = computed(() => {
  const name = auth.user?.displayName ?? auth.user?.email ?? 'M'
  return name.slice(0, 1).toUpperCase()
})

function closeNav(): void {
  isNavOpen.value = false
}

async function handleLogout(): Promise<void> {
  isLoggingOut.value = true
  try {
    await auth.logout()
    await router.push({ name: 'login' })
  } catch {
    // auth.error already carries a user-facing message.
  } finally {
    isLoggingOut.value = false
  }
}
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>

  <div class="app-shell">
    <div
      v-if="isNavOpen"
      class="sidebar-backdrop"
      aria-hidden="true"
      @click="closeNav"
    ></div>

    <aside class="sidebar" :class="{ 'is-open': isNavOpen }">
      <RouterLink class="brand" to="/" @click="closeNav">
        <BrandMark />
        <span>MomoCode</span>
      </RouterLink>

      <nav class="nav" aria-label="主导航">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          class="nav-link"
          :to="item.to"
          :title="item.hint"
          @click="closeNav"
        >
          <span class="nav-dot" aria-hidden="true"></span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div v-if="auth.error" class="notice" role="alert">
        {{ auth.error }}
      </div>

      <div class="sidebar-footer">
        <div>算法训练系统</div>
        <div>v0.1.0 · 夜间构建</div>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="topbar-actions">
          <button
            class="btn btn-ghost mobile-menu-button"
            type="button"
            aria-label="打开导航"
            :aria-expanded="isNavOpen"
            @click="isNavOpen = !isNavOpen"
          >
            菜单
          </button>
          <span class="topbar-title">{{ pageTitle }}</span>
        </div>

        <div class="topbar-actions">
          <button
            v-if="auth.isAuthenticated"
            class="btn btn-ghost galaxy-entry"
            type="button"
            aria-label="星图"
            title="星图"
            :aria-expanded="galaxyOpen"
            :aria-controls="galaxyOpen ? 'galaxy-pull-panel' : undefined"
            @click="galaxyOpen = !galaxyOpen"
          >
            <span class="galaxy-entry-icon" aria-hidden="true">✦</span>
          </button>

          <ThemeToggle />

          <template v-if="auth.isAuthenticated">
            <span class="user-chip" :title="auth.user?.email">
              <span class="user-avatar" aria-hidden="true">{{ userInitial }}</span>
              <span class="user-name">{{ auth.user?.displayName }}</span>
            </span>
            <button
              class="btn btn-ghost"
              type="button"
              :disabled="isLoggingOut"
              @click="handleLogout"
            >
              {{ isLoggingOut ? '退出中…' : '退出' }}
            </button>
          </template>
          <RouterLink v-else class="btn btn-ghost" to="/login">登录</RouterLink>
        </div>
      </header>

      <main id="main-content" class="content">
        <div
          v-if="auth.user && !auth.user.emailVerifiedAt"
          class="notice notice-accent"
          style="margin-bottom: 16px"
        >
          邮箱尚未验证。请到
          <RouterLink to="/settings">设置</RouterLink>
          重新发送验证邮件。
        </div>
        <RouterView />
      </main>
    </div>

    <GalaxyPullDown v-model:open="galaxyOpen" />
  </div>
</template>

<style scoped>
.galaxy-entry-icon {
  color: var(--accent);
  font-size: 12px;
  line-height: 1;
}
</style>
