<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'
import { reviewApi } from '@/api/review'
import { practiceApi } from '@/api/practice'
import { getApiErrorMessage } from '@/api/client'
import type {
  CustomReviewItem,
  DueItem,
  DueQueue,
  ReviewHistoryItem,
  TodayReview,
} from '@/types/review'

const router = useRouter()
const due = ref<DueQueue | null>(null)
const today = ref<TodayReview | null>(null)
const history = ref<ReviewHistoryItem[]>([])
const customItems = ref<CustomReviewItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const startingItemId = ref<string | null>(null)
const reviewingItemId = ref<string | null>(null)
const startError = ref<string | null>(null)
const reviewError = ref<string | null>(null)
const customFormOpen = ref(false)
const customSaving = ref(false)
const customError = ref<string | null>(null)
const customForm = reactive({
  title: '',
  content: '',
  tags: '',
  sourceUrl: '',
})

const ratingOptions = [
  { value: 1, label: '重来' },
  { value: 2, label: '困难' },
  { value: 3, label: '良好' },
  { value: 4, label: '简单' },
]

const ratingLabels: Record<number, string> = {
  1: '重来',
  2: '困难',
  3: '良好',
  4: '简单',
}

function formatDate(value: string | null): string {
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

function itemKey(item: DueItem): string {
  return item.kind === 'custom' ? `custom-${item.custom_item_id}` : `skill-${item.skill_id}`
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [dueData, todayData, historyData, customData] = await Promise.all([
      reviewApi.due(),
      reviewApi.today(),
      reviewApi.history(20),
      reviewApi.customItems(),
    ])
    due.value = dueData
    today.value = todayData
    history.value = historyData
    customItems.value = customData
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

async function startReview(item: DueItem): Promise<void> {
  if (!item.task_id) return
  startingItemId.value = itemKey(item)
  startError.value = null
  try {
    const session = await practiceApi.createSession(item.task_id, 'review')
    await router.push(`/practice/sessions/${session.id}`)
  } catch (err) {
    startError.value = getApiErrorMessage(err)
  } finally {
    startingItemId.value = null
  }
}

async function rateCustom(item: DueItem, rating: number): Promise<void> {
  if (!item.custom_item_id) return
  reviewingItemId.value = itemKey(item)
  reviewError.value = null
  try {
    await reviewApi.reviewCustomItem(item.custom_item_id, rating)
    await load()
  } catch (err) {
    reviewError.value = getApiErrorMessage(err)
  } finally {
    reviewingItemId.value = null
  }
}

async function createCustomItem(): Promise<void> {
  customError.value = null
  if (!customForm.title.trim() || !customForm.content.trim()) {
    customError.value = '标题和内容不能为空。'
    return
  }
  customSaving.value = true
  try {
    await reviewApi.createCustomItem({
      title: customForm.title.trim(),
      content_md: customForm.content.trim(),
      tags: customForm.tags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
      source_url: customForm.sourceUrl.trim() || null,
    })
    customForm.title = ''
    customForm.content = ''
    customForm.tags = ''
    customForm.sourceUrl = ''
    customFormOpen.value = false
    await load()
  } catch (err) {
    customError.value = getApiErrorMessage(err)
  } finally {
    customSaving.value = false
  }
}

async function removeCustomItem(item: CustomReviewItem): Promise<void> {
  if (!window.confirm(`从复习队列移除「${item.title}」？历史复习记录会保留。`)) {
    return
  }
  customError.value = null
  try {
    await reviewApi.deleteCustomItem(item.id)
    await load()
  } catch (err) {
    customError.value = getApiErrorMessage(err)
  }
}

onMounted(load)
</script>

<template>
  <PageHeader
    title="智能复习"
    description="按 FSRS 到期队列完成正式复习；自定义内容与技能共用同一条遗忘曲线。"
  >
    <template #actions>
      <RouterLink class="btn btn-ghost" to="/practice">自由练习</RouterLink>
      <RouterLink class="btn btn-ghost" to="/settings">复习偏好</RouterLink>
    </template>
  </PageHeader>

  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <template v-else>
    <div class="stat-grid">
      <section class="card">
        <div class="stat-label">今日到期</div>
        <div class="stat-value">{{ today?.due_count ?? 0 }}</div>
        <div class="stat-hint">每日上限 {{ due?.daily_limit ?? 50 }}</div>
      </section>
      <section class="card">
        <div class="stat-label">逾期</div>
        <div class="stat-value">{{ today?.overdue_count ?? 0 }}</div>
        <div class="stat-hint">优先复习</div>
      </section>
      <section class="card">
        <div class="stat-label">今日已复习</div>
        <div class="stat-value">{{ today?.reviewed_today ?? 0 }}</div>
        <div class="stat-hint">含自定义内容</div>
      </section>
    </div>

    <div class="notice notice-accent" style="margin-top: 16px">
      时区：{{ due?.timezone ?? 'UTC' }}。正式复习会更新 FSRS；自由练习默认不更新。
    </div>

    <div
      v-if="startError || reviewError"
      class="notice"
      role="alert"
      style="border-color: var(--danger); color: var(--danger); margin-top: 16px"
    >
      {{ startError || reviewError }}
    </div>

    <section class="card" style="margin-top: 16px">
      <div class="topbar-actions" style="justify-content: space-between">
        <h2>到期队列</h2>
        <button class="btn btn-ghost" type="button" @click="load">刷新</button>
      </div>

      <div v-if="due && due.items.length" class="grid grid-2" style="margin-top: 16px">
        <article v-for="item in due.items" :key="itemKey(item)" class="card card-muted">
          <template v-if="item.kind === 'skill'">
            <div class="topbar-actions" style="justify-content: space-between">
              <h3>{{ item.skill_name }}</h3>
              <span class="badge" :class="{ 'badge-danger': item.overdue }">
                {{ item.overdue ? '逾期' : '到期' }}
              </span>
            </div>
            <p style="color: var(--text-muted); margin-top: 4px">
              {{ item.algorithm_name }}
            </p>
            <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
              <span class="badge">到期 {{ formatDate(item.due_at) }}</span>
              <span class="badge">{{ item.task_title }}</span>
            </div>
            <button
              class="btn btn-primary"
              type="button"
              :disabled="startingItemId === itemKey(item)"
              style="margin-top: 12px"
              @click="startReview(item)"
            >
              {{ startingItemId === itemKey(item) ? '创建中…' : '开始复习' }}
            </button>
          </template>

          <template v-else>
            <div class="topbar-actions" style="justify-content: space-between">
              <h3>{{ item.title }}</h3>
              <span class="badge" :class="{ 'badge-danger': item.overdue }">
                {{ item.overdue ? '逾期' : '自定义' }}
              </span>
            </div>
            <p style="color: var(--text-muted); margin-top: 4px">
              {{ item.content_preview }}
            </p>
            <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
              <span class="badge">到期 {{ formatDate(item.due_at) }}</span>
            </div>
            <div class="topbar-actions" style="margin-top: 12px; flex-wrap: wrap">
              <button
                v-for="option in ratingOptions"
                :key="option.value"
                class="btn btn-ghost"
                type="button"
                :disabled="reviewingItemId === itemKey(item)"
                @click="rateCustom(item, option.value)"
              >
                {{ option.label }}
              </button>
            </div>
          </template>
        </article>
      </div>

      <EmptyState
        v-else
        title="今日复习已完成"
        :description="
          today?.next_due_at
            ? `下次到期：${formatDate(today.next_due_at)}`
            : '暂时没有到期内容，可以自由练习或添加自定义复习内容。'
        "
      >
        <RouterLink class="btn btn-ghost" to="/practice">去自由练习</RouterLink>
      </EmptyState>
    </section>

    <section class="card" style="margin-top: 16px">
      <div class="topbar-actions" style="justify-content: space-between">
        <div>
          <h2>自定义复习内容</h2>
          <p style="color: var(--text-muted); margin-top: 4px">
            把想反复看的笔记、模板、错题结论加入队列，按 FSRS 安排复习。
          </p>
        </div>
        <button class="btn btn-ghost" type="button" @click="customFormOpen = !customFormOpen">
          {{ customFormOpen ? '收起' : '添加内容' }}
        </button>
      </div>

      <form
        v-if="customFormOpen"
        style="margin-top: 16px; display: grid; gap: 12px"
        @submit.prevent="createCustomItem"
      >
        <div class="field">
          <label for="custom-title">标题</label>
          <input
            id="custom-title"
            v-model="customForm.title"
            maxlength="200"
            placeholder="例如：树状数组的 lowbit 更新顺序"
            required
          />
        </div>
        <div class="field">
          <label for="custom-content">内容（支持 Markdown）</label>
          <textarea
            id="custom-content"
            v-model="customForm.content"
            rows="6"
            maxlength="20000"
            placeholder="写下你想复习的结论、模板或错题原因…"
            required
          ></textarea>
        </div>
        <div class="grid grid-2">
          <div class="field">
            <label for="custom-tags">标签（可带 #，逗号分隔）</label>
            <input id="custom-tags" v-model="customForm.tags" placeholder="#图论, #模板" />
          </div>
          <div class="field">
            <label for="custom-source">来源链接（可选）</label>
            <input
              id="custom-source"
              v-model="customForm.sourceUrl"
              type="url"
              placeholder="https://..."
            />
          </div>
        </div>
        <div
          v-if="customError"
          class="notice"
          role="alert"
          style="border-color: var(--danger); color: var(--danger)"
        >
          {{ customError }}
        </div>
        <button class="btn btn-primary" type="submit" :disabled="customSaving">
          {{ customSaving ? '保存中…' : '加入复习队列' }}
        </button>
      </form>

      <div v-if="customItems.length" class="grid" style="margin-top: 16px">
        <article v-for="item in customItems" :key="item.id" class="card card-muted">
          <div class="topbar-actions" style="justify-content: space-between">
            <strong>{{ item.title }}</strong>
            <span class="badge">下次到期 {{ formatDate(item.due_at) }}</span>
          </div>
          <p style="color: var(--text-muted); margin-top: 8px">
            {{ item.content_md.slice(0, 160)
            }}{{ item.content_md.length > 160 ? '…' : '' }}
          </p>
          <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
            <span v-for="tag in item.tags" :key="tag" class="badge">#{{ tag }}</span>
            <a
              v-if="item.source_url"
              class="btn btn-ghost"
              :href="item.source_url"
              target="_blank"
              rel="noreferrer"
            >
              来源
            </a>
            <button class="btn btn-ghost" type="button" @click="removeCustomItem(item)">
              移除
            </button>
          </div>
        </article>
      </div>
      <EmptyState
        v-else
        title="还没有自定义复习内容"
        description="添加一条笔记或模板，它会立即进入到期队列并参与 FSRS 调度。"
      />
    </section>

    <section v-if="history.length" class="card" style="margin-top: 16px">
      <h2>最近复习</h2>
      <div class="grid" style="margin-top: 12px">
        <div
          v-for="item in history"
          :key="item.id"
          class="topbar-actions"
          style="justify-content: space-between; flex-wrap: wrap"
        >
          <span>
            <strong>{{ item.kind === 'custom' ? item.title : item.skill_name }}</strong>
            <span v-if="item.kind === 'skill'" style="color: var(--text-muted)">
              · {{ item.algorithm_name }}
            </span>
            <span v-else class="badge" style="margin-left: 8px">自定义</span>
          </span>
          <span class="topbar-actions" style="flex-wrap: wrap">
            <span class="badge">{{ ratingLabels[item.rating] ?? item.rating }}</span>
            <span class="badge">{{ formatDate(item.reviewed_at) }}</span>
          </span>
        </div>
      </div>
    </section>
  </template>
</template>
