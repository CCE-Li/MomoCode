<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ActivityHeatmap from '@/components/ActivityHeatmap.vue'
import StatCard from '@/components/StatCard.vue'
import { analyticsApi } from '@/api/analytics'
import { catalogApi } from '@/api/catalog'
import { getApiErrorMessage } from '@/api/client'
import { reviewApi } from '@/api/review'
import { useAuthStore } from '@/stores/auth'
import type { TrendPoint } from '@/types/analytics'
import type { TodayReview } from '@/types/review'

const auth = useAuthStore()
const contentSummary = ref('—')
const algorithmCount = ref(0)
const taskCount = ref(0)
const today = ref<TodayReview | null>(null)
const heatmapPoints = ref<TrendPoint[]>([])
const heatmapLoading = ref(true)
const heatmapError = ref<string | null>(null)

async function loadHeatmap(): Promise<void> {
  heatmapLoading.value = true
  heatmapError.value = null
  try {
    const data = await analyticsApi.trends(365)
    heatmapPoints.value = data.points
  } catch (err) {
    heatmapError.value = getApiErrorMessage(err)
  } finally {
    heatmapLoading.value = false
  }
}

const trainingTypes = [
  {
    title: '算法识别',
    description: '根据题意、数据范围与复杂度判断适用算法。',
    to: '/practice?type=recognition',
  },
  {
    title: '模板复现',
    description: '不看参考代码，独立写出基础模板。',
    to: '/practice?type=template',
  },
  {
    title: '变体复现',
    description: '完成路径恢复、区间修改等算法变化。',
    to: '/practice?type=variant',
  },
  {
    title: '针对性纠错',
    description: '训练边界、初始化、溢出、越界与逻辑错误。',
    to: '/practice?type=correction',
  },
]

const dueProgress = computed(() =>
  Math.min(100, ((today.value?.due_count ?? 0) / 10) * 100),
)

const todayLabel = computed(() =>
  new Date().toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    weekday: 'short',
  }),
)

onMounted(async () => {
  void loadHeatmap()

  try {
    const [algorithms, tasks] = await Promise.all([
      catalogApi.algorithms(),
      catalogApi.tasks(),
    ])
    algorithmCount.value = algorithms.length
    taskCount.value = tasks.length
    contentSummary.value = `${algorithms.length} 算法 · ${tasks.length} 任务`
  } catch {
    contentSummary.value = '暂不可用'
  }

  try {
    today.value = await reviewApi.today()
  } catch {
    today.value = null
  }
})
</script>

<template>
  <section class="dashboard-hero">
    <div class="hero-copy">
      <span class="eyebrow">MOMOCODE / {{ todayLabel }}</span>
      <h1>训练<span>脉冲</span></h1>
      <p>
        <template v-if="today">
          今日有 <strong>{{ today.due_count }}</strong> 个技能到期，已完成
          <strong>{{ today.reviewed_today }}</strong> 次复习。保持节奏，继续推进。
        </template>
        <template v-else>
          欢迎回来，{{ auth.user?.displayName ?? '同学' }}。现在可以浏览算法库并开始自由练习。
        </template>
      </p>
      <div class="hero-actions">
        <RouterLink class="btn btn-primary" to="/review">
          进入复习队列 <span aria-hidden="true">→</span>
        </RouterLink>
        <RouterLink class="btn btn-ghost" to="/practice">自由练习</RouterLink>
      </div>
    </div>

    <div
      class="hero-gauge"
      :style="{ '--progress': `${dueProgress}%` }"
      aria-label="今日到期技能数"
    >
      <div class="hero-gauge-inner">
        <span class="hero-gauge-label">当前到期</span>
        <strong>{{ today?.due_count ?? '—' }}</strong>
        <span class="hero-gauge-hint">
          {{ today?.overdue_count ?? 0 }} 个逾期
        </span>
      </div>
    </div>

    <div class="hero-footer">
      <span>内容 / {{ contentSummary }}</span>
      <span>已复习 / {{ today?.reviewed_today ?? 0 }}</span>
      <span>时区 / {{ today?.timezone ?? 'UTC' }}</span>
    </div>
  </section>

  <div class="stat-grid">
    <StatCard
      label="今日待复习"
      :value="today ? String(today.due_count) : '—'"
      :hint="today ? `${today.overdue_count} 个逾期 · ${today.timezone}` : 'FSRS 到期队列'"
    />
    <StatCard
      label="今日已复习"
      :value="today ? String(today.reviewed_today) : '—'"
      hint="正式复习记录"
    />
    <StatCard
      label="内容任务"
      :value="taskCount ? String(taskCount) : '—'"
      :hint="`${algorithmCount} 个算法 · 40 个技能`"
    />
  </div>

  <section class="card" style="margin-top: 16px">
    <div class="section-heading">
      <div>
        <span class="eyebrow">训练记录</span>
        <h2>训练热力图</h2>
      </div>
      <span class="badge">过去一年</span>
    </div>
    <div v-if="heatmapLoading" class="stat-hint">正在加载训练记录…</div>
    <div v-else-if="heatmapError" class="notice" role="alert">
      {{ heatmapError }}
      <button class="btn btn-ghost" type="button" @click="loadHeatmap">重试</button>
    </div>
    <ActivityHeatmap v-else :points="heatmapPoints" />
  </section>

  <section class="card training-section">
    <div class="section-heading">
      <div>
        <span class="eyebrow">训练方式</span>
        <h2>训练模式</h2>
      </div>
      <RouterLink class="btn btn-ghost" to="/library">浏览算法库</RouterLink>
    </div>

    <div class="training-grid">
      <RouterLink
        v-for="(item, index) in trainingTypes"
        :key="item.title"
        class="training-card"
        :to="item.to"
      >
        <span class="training-index">0{{ index + 1 }}</span>
        <span class="training-body">
          <strong>{{ item.title }}</strong>
          <span>{{ item.description }}</span>
        </span>
        <span class="training-arrow" aria-hidden="true">↗</span>
      </RouterLink>
    </div>
  </section>
</template>
