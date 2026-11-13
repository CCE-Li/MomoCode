<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import { practiceApi } from '@/api/practice'
import { ojApi } from '@/api/oj'
import { getApiErrorMessage } from '@/api/client'
import type { PracticeResult } from '@/types/practice'
import type { ManualSubmissionPayload, OJPlatform, OJVerdict, Submission } from '@/types/oj'

const route = useRoute()
const router = useRouter()
const sessionId = computed(() => String(route.params.sessionId ?? ''))
const result = ref<PracticeResult | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const startingAgain = ref(false)

const submissions = ref<Submission[]>([])
const submissionsLoading = ref(true)
const ojError = ref<string | null>(null)
const ojSaving = ref(false)
const ojFormOpen = ref(false)
const ojDuplicateMessage = ref<string | null>(null)
const ojPlatform = ref<OJPlatform>('codeforces')
const ojExternalId = ref('')
const ojProblemUrl = ref('')
const ojVerdict = ref<OJVerdict | ''>('accepted')
const ojLanguage = ref('C++17')
const ojTimeMs = ref<number | ''>('')
const ojMemoryKb = ref<number | ''>('')

const platformLabels: Record<string, string> = {
  codeforces: 'Codeforces',
  luogu: '洛谷',
  atcoder: 'AtCoder',
  other: '其他',
}

const verdictLabels: Record<string, string> = {
  accepted: '通过',
  wrong_answer: '答案错误',
  time_limit_exceeded: '超时',
  memory_limit_exceeded: '内存超限',
  runtime_error: '运行错误',
  compilation_error: '编译错误',
  partially_accepted: '部分通过',
  other: '其他',
  unknown: '未填写',
}

const trainingTypeLabels: Record<string, string> = {
  recognition: '识别',
  template: '模板复现',
  variant: '变体复现',
  correction: '针对性纠错',
}

const grade = computed(() => {
  if (!result.value) return 'unknown'
  return result.value.auto_grade?.result ?? result.value.self_assessment ?? 'unknown'
})

const gradeLabel = computed(() => {
  if (grade.value === 'correct') return '正确'
  if (grade.value === 'partial') return '部分正确'
  if (grade.value === 'incorrect') return '错误'
  if (grade.value === 'compile_error') return '编译错误'
  if (grade.value === 'runtime_error') return '运行错误'
  if (grade.value === 'time_limit_exceeded') return '运行超时'
  if (grade.value === 'ungraded') return '未判题'
  return '已提交'
})

const gradeClass = computed(() => {
  if (grade.value === 'correct') return 'badge-success'
  if (grade.value === 'partial') return 'badge-warning'
  if (
    grade.value === 'incorrect' ||
    grade.value === 'compile_error' ||
    grade.value === 'runtime_error' ||
    grade.value === 'time_limit_exceeded'
  ) {
    return 'badge-danger'
  }
  if (grade.value === 'ungraded') return 'badge-warning'
  return ''
})

const judgeCases = computed(() => result.value?.auto_grade?.cases ?? [])

const timeSpent = computed(() => {
  const ms = result.value?.time_spent_ms
  if (ms === null || ms === undefined) return '—'
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${minutes} 分 ${seconds} 秒`
})

const targetSkill = computed(() => result.value?.task.target_skills[0] ?? null)

function formatReviewDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    result.value = await practiceApi.getResult(sessionId.value)
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function startAgain(): Promise<void> {
  if (!result.value) return
  startingAgain.value = true
  try {
    const session = await practiceApi.createSession(result.value.task.id, 'free')
    await router.push(`/practice/sessions/${session.id}`)
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    startingAgain.value = false
  }
}

async function loadSubmissions(): Promise<void> {
  submissionsLoading.value = true
  ojError.value = null
  try {
    submissions.value = await ojApi.sessionSubmissions(sessionId.value)
  } catch (err) {
    ojError.value = getApiErrorMessage(err)
  } finally {
    submissionsLoading.value = false
  }
}

async function submitOj(): Promise<void> {
  ojError.value = null
  ojDuplicateMessage.value = null
  if (!ojExternalId.value.trim()) {
    ojError.value = '请输入 OJ 提交 ID。'
    return
  }

  ojSaving.value = true
  try {
    const payload: ManualSubmissionPayload = {
      platform: ojPlatform.value,
      external_id: ojExternalId.value.trim(),
      problem_url: ojProblemUrl.value.trim() || undefined,
      verdict: ojVerdict.value || undefined,
      language: ojLanguage.value.trim() || undefined,
    }
    if (ojTimeMs.value !== '') payload.time_ms = Number(ojTimeMs.value)
    if (ojMemoryKb.value !== '') payload.memory_kb = Number(ojMemoryKb.value)

    const created = await ojApi.createManualSubmission(payload)
    if (created.duplicate) {
      ojDuplicateMessage.value = '该提交已存在，已复用现有记录。'
    }
    await ojApi.linkSubmission(sessionId.value, created.submission.id)
    await loadSubmissions()
    ojExternalId.value = ''
    ojProblemUrl.value = ''
    ojTimeMs.value = ''
    ojMemoryKb.value = ''
  } catch (err) {
    ojError.value = getApiErrorMessage(err)
  } finally {
    ojSaving.value = false
  }
}

onMounted(async () => {
  await load()
  await loadSubmissions()
})
</script>

<template>
  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <template v-else-if="result">
    <div class="page-header">
      <div>
        <h1>{{ result.task.title }}</h1>
        <p style="white-space: pre-wrap">{{ result.task.statement_md }}</p>
      </div>
      <div class="topbar-actions">
        <span class="badge" :class="gradeClass">{{ gradeLabel }}</span>
        <span class="badge">{{ result.mode === 'review' ? '正式复习' : '自由练习' }}</span>
      </div>
    </div>

    <div class="grid grid-2">
      <section class="card">
        <h2>本次证据</h2>
        <div class="topbar-actions" style="margin-top: 12px; flex-wrap: wrap">
          <span class="badge">用时 {{ timeSpent }}</span>
          <span class="badge">最高提示 {{ result.max_hint_level }}</span>
          <span class="badge">
            {{ trainingTypeLabels[result.training_type] ?? result.training_type }}
          </span>
        </div>

        <div
          v-if="result.auto_grade && result.training_type !== 'recognition'"
          style="margin-top: 16px"
        >
          <h3>自动判题</h3>
          <p style="color: var(--text-muted); margin-top: 4px">
            <template v-if="result.auto_grade.total">
              通过 {{ result.auto_grade.passed ?? 0 }} / {{ result.auto_grade.total }} 个测试用例
            </template>
            <template v-else>
              {{ result.auto_grade.message ?? '该任务尚未配置自动判题用例。' }}
            </template>
          </p>

          <pre v-if="result.auto_grade.compile_output" class="code-block">{{
            result.auto_grade.compile_output
          }}</pre>

          <div
            v-for="(item, index) in judgeCases"
            :key="index"
            class="notice"
            style="margin-top: 10px"
          >
            <div style="width: 100%">
              <div class="topbar-actions" style="justify-content: space-between">
                <strong>用例 {{ index + 1 }}</strong>
                <span
                  class="badge"
                  :class="item.status === 'ok' ? 'badge-success' : 'badge-danger'"
                >
                  {{ item.status }}
                </span>
              </div>
              <div class="judge-case-grid">
                <div>
                  <span class="stat-label">输入</span>
                  <pre class="code-block">{{ item.input }}</pre>
                </div>
                <div>
                  <span class="stat-label">期望输出</span>
                  <pre class="code-block">{{ item.expected_output }}</pre>
                </div>
                <div>
                  <span class="stat-label">实际输出</span>
                  <pre class="code-block">{{ item.actual_output || '（无输出）' }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="result.error_types.length" style="margin-top: 16px">
          <h3>错误类型</h3>
          <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
            <span v-for="item in result.error_types" :key="item" class="badge">
              {{ item }}
            </span>
          </div>
        </div>

        <div v-if="result.hints_used.length" style="margin-top: 16px">
          <h3>提示使用</h3>
          <div
            v-for="hint in result.hints_used"
            :key="hint.level"
            class="notice"
            style="margin-top: 8px"
          >
            <div>
              <strong>{{ hint.level }} 级</strong>
              <div style="white-space: pre-wrap">{{ hint.content }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="card">
        <h2>下一步</h2>
        <p style="color: var(--text-muted); margin-top: 8px">
          <template v-if="result.next_review_at">
            下次复习：{{ formatReviewDate(result.next_review_at) }}
          </template>
          <template v-else>本次未更新复习进度</template>
        </p>

        <div
          v-if="result.mode === 'free' && !result.mark_as_review"
          class="notice"
          style="margin-top: 12px"
        >
          本次自由练习未更新复习进度。
        </div>
        <div v-else class="notice notice-accent" style="margin-top: 12px">
          本次结果已标记为正式复习（或属于正式复习会话）。
        </div>

        <div class="topbar-actions" style="margin-top: 16px; flex-wrap: wrap">
          <button
            class="btn btn-primary"
            type="button"
            :disabled="startingAgain"
            @click="startAgain"
          >
            {{ startingAgain ? '创建中…' : '再练一次' }}
          </button>
          <RouterLink class="btn btn-ghost" to="/review">返回复习队列</RouterLink>
          <RouterLink
            v-if="targetSkill"
            class="btn btn-ghost"
            :to="`/library/skills/${targetSkill.slug}`"
          >
            查看技能
          </RouterLink>
          <RouterLink class="btn btn-ghost" to="/practice">自由练习</RouterLink>
        </div>

        <div class="notice" style="margin-top: 16px">
          一次通过不等于掌握；可在下方手动关联 OJ 提交作为证据。
        </div>
      </section>
    </div>

    <section class="card" style="margin-top: 16px">
      <div class="topbar-actions" style="justify-content: space-between">
        <h2>OJ 证据</h2>
        <button class="btn btn-ghost" type="button" @click="ojFormOpen = !ojFormOpen">
          {{ ojFormOpen ? '收起表单' : '手动关联 OJ 提交' }}
        </button>
      </div>

      <div
        v-if="ojError"
        class="notice"
        role="alert"
        style="border-color: var(--danger); color: var(--danger); margin-top: 12px"
      >
        {{ ojError }}
      </div>
      <div v-if="ojDuplicateMessage" class="notice notice-accent" style="margin-top: 12px">
        {{ ojDuplicateMessage }}
      </div>

      <div v-if="submissionsLoading" class="notice" style="margin-top: 12px">正在加载 OJ 提交…</div>
      <div v-else-if="submissions.length" class="grid grid-2" style="margin-top: 12px">
        <article v-for="submission in submissions" :key="submission.id" class="card card-muted">
          <div class="topbar-actions" style="justify-content: space-between">
            <strong>
              {{ platformLabels[submission.platform] ?? submission.platform }}
              · {{ submission.external_id }}
            </strong>
            <span class="badge" :class="{ 'badge-success': submission.verdict === 'accepted' }">
              {{ verdictLabels[submission.verdict ?? 'unknown'] ?? submission.verdict }}
            </span>
          </div>
          <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
            <span class="badge">{{ submission.source === 'manual' ? '手动关联' : 'OJ 同步' }}</span>
            <span v-if="submission.language" class="badge">{{ submission.language }}</span>
            <span v-if="submission.time_ms !== null" class="badge">
              {{ submission.time_ms }} ms
            </span>
            <span v-if="submission.memory_kb !== null" class="badge">
              {{ submission.memory_kb }} KB
            </span>
          </div>
          <a
            v-if="submission.problem_url"
            :href="submission.problem_url"
            target="_blank"
            rel="noopener noreferrer"
            style="display: inline-block; margin-top: 8px"
          >
            查看题目
          </a>
        </article>
      </div>
      <p v-else style="color: var(--text-muted); margin-top: 12px">尚未关联 OJ 提交。</p>

      <form
        v-if="ojFormOpen"
        class="form-stack"
        style="margin-top: 16px"
        @submit.prevent="submitOj"
      >
        <div class="grid grid-2">
          <div class="field">
            <label for="result-oj-platform">平台</label>
            <select id="result-oj-platform" v-model="ojPlatform">
              <option value="codeforces">Codeforces</option>
              <option value="luogu">洛谷</option>
              <option value="atcoder">AtCoder</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div class="field">
            <label for="result-oj-id">提交 ID</label>
            <input
              id="result-oj-id"
              v-model="ojExternalId"
              type="text"
              placeholder="例如 123456"
              maxlength="200"
              required
            />
          </div>
        </div>

        <div class="grid grid-2">
          <div class="field">
            <label for="result-oj-url">题目链接（可选）</label>
            <input
              id="result-oj-url"
              v-model="ojProblemUrl"
              type="url"
              placeholder="https://codeforces.com/problemset/problem/..."
            />
          </div>
          <div class="field">
            <label for="result-oj-verdict">评测结果</label>
            <select id="result-oj-verdict" v-model="ojVerdict">
              <option value="">未填写</option>
              <option value="accepted">通过</option>
              <option value="wrong_answer">答案错误</option>
              <option value="time_limit_exceeded">超时</option>
              <option value="memory_limit_exceeded">内存超限</option>
              <option value="runtime_error">运行错误</option>
              <option value="compilation_error">编译错误</option>
              <option value="partially_accepted">部分通过</option>
              <option value="other">其他</option>
            </select>
          </div>
        </div>

        <div class="grid grid-3">
          <div class="field">
            <label for="result-oj-language">语言（可选）</label>
            <input id="result-oj-language" v-model="ojLanguage" type="text" maxlength="64" />
          </div>
          <div class="field">
            <label for="result-oj-time">耗时 ms（可选）</label>
            <input id="result-oj-time" v-model.number="ojTimeMs" type="number" min="0" />
          </div>
          <div class="field">
            <label for="result-oj-memory">内存 KB（可选）</label>
            <input id="result-oj-memory" v-model.number="ojMemoryKb" type="number" min="0" />
          </div>
        </div>

        <button class="btn btn-primary" type="submit" :disabled="ojSaving">
          {{ ojSaving ? '关联中…' : '关联到本次训练' }}
        </button>
      </form>
    </section>

    <section v-if="result.reference_solution_md" class="card" style="margin-top: 16px">
      <h2>参考实现</h2>
      <p style="color: var(--text-muted); margin-top: 4px">仅在结果页展示，训练时默认隐藏。</p>
      <pre class="code-block">{{ result.reference_solution_md }}</pre>
    </section>
  </template>
</template>
