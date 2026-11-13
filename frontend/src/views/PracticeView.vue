<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'
import TaskCard from '@/components/TaskCard.vue'
import { catalogApi } from '@/api/catalog'
import { practiceApi } from '@/api/practice'
import { userTasksApi } from '@/api/userTasks'
import { getApiErrorMessage } from '@/api/client'
import type { TaskSummary, TrainingType } from '@/types/catalog'

const route = useRoute()
const router = useRouter()
const tasks = ref<TaskSummary[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const startError = ref<string | null>(null)
const startingTaskId = ref<string | null>(null)
const trainingType = ref<TrainingType | ''>('')
const difficulty = ref<number | ''>('')
const tag = ref('')
const search = ref('')
let searchTimer: number | undefined
let tagTimer: number | undefined

const tabs: { label: string; value: TrainingType | '' }[] = [
  { label: '全部', value: '' },
  { label: '识别', value: 'recognition' },
  { label: '模板', value: 'template' },
  { label: '变体', value: 'variant' },
  { label: '纠错', value: 'correction' },
]

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [catalogTasks, ownTasks] = await Promise.all([
      catalogApi.tasks({
        training_type: trainingType.value,
        difficulty: difficulty.value,
        tag: tag.value.trim() || undefined,
        search: search.value.trim() || undefined,
      }),
      userTasksApi.list({
        training_type: trainingType.value,
        difficulty: difficulty.value,
        tag: tag.value.trim() || undefined,
        search: search.value.trim() || undefined,
      }),
    ])
    tasks.value = [...catalogTasks, ...ownTasks].sort(
      (left, right) =>
        left.difficulty - right.difficulty || left.title.localeCompare(right.title, 'zh-CN'),
    )
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function startTask(task: TaskSummary): Promise<void> {
  startingTaskId.value = task.id
  startError.value = null
  try {
    const session = await practiceApi.createSession(task.id, 'free')
    await router.push(`/practice/sessions/${session.id}`)
  } catch (err) {
    startError.value = getApiErrorMessage(err)
  } finally {
    startingTaskId.value = null
  }
}

onMounted(() => {
  const type = route.query.type
  if (
    type === 'recognition' ||
    type === 'template' ||
    type === 'variant' ||
    type === 'correction'
  ) {
    trainingType.value = type
  }
  const initialTag = route.query.tag
  if (typeof initialTag === 'string') {
    tag.value = initialTag
  }
  load()
})

watch([trainingType, difficulty], load)
watch(search, () => {
  if (searchTimer !== undefined) {
    window.clearTimeout(searchTimer)
  }
  searchTimer = window.setTimeout(load, 300)
})
watch(tag, () => {
  if (tagTimer !== undefined) {
    window.clearTimeout(tagTimer)
  }
  tagTimer = window.setTimeout(load, 300)
})

onBeforeUnmount(() => {
  if (searchTimer !== undefined) {
    window.clearTimeout(searchTimer)
  }
  if (tagTimer !== undefined) {
    window.clearTimeout(tagTimer)
  }
})
</script>

<template>
  <PageHeader
    title="自由练习"
    description="自由选择任务练习；默认不更新 FSRS，完成时可显式标记为正式复习。"
  >
    <template #actions>
      <RouterLink class="btn btn-ghost" to="/practice/user-tasks">我的题目</RouterLink>
      <RouterLink class="btn btn-ghost" to="/library">浏览算法库</RouterLink>
    </template>
  </PageHeader>

  <div class="card" style="margin-bottom: 16px">
    <div class="topbar-actions" style="justify-content: space-between; flex-wrap: wrap">
      <div class="topbar-actions" style="flex-wrap: wrap">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="btn"
          :class="{ 'btn-primary': trainingType === tab.value }"
          type="button"
          @click="trainingType = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="topbar-actions" style="flex-wrap: wrap">
        <div class="field">
          <label class="sr-only" for="practice-search">搜索任务</label>
          <input
            id="practice-search"
            v-model="search"
            type="search"
            placeholder="搜索任务"
          />
        </div>
        <div class="field">
          <label class="sr-only" for="practice-tag">标签</label>
          <input
            id="practice-tag"
            v-model="tag"
            type="search"
            placeholder="标签，如 #二分"
          />
        </div>
        <div class="field">
          <label class="sr-only" for="practice-difficulty">难度</label>
          <select id="practice-difficulty" v-model="difficulty">
            <option value="">全部难度</option>
            <option :value="1">1</option>
            <option :value="2">2</option>
            <option :value="3">3</option>
            <option :value="4">4</option>
            <option :value="5">5</option>
          </select>
        </div>
      </div>
    </div>
  </div>

  <div
    v-if="startError"
    class="notice"
    role="alert"
    style="border-color: var(--danger); color: var(--danger); margin-bottom: 16px"
  >
    {{ startError }}
  </div>

  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <EmptyState
    v-else-if="tasks.length === 0"
    title="没有匹配的任务"
    description="尝试切换训练类型、难度或清除搜索。"
  >
    <button
      class="btn btn-ghost"
      type="button"
      @click="trainingType = ''; difficulty = ''; tag = ''; search = ''"
    >
      清除筛选
    </button>
  </EmptyState>
  <div v-else class="grid grid-2">
    <TaskCard
      v-for="task in tasks"
      :key="task.id"
      :task="task"
      :action-label="startingTaskId === task.id ? '创建中…' : '开始练习'"
      @start="startTask"
    />
  </div>

  <div class="notice notice-accent" style="margin-top: 16px">
    自由练习默认不更新复习进度；标记为正式复习后才会更新对应技能的记忆状态。
  </div>
</template>
