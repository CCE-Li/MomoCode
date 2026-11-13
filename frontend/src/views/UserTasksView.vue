<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'
import TaskCard from '@/components/TaskCard.vue'
import { catalogApi } from '@/api/catalog'
import { userTasksApi } from '@/api/userTasks'
import { practiceApi } from '@/api/practice'
import { ApiError, getApiErrorMessage } from '@/api/client'
import type { SkillSummary, TaskSummary, TrainingType } from '@/types/catalog'
import type { UserTaskInput, UserTaskPlatform } from '@/types/userTasks'

const router = useRouter()
const skills = ref<SkillSummary[]>([])
const tasks = ref<TaskSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const startingTaskId = ref<string | null>(null)
const actionError = ref<string | null>(null)
const tagFilter = ref('')

const formOpen = ref(true)
const saving = ref(false)
const formError = ref<string | null>(null)
const skillSearch = ref('')
const selectedSkillSlugs = ref<string[]>([])
const form = reactive({
  title: '',
  trainingType: 'variant' as TrainingType,
  difficulty: 3,
  platform: '' as '' | UserTaskPlatform,
  problemRef: '',
  problemUrl: '',
  statement: '',
  constraints: '',
  tags: '',
  codeScaffold: '',
  referenceSolution: '',
  hintsJson: '{\n  "1": "先判断题目对应的模型",\n  "2": "写出核心循环或状态转移"\n}',
})

const importOpen = ref(false)
const importing = ref(false)
const importError = ref<string | null>(null)
const importMessage = ref<string | null>(null)
const importJson = ref(`[
  {
    "title": "示例：CF 706B Interesting drink",
    "training_type": "variant",
    "evaluation_mode": "self_assessment",
    "difficulty": 2,
    "oj_platform": "codeforces",
    "oj_problem_ref": "CF 706B",
    "oj_problem_url": "https://codeforces.com/problemset/problem/706/B",
    "statement_md": "完成题目后，用二分模板复盘边界。",
    "target_skills": ["binary-search-template"],
    "max_hint_level": 0
  }
]`)

const filteredSkills = computed(() => {
  const keyword = skillSearch.value.trim().toLowerCase()
  const list = keyword
    ? skills.value.filter(
        (skill) =>
          skill.name.toLowerCase().includes(keyword) ||
          skill.slug.includes(keyword) ||
          skill.algorithm_name.toLowerCase().includes(keyword),
      )
    : skills.value
  return list.slice(0, 80)
})

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [skillData, taskData] = await Promise.all([
      catalogApi.skills(),
      userTasksApi.list({ tag: tagFilter.value.trim() || undefined }),
    ])
    skills.value = skillData
    tasks.value = taskData
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function parseTags(value: string): string[] {
  const result: string[] = []
  const seen = new Set<string>()
  for (const piece of value.split(/[\s,，]+/)) {
    const tag = piece.trim().replace(/^#+/, '')
    if (!tag) continue
    const key = tag.toLocaleLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    result.push(tag.slice(0, 32))
    if (result.length >= 12) break
  }
  return result
}

function messageFor(err: unknown): string {
  if (err instanceof SyntaxError) return 'JSON 格式不正确，请检查语法。'
  if (err instanceof Error && !(err instanceof ApiError)) return err.message
  return getApiErrorMessage(err)
}

function toggleSkill(slug: string): void {
  if (selectedSkillSlugs.value.includes(slug)) {
    selectedSkillSlugs.value = selectedSkillSlugs.value.filter((item) => item !== slug)
  } else {
    selectedSkillSlugs.value = [...selectedSkillSlugs.value, slug]
  }
}

function parseHints(): Record<string, string> {
  const text = form.hintsJson.trim()
  if (!text) return {}
  const parsed: unknown = JSON.parse(text)
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    throw new Error('提示必须是对象，例如 {"1": "...", "2": "..."}。')
  }
  const hints: Record<string, string> = {}
  for (const [key, value] of Object.entries(parsed)) {
    if (!/^[1-5]$/.test(key)) {
      throw new Error('提示键只能是 1–5。')
    }
    hints[key] = String(value)
  }
  return hints
}

function buildPayload(): UserTaskInput {
  if (!form.title.trim()) throw new Error('请填写标题。')
  if (!form.statement.trim()) throw new Error('请填写题目说明。')
  if (selectedSkillSlugs.value.length === 0) throw new Error('请选择至少一个目标技能。')
  if (form.platform && !form.problemRef.trim()) {
    throw new Error('关联 OJ 时请填写题号。')
  }
  if (form.platform && !form.problemUrl.trim()) {
    throw new Error('关联 OJ 时请填写题目链接。')
  }
  if (form.trainingType === 'recognition' && selectedSkillSlugs.value.length === 0) {
    throw new Error('识别题需要至少一个目标技能。')
  }

  const hints = parseHints()
  if (form.trainingType === 'recognition' && Object.keys(hints).some((key) => Number(key) > 3)) {
    throw new Error('识别题只允许 1–3 级提示。')
  }
  const maxHintLevel = Object.keys(hints).length
    ? Math.max(...Object.keys(hints).map(Number))
    : 0

  return {
    title: form.title.trim(),
    training_type: form.trainingType,
    evaluation_mode:
      form.trainingType === 'recognition' ? 'auto_recognition' : 'self_assessment',
    difficulty: Number(form.difficulty),
    source_ref: form.platform ? `${form.platform}:${form.problemRef.trim()}` : null,
    oj_platform: form.platform || null,
    oj_problem_ref: form.platform ? form.problemRef.trim() : null,
    oj_problem_url: form.platform ? form.problemUrl.trim() : null,
    statement_md: form.statement.trim(),
    constraints_md: form.constraints.trim() || null,
    code_scaffold: form.codeScaffold || null,
    reference_solution_md: form.referenceSolution || null,
    language: 'cpp17',
    hints,
    max_hint_level: maxHintLevel,
    tags: parseTags(form.tags),
    target_skills: selectedSkillSlugs.value,
    related_skills: [],
  }
}

async function createTask(): Promise<void> {
  formError.value = null
  saving.value = true
  try {
    const payload = buildPayload()
    await userTasksApi.create(payload)
    form.title = ''
    form.statement = ''
    form.constraints = ''
    form.tags = ''
    form.codeScaffold = ''
    form.referenceSolution = ''
    form.problemRef = ''
    form.problemUrl = ''
    selectedSkillSlugs.value = []
    await load()
  } catch (err) {
    formError.value = messageFor(err)
  } finally {
    saving.value = false
  }
}

async function bulkImport(): Promise<void> {
  importError.value = null
  importMessage.value = null
  importing.value = true
  try {
    const parsed: unknown = JSON.parse(importJson.value)
    const items = Array.isArray(parsed)
      ? parsed
      : typeof parsed === 'object' && parsed !== null && Array.isArray((parsed as { tasks?: unknown }).tasks)
        ? (parsed as { tasks: unknown[] }).tasks
        : null
    if (!items || items.length === 0) {
      throw new Error('请输入 JSON 数组，或 {"tasks": [...]}。')
    }
    const result = await userTasksApi.bulkImport(items as UserTaskInput[])
    importMessage.value = `成功导入 ${result.total} 道题。`
    await load()
  } catch (err) {
    importError.value = messageFor(err)
  } finally {
    importing.value = false
  }
}

async function startTask(task: TaskSummary): Promise<void> {
  startingTaskId.value = task.id
  actionError.value = null
  try {
    const session = await practiceApi.createSession(task.id, 'free')
    await router.push(`/practice/sessions/${session.id}`)
  } catch (err) {
    actionError.value = getApiErrorMessage(err)
  } finally {
    startingTaskId.value = null
  }
}

async function removeTask(task: TaskSummary): Promise<void> {
  if (!window.confirm(`删除自建题目「${task.title}」？历史训练记录会保留。`)) {
    return
  }
  actionError.value = null
  try {
    await userTasksApi.delete(task.id)
    await load()
  } catch (err) {
    actionError.value = getApiErrorMessage(err)
  }
}

onMounted(load)
</script>

<template>
  <PageHeader
    title="我的题目"
    description="按与内置内容相同的导入规则，添加自己的 OJ 题目或原创训练题；只有你自己可见。"
  >
    <template #actions>
      <RouterLink class="btn btn-ghost" to="/practice">自由练习</RouterLink>
      <RouterLink class="btn btn-ghost" to="/library">算法库</RouterLink>
    </template>
  </PageHeader>

  <div
    v-if="actionError"
    class="notice"
    role="alert"
    style="border-color: var(--danger); color: var(--danger); margin-bottom: 16px"
  >
    {{ actionError }}
  </div>

  <section class="card">
    <div class="topbar-actions" style="justify-content: space-between">
      <div>
        <h2>添加题目</h2>
        <p style="color: var(--text-muted); margin-top: 4px">
          必填：标题、题目说明、至少一个目标技能。关联 OJ 时需同时填写平台、题号和链接。
        </p>
      </div>
      <button class="btn btn-ghost" type="button" @click="formOpen = !formOpen">
        {{ formOpen ? '收起' : '展开' }}
      </button>
    </div>

    <form
      v-if="formOpen"
      style="margin-top: 16px; display: grid; gap: 12px"
      @submit.prevent="createTask"
    >
      <div class="grid grid-2">
        <div class="field">
          <label for="user-task-title">标题</label>
          <input
            id="user-task-title"
            v-model="form.title"
            maxlength="200"
            placeholder="例如：CF 706B 二分查找复盘"
            required
          />
        </div>
        <div class="field">
          <label for="user-task-difficulty">难度</label>
          <select id="user-task-difficulty" v-model.number="form.difficulty">
            <option :value="1">1</option>
            <option :value="2">2</option>
            <option :value="3">3</option>
            <option :value="4">4</option>
            <option :value="5">5</option>
          </select>
        </div>
      </div>

      <div class="grid grid-2">
        <div class="field">
          <label for="user-task-type">训练类型</label>
          <select id="user-task-type" v-model="form.trainingType">
            <option value="recognition">识别</option>
            <option value="template">模板复现</option>
            <option value="variant">变体 / OJ 题</option>
            <option value="correction">纠错</option>
          </select>
        </div>
        <div class="field">
          <label for="user-task-platform">来源平台</label>
          <select id="user-task-platform" v-model="form.platform">
            <option value="">不关联 OJ</option>
            <option value="codeforces">Codeforces</option>
            <option value="luogu">洛谷</option>
            <option value="atcoder">AtCoder</option>
            <option value="other">其他</option>
          </select>
        </div>
      </div>

      <div v-if="form.platform" class="grid grid-2">
        <div class="field">
          <label for="user-task-ref">题号</label>
          <input
            id="user-task-ref"
            v-model="form.problemRef"
            maxlength="200"
            placeholder="例如：CF 706B / P2249"
            required
          />
        </div>
        <div class="field">
          <label for="user-task-url">题目链接</label>
          <input
            id="user-task-url"
            v-model="form.problemUrl"
            type="url"
            maxlength="2000"
            placeholder="https://..."
            required
          />
        </div>
      </div>

      <div class="field">
        <label for="user-task-tags">标签（可带 #，空格或逗号分隔）</label>
        <input
          id="user-task-tags"
          v-model="form.tags"
          placeholder="#二分 #双指针 #BFS"
        />
      </div>

      <div class="field">
        <label for="user-task-statement">题目说明 / 训练目标</label>
        <textarea
          id="user-task-statement"
          v-model="form.statement"
          rows="5"
          maxlength="20000"
          placeholder="写下题目要求、复盘重点或模板目标…"
          required
        ></textarea>
      </div>

      <div class="grid grid-2">
        <div class="field">
          <label for="user-task-constraints">数据范围 / 约束（可选）</label>
          <textarea
            id="user-task-constraints"
            v-model="form.constraints"
            rows="3"
            maxlength="5000"
            placeholder="以 OJ 原题为准。"
          ></textarea>
        </div>
        <div class="field">
          <label for="user-task-hints">提示 JSON（可选，键 1–5）</label>
          <textarea
            id="user-task-hints"
            v-model="form.hintsJson"
            rows="3"
            placeholder='{"1": "...", "2": "..."}'
          ></textarea>
        </div>
      </div>

      <div class="field">
        <label for="user-task-skill-search">目标技能（至少一个）</label>
        <input
          id="user-task-skill-search"
          v-model="skillSearch"
          type="search"
          placeholder="搜索技能、算法或 slug"
        />
        <div
          class="answer-options answer-options-wide"
          style="margin-top: 8px; max-height: 240px; overflow: auto"
        >
          <label v-for="skill in filteredSkills" :key="skill.id" class="answer-option">
            <input
              type="checkbox"
              :value="skill.slug"
              :checked="selectedSkillSlugs.includes(skill.slug)"
              @change="toggleSkill(skill.slug)"
            />
            <span>
              <strong>{{ skill.algorithm_name }}</strong>
              <span style="color: var(--text-muted)"> · {{ skill.name }}</span>
            </span>
          </label>
        </div>
        <p style="color: var(--text-muted); margin-top: 6px">
          已选 {{ selectedSkillSlugs.length }} 个技能。
        </p>
      </div>

      <div class="grid grid-2">
        <div class="field">
          <label for="user-task-scaffold">起始代码（可选）</label>
          <textarea
            id="user-task-scaffold"
            v-model="form.codeScaffold"
            rows="5"
            maxlength="200000"
            placeholder="// TODO: ..."
          ></textarea>
        </div>
        <div class="field">
          <label for="user-task-reference">参考实现（可选，训练时隐藏）</label>
          <textarea
            id="user-task-reference"
            v-model="form.referenceSolution"
            rows="5"
            maxlength="200000"
            placeholder="参考代码或复盘结论"
          ></textarea>
        </div>
      </div>

      <div
        v-if="formError"
        class="notice"
        role="alert"
        style="border-color: var(--danger); color: var(--danger)"
      >
        {{ formError }}
      </div>
      <button class="btn btn-primary" type="submit" :disabled="saving">
        {{ saving ? '保存中…' : '添加题目' }}
      </button>
    </form>
  </section>

  <section class="card" style="margin-top: 16px">
    <div class="topbar-actions" style="justify-content: space-between">
      <div>
        <h2>批量导入</h2>
        <p style="color: var(--text-muted); margin-top: 4px">
          按内置 tasks.json 的字段格式导入 JSON 数组；最多 50 道，任一道校验失败则整批不写入。
        </p>
      </div>
      <button class="btn btn-ghost" type="button" @click="importOpen = !importOpen">
        {{ importOpen ? '收起' : '展开' }}
      </button>
    </div>

    <div v-if="importOpen" style="margin-top: 16px">
      <div class="field">
        <label for="user-task-import">JSON</label>
        <textarea
          id="user-task-import"
          v-model="importJson"
          rows="12"
          spellcheck="false"
          style="font-family: var(--font-mono)"
        ></textarea>
      </div>
      <div
        v-if="importError"
        class="notice"
        role="alert"
        style="border-color: var(--danger); color: var(--danger); margin-top: 12px"
      >
        {{ importError }}
      </div>
      <div v-if="importMessage" class="notice notice-accent" style="margin-top: 12px">
        {{ importMessage }}
      </div>
      <button
        class="btn btn-primary"
        type="button"
        style="margin-top: 12px"
        :disabled="importing"
        @click="bulkImport"
      >
        {{ importing ? '导入中…' : '批量导入' }}
      </button>
    </div>
  </section>

  <section class="card" style="margin-top: 16px">
    <div class="topbar-actions" style="justify-content: space-between; flex-wrap: wrap">
      <h2>我的题目</h2>
      <div class="topbar-actions" style="flex-wrap: wrap">
        <div class="field">
          <label class="sr-only" for="user-task-tag-filter">按标签筛选</label>
          <input
            id="user-task-tag-filter"
            v-model="tagFilter"
            type="search"
            placeholder="按标签筛选，如 #二分"
            @change="load"
          />
        </div>
        <button class="btn btn-ghost" type="button" @click="load">刷新</button>
      </div>
    </div>

    <LoadingState v-if="loading" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState
      v-else-if="tasks.length === 0"
      title="还没有自建题目"
      description="用上方表单添加一道题，它会出现在自由练习列表中，并可以关联目标技能进入复习。"
    />
    <div v-else class="grid grid-2" style="margin-top: 16px">
      <TaskCard
        v-for="task in tasks"
        :key="task.id"
        :task="task"
        :action-label="startingTaskId === task.id ? '创建中…' : '开始练习'"
        deletable
        @start="startTask"
        @delete="removeTask"
      />
    </div>
  </section>
</template>
