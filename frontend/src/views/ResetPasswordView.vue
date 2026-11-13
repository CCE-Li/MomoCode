<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import { resetPassword } from '@/api/auth'
import { getApiErrorMessage } from '@/api/client'

const route = useRoute()
const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : ''))
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const success = ref(false)
const error = ref<string | null>(null)

async function submit(): Promise<void> {
  error.value = null
  if (!token.value) {
    error.value = '重置链接缺少 token。'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = '两次输入的新密码不一致。'
    return
  }
  if (newPassword.value.length < 8) {
    error.value = '新密码至少 8 位。'
    return
  }
  loading.value = true
  try {
    await resetPassword(token.value, newPassword.value)
    success.value = true
    newPassword.value = ''
    confirmPassword.value = ''
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

      <h1>设置新密码</h1>
      <p>重置后所有设备会退出登录，请使用新密码重新登录。</p>

      <form v-if="!success" class="form-stack" @submit.prevent="submit">
        <div class="field">
          <label for="reset-password">新密码</label>
          <input
            id="reset-password"
            v-model="newPassword"
            type="password"
            autocomplete="new-password"
            minlength="8"
            required
          />
        </div>
        <div class="field">
          <label for="reset-confirm">确认新密码</label>
          <input
            id="reset-confirm"
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            minlength="8"
            required
          />
        </div>

        <div v-if="error" class="notice" role="alert" style="border-color: var(--danger); color: var(--danger)">
          {{ error }}
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="loading">
            {{ loading ? '保存中…' : '保存新密码' }}
          </button>
        </div>
      </form>

      <div v-else class="notice notice-accent" role="status">
        密码已重置，所有设备已退出登录。
      </div>

      <div class="form-actions" style="margin-top: 20px">
        <RouterLink class="btn btn-primary" to="/login">去登录</RouterLink>
      </div>
    </section>
  </main>
</template>
