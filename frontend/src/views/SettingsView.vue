<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import HealthBadge from '@/components/HealthBadge.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { useAuthStore } from '@/stores/auth'
import { ojApi } from '@/api/oj'
import { settingsApi } from '@/api/settings'
import { getApiErrorMessage } from '@/api/client'
import { resendVerification } from '@/api/auth'
import type { AuthSession } from '@/api/auth'
import type { OJAccount } from '@/types/oj'
import type { UserPreferences } from '@/types/settings'

const auth = useAuthStore()
const router = useRouter()

const platformLabels: Record<string, string> = {
  codeforces: 'Codeforces',
  luogu: '洛谷',
  atcoder: 'AtCoder',
  other: '其他',
}

const accounts = ref<OJAccount[]>([])
const accountsLoading = ref(true)
const accountError = ref<string | null>(null)
const accountSaving = ref(false)
const syncingAccountId = ref<string | null>(null)
const syncMessage = ref<string | null>(null)
const platform = ref('codeforces')
const handle = ref('')
const displayName = ref('')

const preferences = ref<UserPreferences | null>(null)
const prefsLoading = ref(true)
const prefsSaving = ref(false)
const prefsError = ref<string | null>(null)
const prefsSaved = ref(false)
const timezone = ref('UTC')
const dailyLimit = ref(50)
const desiredRetention = ref(0.9)

const profileName = ref('')
const profileSaving = ref(false)
const profileMessage = ref<string | null>(null)
const profileError = ref<string | null>(null)
const verificationSending = ref(false)
const verificationMessage = ref<string | null>(null)
const verificationError = ref<string | null>(null)

const deleteOpen = ref(false)
const deletePassword = ref('')
const deleteConfirmation = ref('')
const deleteSaving = ref(false)
const deleteError = ref<string | null>(null)

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordSaving = ref(false)
const passwordError = ref<string | null>(null)
const passwordMessage = ref<string | null>(null)
const securityError = ref<string | null>(null)
const securityMessage = ref<string | null>(null)
const sessionActionId = ref<string | null>(null)

async function loadAccounts(): Promise<void> {
  accountsLoading.value = true
  accountError.value = null
  try {
    accounts.value = await ojApi.accounts()
  } catch (err) {
    accountError.value = getApiErrorMessage(err)
  } finally {
    accountsLoading.value = false
  }
}

async function loadPreferences(): Promise<void> {
  prefsLoading.value = true
  prefsError.value = null
  try {
    const data = await settingsApi.getPreferences()
    preferences.value = data
    timezone.value = data.timezone
    dailyLimit.value = data.daily_review_limit
    desiredRetention.value = Number(data.desired_retention.toFixed(2))
    profileName.value = auth.user?.displayName ?? ''
  } catch (err) {
    prefsError.value = getApiErrorMessage(err)
  } finally {
    prefsLoading.value = false
  }
}

async function savePreferences(): Promise<void> {
  prefsSaving.value = true
  prefsError.value = null
  prefsSaved.value = false
  try {
    const updated = await settingsApi.updatePreferences({
      timezone: timezone.value.trim(),
      daily_review_limit: dailyLimit.value,
      desired_retention: desiredRetention.value,
    })
    preferences.value = updated
    prefsSaved.value = true
  } catch (err) {
    prefsError.value = getApiErrorMessage(err)
  } finally {
    prefsSaving.value = false
  }
}

function exportData(): void {
  window.location.href = '/api/v1/settings/export'
}

async function saveProfile(): Promise<void> {
  profileSaving.value = true
  profileError.value = null
  profileMessage.value = null
  try {
    await settingsApi.updateProfile({
      display_name: profileName.value.trim() || undefined,
    })
    await auth.fetchMe()
    profileMessage.value = '显示名已保存。'
  } catch (err) {
    profileError.value = getApiErrorMessage(err)
  } finally {
    profileSaving.value = false
  }
}

async function resendEmailVerification(): Promise<void> {
  verificationSending.value = true
  verificationError.value = null
  verificationMessage.value = null
  try {
    await resendVerification()
    verificationMessage.value =
      '验证邮件已发送。开发环境请查看后端日志中的验证链接。'
  } catch (err) {
    verificationError.value = getApiErrorMessage(err)
  } finally {
    verificationSending.value = false
  }
}

async function deleteAccountNow(): Promise<void> {
  deleteError.value = null
  if (deleteConfirmation.value !== 'DELETE') {
    deleteError.value = '请输入 DELETE 确认。'
    return
  }
  if (!deletePassword.value) {
    deleteError.value = '请输入账号密码。'
    return
  }
  deleteSaving.value = true
  try {
    await auth.deleteAccount(deletePassword.value)
    await router.push('/login')
  } catch (err) {
    deleteError.value = getApiErrorMessage(err)
  } finally {
    deleteSaving.value = false
  }
}

async function submitPasswordChange(): Promise<void> {
  passwordError.value = null
  passwordMessage.value = null
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = '两次输入的新密码不一致。'
    return
  }
  if (newPassword.value.length < 8) {
    passwordError.value = '新密码至少 8 位。'
    return
  }

  passwordSaving.value = true
  try {
    await auth.changePassword(currentPassword.value, newPassword.value)
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    passwordMessage.value = '密码已更新，其他设备已退出登录。'
  } catch (err) {
    passwordError.value = getApiErrorMessage(err)
  } finally {
    passwordSaving.value = false
  }
}

function formatSessionDate(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function revokeOneSession(session: AuthSession): Promise<void> {
  if (!window.confirm('确定撤销该设备会话？')) return
  securityError.value = null
  securityMessage.value = null
  sessionActionId.value = session.id
  try {
    await auth.revokeSession(session.id)
    if (session.is_current) {
      await router.push('/login')
    } else {
      securityMessage.value = '该设备已退出登录。'
    }
  } catch (err) {
    securityError.value = getApiErrorMessage(err)
  } finally {
    sessionActionId.value = null
  }
}

async function logoutEverywhere(): Promise<void> {
  if (!window.confirm('确定退出所有设备？当前会话也会失效。')) return
  securityError.value = null
  try {
    await auth.logoutAll()
    await router.push('/login')
  } catch (err) {
    securityError.value = getApiErrorMessage(err)
  }
}

async function addAccount(): Promise<void> {
  accountError.value = null
  if (!handle.value.trim()) {
    accountError.value = '请输入 OJ 账号标识。'
    return
  }
  accountSaving.value = true
  try {
    const account = await ojApi.createAccount({
      platform: platform.value,
      handle: handle.value.trim(),
      display_name: displayName.value.trim() || undefined,
    })
    accounts.value = [...accounts.value, account]
    handle.value = ''
    displayName.value = ''
  } catch (err) {
    accountError.value = getApiErrorMessage(err)
  } finally {
    accountSaving.value = false
  }
}

async function removeAccount(account: OJAccount): Promise<void> {
  if (
    !window.confirm(
      `移除 ${platformLabels[account.platform] ?? account.platform} 账号 ${account.handle}？`,
    )
  ) {
    return
  }
  accountError.value = null
  try {
    await ojApi.deleteAccount(account.id)
    accounts.value = accounts.value.filter((item) => item.id !== account.id)
  } catch (err) {
    accountError.value = getApiErrorMessage(err)
  }
}

async function syncAccount(account: OJAccount): Promise<void> {
  syncingAccountId.value = account.id
  syncMessage.value = null
  accountError.value = null
  try {
    const result = await ojApi.syncAccount(account.id)
    syncMessage.value = `同步完成：拉取 ${result.fetched} 条，新增 ${result.created} 条，跳过 ${result.skipped} 条。`
    await loadAccounts()
  } catch (err) {
    accountError.value = getApiErrorMessage(err)
  } finally {
    syncingAccountId.value = null
  }
}

onMounted(() => {
  void loadAccounts()
  void loadPreferences()
  void auth.loadSessions()
})
</script>

<template>
  <PageHeader
    title="设置"
    description="账号、复习偏好、OJ 关联与外观设置。"
  />

  <div class="grid grid-2">
    <section class="card">
      <h2>当前账号</h2>
      <div class="form-stack" style="margin-top: 16px">
        <div class="field">
          <label for="account-email">邮箱</label>
          <input id="account-email" :value="auth.user?.email ?? '—'" readonly />
        </div>
        <div class="field">
          <label for="account-name">显示名</label>
          <input id="account-name" v-model="profileName" type="text" maxlength="80" />
        </div>
        <div class="topbar-actions" style="flex-wrap: wrap">
          <span class="badge" :class="auth.user?.emailVerifiedAt ? 'badge-success' : 'badge-warning'">
            {{ auth.user?.emailVerifiedAt ? '邮箱已验证' : '邮箱未验证' }}
          </span>
          <button
            v-if="!auth.user?.emailVerifiedAt"
            class="btn btn-ghost"
            type="button"
            :disabled="verificationSending"
            @click="resendEmailVerification"
          >
            {{ verificationSending ? '发送中…' : '重新发送验证邮件' }}
          </button>
        </div>
        <div
          v-if="verificationError"
          class="notice"
          role="alert"
          style="border-color: var(--danger); color: var(--danger)"
        >
          {{ verificationError }}
        </div>
        <div v-if="verificationMessage" class="notice notice-accent">
          {{ verificationMessage }}
        </div>
        <div
          v-if="profileError"
          class="notice"
          role="alert"
          style="border-color: var(--danger); color: var(--danger)"
        >
          {{ profileError }}
        </div>
        <div v-if="profileMessage" class="notice notice-accent">
          {{ profileMessage }}
        </div>
        <div class="topbar-actions">
          <button
            class="btn btn-primary"
            type="button"
            :disabled="profileSaving"
            @click="saveProfile"
          >
            {{ profileSaving ? '保存中…' : '保存显示名' }}
          </button>
          <button class="btn btn-ghost" type="button" @click="exportData">
            导出我的数据
          </button>
          <small style="color: var(--text-subtle)">
            导出 JSON 包含训练、复习、OJ 与统计数据，不包含密码/令牌。
          </small>
        </div>
      </div>
    </section>

    <section class="card">
      <h2>外观</h2>
      <p style="color: var(--text-muted); margin-top: 4px">
        深色、浅色或跟随系统。主题会保存在本地。
      </p>
      <div style="margin-top: 16px">
        <ThemeToggle />
      </div>
    </section>

    <section class="card">
      <h2>API 状态</h2>
      <p style="color: var(--text-muted); margin-top: 4px">
        前端通过 Vite 代理访问 FastAPI。
      </p>
      <div style="margin-top: 16px">
        <HealthBadge />
      </div>
    </section>

    <section class="card">
      <h2>复习偏好</h2>
      <div v-if="prefsLoading" class="notice" style="margin-top: 12px">
        正在加载复习偏好…
      </div>
      <form v-else class="form-stack" style="margin-top: 16px" @submit.prevent="savePreferences">
        <div class="field">
          <label for="timezone">时区（IANA）</label>
          <input
            id="timezone"
            v-model="timezone"
            type="text"
            list="timezone-options"
            placeholder="UTC"
            maxlength="64"
          />
          <datalist id="timezone-options">
            <option value="UTC" />
            <option value="Asia/Shanghai" />
            <option value="Asia/Tokyo" />
            <option value="Asia/Singapore" />
            <option value="Europe/London" />
            <option value="America/New_York" />
          </datalist>
          <small>影响今日复习边界与到期队列。</small>
        </div>
        <div class="field">
          <label for="daily-limit">每日复习上限</label>
          <input
            id="daily-limit"
            v-model.number="dailyLimit"
            type="number"
            min="1"
            max="500"
          />
          <small>默认 50；超出部分留待后续日期。</small>
        </div>
        <div class="field">
          <label for="desired-retention">目标保留率</label>
          <input
            id="desired-retention"
            v-model.number="desiredRetention"
            type="number"
            min="0.7"
            max="0.99"
            step="0.01"
          />
          <small>越高复习越频繁；这是 FSRS 参数，不是能力分数。</small>
        </div>
        <div
          v-if="prefsError"
          class="notice"
          role="alert"
          style="border-color: var(--danger); color: var(--danger)"
        >
          {{ prefsError }}
        </div>
        <div v-if="prefsSaved" class="notice notice-accent">复习偏好已保存。</div>
        <button class="btn btn-primary" type="submit" :disabled="prefsSaving">
          {{ prefsSaving ? '保存中…' : '保存复习偏好' }}
        </button>
      </form>
    </section>

    <section class="card" style="grid-column: 1 / -1">
      <h2>安全</h2>
      <p style="color: var(--text-muted); margin-top: 4px">
        修改密码会撤销其他设备；当前设备保持登录。会话列表不展示令牌或 IP 哈希。
      </p>

      <div class="grid grid-2" style="margin-top: 16px">
        <form class="form-stack" @submit.prevent="submitPasswordChange">
          <h3>修改密码</h3>
          <div class="field">
            <label for="current-password">当前密码</label>
            <input
              id="current-password"
              v-model="currentPassword"
              type="password"
              autocomplete="current-password"
              required
            />
          </div>
          <div class="field">
            <label for="new-password">新密码</label>
            <input
              id="new-password"
              v-model="newPassword"
              type="password"
              autocomplete="new-password"
              minlength="8"
              required
            />
          </div>
          <div class="field">
            <label for="confirm-password">确认新密码</label>
            <input
              id="confirm-password"
              v-model="confirmPassword"
              type="password"
              autocomplete="new-password"
              minlength="8"
              required
            />
          </div>
          <div
            v-if="passwordError"
            class="notice"
            role="alert"
            style="border-color: var(--danger); color: var(--danger)"
          >
            {{ passwordError }}
          </div>
          <div v-if="passwordMessage" class="notice notice-accent">
            {{ passwordMessage }}
          </div>
          <button class="btn btn-primary" type="submit" :disabled="passwordSaving">
            {{ passwordSaving ? '更新中…' : '更新密码' }}
          </button>
        </form>

        <div>
          <div class="topbar-actions" style="justify-content: space-between">
            <h3>活跃会话</h3>
            <button class="btn btn-ghost" type="button" @click="logoutEverywhere">
              退出所有设备
            </button>
          </div>

          <div v-if="auth.sessionsLoading" class="notice" style="margin-top: 12px">
            正在加载会话…
          </div>
          <div v-else-if="auth.sessions.length" class="grid" style="margin-top: 12px">
            <article
              v-for="session in auth.sessions"
              :key="session.id"
              class="card card-muted"
            >
              <div class="topbar-actions" style="justify-content: space-between">
                <span style="overflow-wrap: anywhere">
                  {{ session.user_agent ?? '未知设备' }}
                  <span v-if="session.is_current" class="badge">当前</span>
                </span>
                <button
                  class="btn btn-ghost"
                  type="button"
                  :disabled="sessionActionId === session.id"
                  @click="revokeOneSession(session)"
                >
                  撤销
                </button>
              </div>
              <p style="color: var(--text-subtle); margin-top: 6px; font-size: 12px">
                登录 {{ formatSessionDate(session.created_at) }} · 最近
                {{ formatSessionDate(session.last_used_at) }} · 到期
                {{ formatSessionDate(session.expires_at) }}
              </p>
            </article>
          </div>
          <p v-else style="color: var(--text-muted); margin-top: 12px">
            暂无活跃会话。
          </p>

          <div
            v-if="securityError"
            class="notice"
            role="alert"
            style="border-color: var(--danger); color: var(--danger); margin-top: 12px"
          >
            {{ securityError }}
          </div>
          <div v-if="securityMessage" class="notice notice-accent" style="margin-top: 12px">
            {{ securityMessage }}
          </div>
        </div>
      </div>
    </section>

    <section class="card danger-zone" style="grid-column: 1 / -1">
      <div class="section-heading">
        <div>
          <span class="eyebrow">危险区域</span>
          <h2>删除账号</h2>
        </div>
        <button
          class="btn btn-ghost"
          type="button"
          @click="deleteOpen = !deleteOpen"
        >
          {{ deleteOpen ? '取消' : '删除账号' }}
        </button>
      </div>
      <p style="color: var(--text-muted); margin-top: 4px">
        永久删除账号，以及训练会话、复习记录、OJ 关联、统计数据与登录会话。此操作不可恢复。
      </p>

      <form
        v-if="deleteOpen"
        class="form-stack"
        style="margin-top: 16px"
        @submit.prevent="deleteAccountNow"
      >
        <div class="grid grid-2">
          <div class="field">
            <label for="delete-account-password">账号密码</label>
            <input
              id="delete-account-password"
              v-model="deletePassword"
              type="password"
              autocomplete="current-password"
              required
            />
          </div>
          <div class="field">
            <label for="delete-account-confirm">输入 DELETE 确认</label>
            <input
              id="delete-account-confirm"
              v-model="deleteConfirmation"
              type="text"
              placeholder="DELETE"
              autocomplete="off"
              required
            />
          </div>
        </div>

        <div
          v-if="deleteError"
          class="notice"
          role="alert"
          style="border-color: var(--danger); color: var(--danger)"
        >
          {{ deleteError }}
        </div>

        <button class="btn btn-danger" type="submit" :disabled="deleteSaving">
          {{ deleteSaving ? '删除中…' : '永久删除账号' }}
        </button>
      </form>
    </section>

    <section class="card" style="grid-column: 1 / -1">
      <h2>OJ 账号</h2>
      <p style="color: var(--text-muted); margin-top: 4px">
        当前版本支持手动关联提交与 Codeforces 手动同步；不保存 OJ 密码，同步失败不影响已有训练数据。
      </p>

      <div
        v-if="accountError"
        class="notice"
        role="alert"
        style="border-color: var(--danger); color: var(--danger); margin-top: 12px"
      >
        {{ accountError }}
      </div>
      <div v-if="syncMessage" class="notice notice-accent" style="margin-top: 12px">
        {{ syncMessage }}
      </div>

      <div v-if="accountsLoading" class="notice" style="margin-top: 12px">
        正在加载 OJ 账号…
      </div>
      <div v-else-if="accounts.length" class="grid" style="margin-top: 12px">
        <div
          v-for="account in accounts"
          :key="account.id"
          class="topbar-actions"
          style="justify-content: space-between; flex-wrap: wrap"
        >
          <span>
            <strong>{{ platformLabels[account.platform] ?? account.platform }}</strong>
            <span style="color: var(--text-muted)"> · {{ account.handle }}</span>
            <span v-if="account.display_name" style="color: var(--text-muted)">
              （{{ account.display_name }}）
            </span>
            <span
              v-if="account.last_synced_at"
              style="color: var(--text-subtle); display: block; font-size: 12px"
            >
              最近同步：{{ formatSessionDate(account.last_synced_at) }}
            </span>
          </span>
          <span class="topbar-actions">
            <button
              v-if="account.platform === 'codeforces'"
              class="btn btn-ghost"
              type="button"
              :disabled="syncingAccountId === account.id"
              @click="syncAccount(account)"
            >
              {{ syncingAccountId === account.id ? '同步中…' : '同步' }}
            </button>
            <button class="btn btn-ghost" type="button" @click="removeAccount(account)">
              移除
            </button>
          </span>
        </div>
      </div>
      <p v-else style="color: var(--text-muted); margin-top: 12px">
        尚未关联 OJ 账号。
      </p>

      <form class="form-stack" style="margin-top: 16px" @submit.prevent="addAccount">
        <div class="grid grid-2">
          <div class="field">
            <label for="oj-platform">平台</label>
            <select id="oj-platform" v-model="platform">
              <option value="codeforces">Codeforces</option>
              <option value="luogu">洛谷</option>
              <option value="atcoder">AtCoder</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div class="field">
            <label for="oj-handle">账号标识</label>
            <input
              id="oj-handle"
              v-model="handle"
              type="text"
              placeholder="例如 tourist"
              maxlength="120"
            />
          </div>
        </div>
        <div class="field">
          <label for="oj-display-name">显示名（可选）</label>
          <input
            id="oj-display-name"
            v-model="displayName"
            type="text"
            maxlength="120"
          />
        </div>
        <button class="btn btn-primary" type="submit" :disabled="accountSaving">
          {{ accountSaving ? '保存中…' : '添加 OJ 账号' }}
        </button>
      </form>
    </section>
  </div>
</template>
