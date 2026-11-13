<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref<string | null>(null)

async function submit(): Promise<void> {
  error.value = null

  if (!email.value.trim() || !password.value) {
    error.value = '请输入邮箱和密码。'
    return
  }

  try {
    await auth.login({
      email: email.value.trim(),
      password: password.value,
    })
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.push(redirect)
  } catch {
    error.value = auth.error ?? '登录失败，请稍后重试。'
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

      <h1>登录</h1>
      <p>保存训练证据、复习状态与技能表现。</p>

      <form class="form-stack" novalidate @submit.prevent="submit">
        <div class="field">
          <label for="login-email">邮箱</label>
          <input
            id="login-email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            required
            autofocus
            :aria-invalid="Boolean(error)"
            aria-describedby="login-error"
          />
        </div>
        <div class="field">
          <label for="login-password">密码</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="至少 8 位"
            required
            :aria-invalid="Boolean(error)"
            aria-describedby="login-error"
          />
        </div>

        <div
          v-if="error"
          id="login-error"
          class="notice"
          role="alert"
          style="border-color: var(--danger); color: var(--danger)"
        >
          {{ error }}
        </div>

        <div class="notice">
          登录状态通过 HttpOnly 会话 Cookie 维护；注册后可验证邮箱。
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="auth.loading">
            {{ auth.loading ? '登录中…' : '登录' }}
          </button>
          <RouterLink to="/forgot-password">忘记密码</RouterLink>
          <RouterLink to="/register">创建账号</RouterLink>
        </div>
      </form>
    </section>
  </main>
</template>
