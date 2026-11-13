<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import { verifyEmail } from '@/api/auth'
import { getApiErrorMessage } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const status = ref<'loading' | 'success' | 'error'>('loading')
const message = ref('正在验证邮箱…')

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!token) {
    status.value = 'error'
    message.value = '验证链接缺少 token。'
    return
  }
  try {
    await verifyEmail(token)
    status.value = 'success'
    message.value = '邮箱验证成功。'
    if (auth.user) {
      try {
        await auth.fetchMe()
      } catch {
        // 刷新用户信息失败不影响验证结果。
      }
    }
  } catch (err) {
    status.value = 'error'
    message.value = getApiErrorMessage(err)
  }
})
</script>

<template>
  <main class="auth-shell">
    <section class="card auth-card">
      <RouterLink class="brand" to="/" style="padding: 0; margin-bottom: 24px">
        <BrandMark />
        <span>MomoCode</span>
      </RouterLink>

      <h1>邮箱验证</h1>
      <div
        class="notice"
        :class="{ 'notice-accent': status === 'success' }"
        :style="status === 'error' ? 'border-color: var(--danger); color: var(--danger)' : ''"
        role="status"
      >
        {{ message }}
      </div>

      <div class="form-actions" style="margin-top: 20px">
        <RouterLink class="btn btn-primary" to="/">返回仪表盘</RouterLink>
        <RouterLink to="/settings">账号设置</RouterLink>
      </div>
    </section>
  </main>
</template>
