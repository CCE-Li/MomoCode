<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import HintPanel from '@/components/HintPanel.vue'
import MarkdownText from '@/components/MarkdownText.vue'
import SessionTimer from '@/components/SessionTimer.vue'
import { catalogApi } from '@/api/catalog'
import { practiceApi } from '@/api/practice'
import { getApiErrorMessage } from '@/api/client'
import { useTheme } from '@/composables/useTheme'
import type {
  AiReviewResult,
  PracticeSession,
  RunTestsResult,
  SelfAssessment,
} from '@/types/practice'
import type { SkillSummary } from '@/types/catalog'

const route = useRoute()
const router = useRouter()
const { resolved } = useTheme()

const MonacoEditor = defineAsyncComponent({
  loader: () => import('@/components/MonacoEditor.vue'),
  loadingComponent: LoadingState,
  delay: 200,
})

const sessionId = computed(() => String(route.params.sessionId ?? ''))
const session = ref<PracticeSession | null>(null)
const recognitionSkills = ref<SkillSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const answerError = ref<string | null>(null)
const hintLoading = ref(false)
const submitting = ref(false)

const selectedSkillIds = ref<string[]>([])
const code = ref('')
const errorTypes = ref<string[]>([])
const selfAssessment = ref<SelfAssessment | ''>('')
const markAsReview = ref(false)
const vimEnabled = ref(true)
const problemCollapsed = ref(false)
const testCases = ref<
  Array<{ id: number; input: string; expected_output: string; sample: boolean }>
>([])
const runningTests = ref(false)
const runError = ref<string | null>(null)
const runResult = ref<RunTestsResult | null>(null)
const aiReviewLoading = ref(false)
const aiReviewError = ref<string | null>(null)
const aiReview = ref<AiReviewResult | null>(null)
const draftStatus = ref<'idle' | 'saving' | 'saved' | 'error'>('idle')
const draftSavedAt = ref<string | null>(null)
const pastCode = ref<string | null>(null)
const pastCodeOpen = ref(false)
const editorHeight = ref(readStoredHeight())
let nextCaseId = 1
let draftTimer: number | undefined
let heightTimer: number | undefined

const EDITOR_HEIGHT_KEY = 'momocode-editor-height'
const MIN_EDITOR_HEIGHT = 320
const MAX_EDITOR_HEIGHT = 1100

function readStoredHeight(): number {
  if (typeof window === 'undefined') return 560
  const raw = Number(window.localStorage.getItem(EDITOR_HEIGHT_KEY))
  if (!Number.isFinite(raw) || raw <= 0) return 560
  return Math.min(MAX_EDITOR_HEIGHT, Math.max(MIN_EDITOR_HEIGHT, raw))
}

const editorStyle = computed(() => ({
  height: `${editorHeight.value}px`,
}))

function resizeBy(delta: number): void {
  editorHeight.value = Math.min(
    MAX_EDITOR_HEIGHT,
    Math.max(MIN_EDITOR_HEIGHT, editorHeight.value + delta),
  )
  window.localStorage.setItem(EDITOR_HEIGHT_KEY, String(editorHeight.value))
}

function startResize(event: PointerEvent): void {
  event.preventDefault()
  const startY = event.clientY
  const startHeight = editorHeight.value
  const target = event.currentTarget as HTMLElement | null
  target?.setPointerCapture?.(event.pointerId)

  function onMove(moveEvent: PointerEvent): void {
    const next = Math.min(
      MAX_EDITOR_HEIGHT,
      Math.max(MIN_EDITOR_HEIGHT, startHeight + (moveEvent.clientY - startY)),
    )
    editorHeight.value = next
  }

  function onUp(): void {
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
    if (heightTimer !== undefined) window.clearTimeout(heightTimer)
    heightTimer = window.setTimeout(() => {
      window.localStorage.setItem(EDITOR_HEIGHT_KEY, String(editorHeight.value))
    }, 200)
  }

  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

const task = computed(() => session.value?.task ?? null)
const isRecognition = computed(() => session.value?.training_type === 'recognition')
const isSubmitted = computed(() => session.value?.status === 'submitted')
const needsSelfAssessment = computed(
  () => !isRecognition.value && task.value?.evaluation_mode === 'self_assessment',
)
const selfAssessmentOptions: Array<{ value: SelfAssessment; label: string }> = [
  { value: 'correct', label: '正确' },
  { value: 'partial', label: '部分正确' },
  { value: 'incorrect', label: '错误' },
]
const editorTheme = computed(() => (resolved.value === 'dark' ? 'vs-dark' : 'vs'))
const modeLabel = computed(() => (session.value?.mode === 'review' ? '正式复习' : '自由练习'))

const statusLabels: Record<string, string> = {
  in_progress: '进行中',
  submitted: '已提交',
  completed: '已完成',
  abandoned: '已放弃',
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const data = await practiceApi.getSession(sessionId.value)
    if (data.status === 'completed') {
      await router.replace(`/practice/sessions/${data.id}/result`)
      return
    }
    session.value = data
    code.value = data.draft_code ?? data.task.code_scaffold ?? ''
    draftSavedAt.value = data.draft_saved_at
    draftStatus.value = data.draft_code ? 'saved' : 'idle'
    pastCode.value = data.submitted_code ?? null
    selfAssessment.value = data.self_assessment ?? ''
    testCases.value = (data.task.sample_cases ?? []).map((item) => ({
      id: nextCaseId++,
      input: item.input,
      expected_output: item.expected_output,
      sample: true,
    }))
    if (data.training_type === 'recognition') {
      recognitionSkills.value = await catalogApi.skills({ skill_type: 'recognition' })
    }
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function reloadSession(): Promise<void> {
  const data = await practiceApi.getSession(sessionId.value)
  session.value = data
}

async function requestHint(level: number): Promise<void> {
  hintLoading.value = true
  answerError.value = null
  try {
    await practiceApi.requestHint(sessionId.value, level)
    await reloadSession()
  } catch (err) {
    answerError.value = getApiErrorMessage(err)
  } finally {
    hintLoading.value = false
  }
}

function toggleSkill(skillId: string): void {
  if (selectedSkillIds.value.includes(skillId)) {
    selectedSkillIds.value = selectedSkillIds.value.filter((id) => id !== skillId)
  } else {
    selectedSkillIds.value = [...selectedSkillIds.value, skillId]
  }
}

function toggleErrorType(errorType: string): void {
  if (errorTypes.value.includes(errorType)) {
    errorTypes.value = errorTypes.value.filter((item) => item !== errorType)
  } else {
    errorTypes.value = [...errorTypes.value, errorType]
  }
}

function addTestCase(): void {
  testCases.value = [
    ...testCases.value,
    { id: nextCaseId++, input: '', expected_output: '', sample: false },
  ]
}

function removeTestCase(id: number): void {
  testCases.value = testCases.value.filter((item) => item.id !== id)
}

function caseResult(index: number) {
  return runResult.value?.cases?.[index]
}

function caseStatusLabel(status: string): string {
  if (status === 'ok') return '通过'
  if (status === 'wrong_answer') return '答案错误'
  if (status === 'time_limit_exceeded') return '超时'
  if (status === 'runtime_error') return '运行错误'
  return status
}

function restoreTemplate(): void {
  if (!task.value) return
  code.value = task.value.code_scaffold ?? ''
  draftStatus.value = 'idle'
  void persistDraft()
}

function usePastCode(): void {
  if (!pastCode.value) return
  code.value = pastCode.value
  pastCodeOpen.value = false
  void persistDraft()
}

async function persistDraft(): Promise<void> {
  if (!session.value || session.value.status !== 'in_progress') return
  const snapshot = code.value
  draftStatus.value = 'saving'
  try {
    const data = await practiceApi.saveDraft(sessionId.value, snapshot)
    if (data.draft_code === snapshot) {
      draftStatus.value = 'saved'
      draftSavedAt.value = data.draft_saved_at
    }
  } catch {
    draftStatus.value = 'error'
  }
}

function scheduleDraftSave(): void {
  if (draftTimer !== undefined) window.clearTimeout(draftTimer)
  draftTimer = window.setTimeout(() => {
    void persistDraft()
  }, 700)
}

watch(code, (value, previous) => {
  if (!session.value || session.value.status !== 'in_progress') return
  if (value === previous) return
  draftStatus.value = 'saving'
  scheduleDraftSave()
})

onBeforeUnmount(() => {
  if (draftTimer !== undefined) window.clearTimeout(draftTimer)
  if (heightTimer !== undefined) window.clearTimeout(heightTimer)
  window.localStorage.setItem(EDITOR_HEIGHT_KEY, String(editorHeight.value))
  if (draftStatus.value === 'saving') {
    void practiceApi.saveDraft(sessionId.value, code.value).catch(() => undefined)
  }
})

async function runAiReview(): Promise<void> {
  aiReviewError.value = null
  aiReview.value = null
  if (!code.value.trim()) {
    aiReviewError.value = '代码不能为空。'
    return
  }

  aiReviewLoading.value = true
  try {
    aiReview.value = await practiceApi.aiReview(sessionId.value, code.value)
  } catch (err) {
    aiReviewError.value = getApiErrorMessage(err)
  } finally {
    aiReviewLoading.value = false
  }
}

async function runTests(): Promise<void> {
  runError.value = null
  runResult.value = null
  if (testCases.value.length === 0) {
    runError.value = '请至少添加一个测试用例。'
    return
  }
  if (!code.value.trim()) {
    runError.value = '代码不能为空。'
    return
  }

  runningTests.value = true
  try {
    runResult.value = await practiceApi.runTests(
      sessionId.value,
      code.value,
      testCases.value.map((item) => ({
        input: item.input,
        expected_output: item.expected_output || undefined,
      })),
    )
  } catch (err) {
    runError.value = getApiErrorMessage(err)
  } finally {
    runningTests.value = false
  }
}

async function completeOnly(): Promise<void> {
  submitting.value = true
  answerError.value = null
  try {
    await practiceApi.completeSession(
      sessionId.value,
      markAsReview.value || session.value?.mode === 'review',
    )
    await router.push(`/practice/sessions/${sessionId.value}/result`)
  } catch (err) {
    answerError.value = getApiErrorMessage(err)
  } finally {
    submitting.value = false
  }
}

async function submit(): Promise<void> {
  if (!session.value || !task.value) return
  if (isSubmitted.value) {
    await completeOnly()
    return
  }

  answerError.value = null
  if (isRecognition.value && selectedSkillIds.value.length === 0) {
    answerError.value = '请选择至少一个算法/技能。'
    return
  }
  if (needsSelfAssessment.value && !selfAssessment.value) {
    answerError.value = '请先完成自评。'
    return
  }

  submitting.value = true
  try {
    if (isRecognition.value) {
      await practiceApi.submitAnswer(sessionId.value, {
        answer_payload: { selected_skill_ids: selectedSkillIds.value },
      })
    } else {
      await practiceApi.submitAnswer(sessionId.value, {
        answer_payload: { code: code.value },
        self_assessment: selfAssessment.value || undefined,
        error_types: errorTypes.value,
      })
    }
    await practiceApi.completeSession(
      sessionId.value,
      markAsReview.value || session.value.mode === 'review',
    )
    await router.push(`/practice/sessions/${sessionId.value}/result`)
  } catch (err) {
    answerError.value = getApiErrorMessage(err)
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <template v-else-if="session && task">
    <div class="page-header">
      <div>
        <h1>{{ task.title }}</h1>
        <p>左侧阅读题目与约束，右侧完成作答并提交。</p>
      </div>
      <div class="workspace-actions">
        <button
          class="btn btn-ghost"
          type="button"
          :aria-pressed="problemCollapsed"
          @click="problemCollapsed = !problemCollapsed"
        >
          {{ problemCollapsed ? '展开题目' : '收起题目' }}
        </button>
        <details class="workspace-popover">
          <summary class="btn btn-ghost">本次状态</summary>
          <div class="popover-panel">
            <h3>本次状态</h3>
            <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
              <span class="badge">{{ modeLabel }}</span>
              <span class="badge">{{ statusLabels[session.status] ?? session.status }}</span>
              <span class="badge"
                >提示 {{ session.max_hint_level }} / {{ task.max_hint_level }}</span
              >
              <span class="badge">难度 {{ task.difficulty }}</span>
            </div>
            <p style="color: var(--text-muted); margin-top: 8px">
              提交后系统会自动编译并运行代码，与内置测试用例比对。
            </p>
          </div>
        </details>

        <details v-if="!isRecognition && task.error_types.length" class="workspace-popover">
          <summary class="btn btn-ghost" :class="{ 'is-active': errorTypes.length }">
            错误类型{{ errorTypes.length ? ` · ${errorTypes.length}` : '' }}
          </summary>
          <div class="popover-panel">
            <h3>错误类型</h3>
            <div class="answer-options" style="margin-top: 8px">
              <label v-for="errorType in task.error_types" :key="errorType" class="answer-option">
                <input
                  type="checkbox"
                  :value="errorType"
                  :checked="errorTypes.includes(errorType)"
                  :disabled="isSubmitted"
                  @change="toggleErrorType(errorType)"
                />
                {{ errorType }}
              </label>
            </div>
          </div>
        </details>

        <SessionTimer :started-at="session.started_at" />
      </div>
    </div>

    <div
      v-if="answerError"
      class="notice"
      role="alert"
      style="border-color: var(--danger); color: var(--danger); margin-bottom: 16px"
    >
      {{ answerError }}
    </div>

    <div class="workspace-grid" :class="{ 'is-collapsed': problemCollapsed }">
      <aside class="card workspace-problem">
        <div class="workspace-problem-body">
          <h2>题目</h2>
          <MarkdownText :content="task.statement_md" />
          <div v-if="task.constraints_md" style="margin-top: 16px">
            <h3>约束</h3>
            <MarkdownText :content="task.constraints_md" />
          </div>
          <div v-if="task.target_skills.length" style="margin-top: 16px">
            <h3>目标技能</h3>
            <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
              <span v-for="skill in task.target_skills" :key="skill.id" class="badge">
                {{ skill.name }}
              </span>
            </div>
          </div>
          <div class="notice" style="margin-top: 16px">
            参考实现会在提交后展示；正式复习时不会提前暴露答案。
          </div>
        </div>

        <details class="hint-drawer">
          <summary>
            <span>提示</span>
            <span class="hint-summary-meta">
              可用 {{ task.max_hint_level }} 级 · {{ session.hints_used.length }} 已用
            </span>
          </summary>
          <div class="hint-drawer-body">
            <HintPanel
              :max-hint-level="task.max_hint_level"
              :hints-used="session.hints_used"
              :loading="hintLoading"
              @request="requestHint"
            />
          </div>
        </details>
      </aside>

      <div class="workspace-answer">
        <section class="card" :class="{ 'workspace-answer-card': !isRecognition }">
          <div class="answer-toolbar">
            <h2>作答</h2>
            <div class="answer-toolbar-actions">
              <span class="badge" :class="{ 'badge-success': draftStatus === 'saved' }">
                <template v-if="draftStatus === 'saving'">保存中…</template>
                <template v-else-if="draftStatus === 'saved'">草稿已保存</template>
                <template v-else-if="draftStatus === 'error'">草稿保存失败</template>
                <template v-else>自动保存已开启</template>
              </span>
              <template v-if="!isRecognition">
                <button class="btn btn-ghost" type="button" @click="restoreTemplate">
                  格式化（回到模板）
                </button>
                <button
                  class="btn btn-ghost"
                  type="button"
                  :disabled="!pastCode"
                  :title="pastCode ? '查看上一次提交的代码' : '暂无历史代码'"
                  @click="pastCodeOpen = !pastCodeOpen"
                >
                  历史代码
                </button>
                <button
                  class="btn btn-ghost"
                  :class="{ 'is-active': vimEnabled }"
                  type="button"
                  :aria-pressed="vimEnabled"
                  @click="vimEnabled = !vimEnabled"
                >
                  Vim {{ vimEnabled ? '开' : '关' }}
                </button>
              </template>
            </div>
          </div>

          <div v-if="pastCodeOpen && pastCode" class="history-code">
            <div class="topbar-actions" style="justify-content: space-between">
              <strong>上一次提交的代码</strong>
              <div class="answer-toolbar-actions">
                <button class="btn btn-ghost" type="button" @click="usePastCode">填入编辑区</button>
                <button class="btn btn-ghost" type="button" @click="pastCodeOpen = false">
                  关闭
                </button>
              </div>
            </div>
            <pre class="code-block">{{ pastCode }}</pre>
          </div>

          <template v-if="isRecognition">
            <p style="color: var(--text-muted); margin-top: 4px">
              选择你认为适用的算法/技能，可多选。
            </p>
            <div class="answer-options answer-options-wide" style="margin-top: 12px">
              <label v-for="skill in recognitionSkills" :key="skill.id" class="answer-option">
                <input
                  type="checkbox"
                  :value="skill.id"
                  :checked="selectedSkillIds.includes(skill.id)"
                  @change="toggleSkill(skill.id)"
                />
                <span>
                  <strong>{{ skill.algorithm_name }}</strong>
                  <span style="color: var(--text-muted)"> · {{ skill.name }}</span>
                </span>
              </label>
            </div>
          </template>

          <template v-else>
            <div class="editor-frame" :style="editorStyle">
              <MonacoEditor
                v-model="code"
                language="cpp"
                :theme="editorTheme"
                :read-only="session.status !== 'in_progress'"
                :vim-enabled="vimEnabled"
              />
            </div>
            <div
              class="editor-resizer"
              role="separator"
              aria-orientation="horizontal"
              aria-label="拖动调整编辑器高度"
              tabindex="0"
              :title="`编辑器高度 ${editorHeight}px`"
              @pointerdown="startResize"
              @keydown.up.prevent="resizeBy(-40)"
              @keydown.down.prevent="resizeBy(40)"
            />

            <div class="editor-meta">
              <span>高度 {{ editorHeight }}px · 可拖动下方分隔条调整</span>
              <span v-if="draftSavedAt">
                草稿保存于 {{ new Date(draftSavedAt).toLocaleTimeString('zh-CN') }}
              </span>
            </div>
            <p style="color: var(--text-muted); margin-top: 12px">
              {{
                needsSelfAssessment
                  ? '本题来自 OJ 或模板复现，没有内置判题用例；提交前请先完成自评。'
                  : '提交后系统会自动编译并运行代码，与内置测试用例比对；不需要手动自评。'
              }}
            </p>

            <div
              v-if="needsSelfAssessment && !isSubmitted"
              class="notice notice-accent"
              style="margin-top: 12px"
            >
              <strong>完成后自评</strong>
              <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
                <button
                  v-for="option in selfAssessmentOptions"
                  :key="option.value"
                  class="btn"
                  :class="{ 'btn-primary': selfAssessment === option.value }"
                  type="button"
                  :aria-pressed="selfAssessment === option.value"
                  @click="selfAssessment = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>

            <details class="test-runner ai-review" open>
              <summary>
                <span>AI 判题</span>
                <span class="hint-summary-meta">题面 + 参考实现 + 你的代码</span>
              </summary>
              <div class="test-runner-body">
                <p style="color: var(--text-muted); font-size: 12px">
                  AI
                  依据题面、约束和参考实现给出一致性结论与改进建议，不执行代码；最终判分仍以内置测试用例为准。
                </p>
                <div class="test-runner-actions">
                  <span />
                  <button
                    class="btn btn-primary"
                    type="button"
                    :disabled="aiReviewLoading"
                    @click="runAiReview"
                  >
                    {{ aiReviewLoading ? '分析中…' : 'AI 判题' }}
                  </button>
                </div>

                <div
                  v-if="aiReviewError"
                  class="notice"
                  role="alert"
                  style="border-color: var(--danger); color: var(--danger)"
                >
                  {{ aiReviewError }}
                </div>

                <div v-if="aiReview" class="notice notice-accent">
                  <div style="width: 100%">
                    <div class="topbar-actions" style="justify-content: space-between">
                      <strong>{{ aiReview.summary }}</strong>
                      <span
                        class="badge"
                        :class="
                          aiReview.verdict === 'correct'
                            ? 'badge-success'
                            : aiReview.verdict === 'partial'
                              ? 'badge-warning'
                              : 'badge-danger'
                        "
                      >
                        {{ aiReview.verdict }}
                        <template v-if="aiReview.score !== null"> · {{ aiReview.score }} </template>
                      </span>
                    </div>
                    <ul v-if="aiReview.issues.length" class="ai-review-list">
                      <li v-for="issue in aiReview.issues" :key="issue">{{ issue }}</li>
                    </ul>
                    <ul v-if="aiReview.suggestions.length" class="ai-review-list">
                      <li v-for="item in aiReview.suggestions" :key="item">{{ item }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </details>

            <details class="test-runner" open>
              <summary>
                <span>测试运行</span>
                <span class="hint-summary-meta">{{ testCases.length }} 个用例</span>
              </summary>
              <div class="test-runner-body">
                <div v-for="(item, index) in testCases" :key="item.id" class="test-case">
                  <div class="test-case-head">
                    <span class="badge" :class="{ 'badge-accent': item.sample }">
                      {{ item.sample ? '题目样例' : '自定义' }} {{ index + 1 }}
                    </span>
                    <button
                      v-if="!item.sample"
                      class="btn btn-ghost"
                      type="button"
                      @click="removeTestCase(item.id)"
                    >
                      删除
                    </button>
                  </div>
                  <div class="test-case-grid">
                    <label>
                      <span class="stat-label">输入</span>
                      <textarea v-model="item.input" rows="3"></textarea>
                    </label>
                    <label>
                      <span class="stat-label">期望输出（可留空）</span>
                      <textarea v-model="item.expected_output" rows="3"></textarea>
                    </label>
                  </div>
                  <div v-if="caseResult(index)" class="test-case-result">
                    <span
                      class="badge"
                      :class="caseResult(index)?.status === 'ok' ? 'badge-success' : 'badge-danger'"
                    >
                      {{ caseStatusLabel(caseResult(index)?.status ?? '') }}
                    </span>
                    <div>
                      <span class="stat-label">实际输出</span>
                      <pre class="code-block">{{
                        caseResult(index)?.actual_output || '（无输出）'
                      }}</pre>
                    </div>
                  </div>
                </div>

                <div class="test-runner-actions">
                  <button class="btn btn-ghost" type="button" @click="addTestCase">添加用例</button>
                  <button
                    class="btn btn-primary"
                    type="button"
                    :disabled="runningTests"
                    @click="runTests"
                  >
                    {{ runningTests ? '运行中…' : '运行测试' }}
                  </button>
                </div>

                <div
                  v-if="runError"
                  class="notice"
                  role="alert"
                  style="border-color: var(--danger); color: var(--danger)"
                >
                  {{ runError }}
                </div>

                <div v-if="runResult" class="notice notice-accent" style="margin-top: 12px">
                  <div>
                    <strong>
                      {{ runResult.result }} · 通过 {{ runResult.passed }} / {{ runResult.total }}
                    </strong>
                    <pre v-if="runResult.compile_output" class="code-block">{{
                      runResult.compile_output
                    }}</pre>
                  </div>
                </div>
              </div>
            </details>
          </template>

          <div class="topbar-actions" style="margin-top: 16px; justify-content: space-between">
            <label v-if="session.mode === 'free'" class="answer-option" style="margin: 0">
              <input v-model="markAsReview" type="checkbox" />
              标记为正式复习
            </label>
            <span v-else class="badge">正式复习会更新复习进度</span>

            <button class="btn btn-primary" type="button" :disabled="submitting" @click="submit">
              {{ submitting ? '提交中…' : isSubmitted ? '完成会话' : '提交' }}
            </button>
          </div>
        </section>
      </div>
    </div>
  </template>
</template>
