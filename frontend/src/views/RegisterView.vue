<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import BrandMark from '@/components/BrandMark.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const displayName = ref('')
const error = ref<string | null>(null)

async function submit(): Promise<void> {
  error.value = null

  if (!email.value.trim()) {
    error.value = '请输入邮箱。'
    return
  }
  if (password.value.length < 8) {
    error.value = '密码至少需要 8 个字符。'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致。'
    return
  }

  try {
    await auth.register({
      email: email.value.trim(),
      password: password.value,
      displayName: displayName.value.trim() || undefined,
    })
    await router.push('/')
  } catch {
    error.value = auth.error ?? '注册失败，请稍后重试。'
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

      <h1>创建账号</h1>
      <p>当前版本使用邮箱密码；暂不发送验证邮件。</p>

      <form class="form-stack" novalidate @submit.prevent="submit">
        <div class="field">
          <label for="register-email">邮箱</label>
          <input
            id="register-email"
            v-model="email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            required
            autofocus
            :aria-invalid="Boolean(error)"
            aria-describedby="register-error"
          />
        </div>
        <div class="field">
          <label for="register-password">密码</label>
          <input
            id="register-password"
            v-model="password"
            type="password"
            autocomplete="new-password"
            placeholder="至少 8 位"
            required
            :aria-invalid="Boolean(error)"
            aria-describedby="register-error"
          />
        </div>
        <div class="field">
          <label for="register-confirm">确认密码</label>
          <input
            id="register-confirm"
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            placeholder="再次输入密码"
            required
            :aria-invalid="Boolean(error)"
            aria-describedby="register-error"
          />
        </div>
        <div class="field">
          <label for="register-name">显示名（可选）</label>
          <input
            id="register-name"
            v-model="displayName"
            type="text"
            autocomplete="nickname"
            placeholder="怎么称呼你"
            maxlength="80"
          />
        </div>

        <div
          v-if="error"
          id="register-error"
          class="notice"
          role="alert"
          style="border-color: var(--danger); color: var(--danger)"
        >
          {{ error }}
        </div>

        <div class="notice">
          注册成功后会建立会话，并发送验证邮件。开发环境请查看后端日志中的验证链接。
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="auth.loading">
            {{ auth.loading ? '创建中…' : '创建账号' }}
          </button>
          <RouterLink to="/login">已有账号</RouterLink>
        </div>
      </form>
    </section>
  </main>
</template>
