<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import { requestPasswordReset } from '@/api/auth'
import { getApiErrorMessage } from '@/api/client'

const email = ref('')
const loading = ref(false)
const message = ref<string | null>(null)
const error = ref<string | null>(null)

async function submit(): Promise<void> {
  error.value = null
  message.value = null
  if (!email.value.trim()) {
    error.value = '请输入邮箱。'
    return
  }
  loading.value = true
  try {
    message.value = await requestPasswordReset(email.value.trim())
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="auth-shell">
    <section class="card auth-card">
      <RouterLink class="brand" to="/" style="padding: 0; margin-bottom: 24px">
        <BrandMark />
        <span>MomoCode</span>
      </RouterLink>

      <h1>找回密码</h1>
      <p>输入注册邮箱；如果账号存在，我们会发送重置链接。</p>

      <form class="form-stack" @submit.prevent="submit">
        <div class="field">
          <label for="forgot-email">邮箱</label>
          <input
            id="forgot-email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            required
          />
        </div>

        <div v-if="error" class="notice" role="alert" style="border-color: var(--danger); color: var(--danger)">
          {{ error }}
        </div>
        <div v-if="message" class="notice notice-accent" role="status">
          {{ message }}
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="loading">
            {{ loading ? '发送中…' : '发送重置链接' }}
          </button>
          <RouterLink to="/login">返回登录</RouterLink>
        </div>
      </form>
    </section>
  </main>
</template>
