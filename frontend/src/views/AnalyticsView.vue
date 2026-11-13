<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import type { EChartsOption } from 'echarts'
import PageHeader from '@/components/PageHeader.vue'
import LoadingState from '@/components/LoadingState.vue'
import ErrorState from '@/components/ErrorState.vue'
import EmptyState from '@/components/EmptyState.vue'
import StatCard from '@/components/StatCard.vue'
import EChart from '@/components/EChart.vue'
import { analyticsApi } from '@/api/analytics'
import { getApiErrorMessage } from '@/api/client'
import { useTheme } from '@/composables/useTheme'
import type {
  ErrorDistributionItem,
  ForgettingCurve,
  MetricDefinition,
  Overview,
  SkillStat,
  Trends,
} from '@/types/analytics'

const days = ref(30)
const { resolved } = useTheme()
const chartText = computed(() => (resolved.value === 'dark' ? '#9aa1ab' : '#5d626a'))
const chartGrid = computed(() => (resolved.value === 'dark' ? '#242a31' : '#e4e1dd'))
const chartColors = computed(() =>
  resolved.value === 'dark' ? ['#ff6a2a', '#8b93a1'] : ['#e6531b', '#6b7280'],
)
const tooltipStyle = computed(() => ({
  backgroundColor: resolved.value === 'dark' ? '#15181c' : '#ffffff',
  borderColor: resolved.value === 'dark' ? '#2a2f36' : '#e4e1dd',
  textStyle: { color: resolved.value === 'dark' ? '#f2f4f7' : '#1e2024' },
}))
const overview = ref<Overview | null>(null)
const trends = ref<Trends | null>(null)
const forgetting = ref<ForgettingCurve | null>(null)
const errors = ref<ErrorDistributionItem[]>([])
const skills = ref<SkillStat[]>([])
const definitions = ref<MetricDefinition[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const typeLabels: Record<string, string> = {
  recognition: '识别',
  template: '模板',
  variant: '变体',
  correction: '纠错',
}

function percent(value: number | null): string {
  return value === null ? '—' : `${(value * 100).toFixed(1)}%`
}

function fixed(value: number | null, digits = 2): string {
  return value === null ? '—' : value.toFixed(digits)
}

function scoreValue(value: number | null): string {
  return value === null ? '—' : value.toFixed(1)
}

const hasSessions = computed(() => (overview.value?.sessions_completed ?? 0) > 0)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [overviewData, trendData, errorData, skillData, definitionData, forgettingData] =
      await Promise.all([
        analyticsApi.overview(days.value),
        analyticsApi.trends(days.value),
        analyticsApi.errors(days.value),
        analyticsApi.skills(days.value),
        analyticsApi.definitions(),
        analyticsApi.forgettingCurve(30),
      ])
    overview.value = overviewData
    trends.value = trendData
    errors.value = errorData
    skills.value = skillData
    definitions.value = definitionData
    forgetting.value = forgettingData
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

watch(days, load)
onMounted(load)

const trendOption = computed<EChartsOption>(() => {
  const points = trends.value?.points ?? []
  return {
    color: chartColors.value,
    textStyle: { color: chartText.value },
    tooltip: { trigger: 'axis', ...tooltipStyle.value },
    legend: { data: ['正确率', '独立比例'], textStyle: { color: chartText.value } },
    grid: { left: 48, right: 20, top: 42, bottom: 36 },
    xAxis: {
      type: 'category',
      data: points.map((point) => point.date.slice(5)),
      axisLabel: {
        color: chartText.value,
        interval: Math.max(0, Math.floor(points.length / 8) - 1),
      },
      axisLine: { lineStyle: { color: chartGrid.value } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value}%', color: chartText.value },
      splitLine: { lineStyle: { color: chartGrid.value } },
    },
    series: [
      {
        name: '正确率',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: points.map((point) =>
          point.correctness_rate === null
            ? null
            : Number((point.correctness_rate * 100).toFixed(1)),
        ),
      },
      {
        name: '独立比例',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: points.map((point) =>
          point.independent_rate === null
            ? null
            : Number((point.independent_rate * 100).toFixed(1)),
        ),
      },
    ],
  }
})

const typeOption = computed<EChartsOption>(() => {
  const items = overview.value?.training_types ?? []
  return {
    color: chartColors.value,
    textStyle: { color: chartText.value },
    tooltip: { trigger: 'axis', ...tooltipStyle.value },
    grid: { left: 48, right: 20, top: 24, bottom: 36 },
    xAxis: {
      type: 'category',
      data: items.map((item) => typeLabels[item.training_type] ?? item.training_type),
      axisLabel: { color: chartText.value },
      axisLine: { lineStyle: { color: chartGrid.value } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: chartText.value },
      splitLine: { lineStyle: { color: chartGrid.value } },
    },
    series: [
      {
        type: 'bar',
        name: '完成次数',
        data: items.map((item) => item.sessions),
        barMaxWidth: 36,
      },
    ],
  }
})

const errorOption = computed<EChartsOption>(() => ({
  color: chartColors.value,
  textStyle: { color: chartText.value },
  tooltip: { trigger: 'axis', ...tooltipStyle.value },
  grid: { left: 80, right: 20, top: 24, bottom: 36 },
  xAxis: {
    type: 'value',
    minInterval: 1,
    axisLabel: { color: chartText.value },
    splitLine: { lineStyle: { color: chartGrid.value } },
  },
  yAxis: {
    type: 'category',
    data: errors.value.map((item) => item.error_type),
    axisLabel: { color: chartText.value },
    axisLine: { lineStyle: { color: chartGrid.value } },
  },
  series: [
    {
      type: 'bar',
      name: '次数',
      data: errors.value.map((item) => item.count),
      barMaxWidth: 24,
    },
  ],
}))

const forgettingOption = computed<EChartsOption>(() => {
  const curve = forgetting.value
  const points = curve?.points ?? []
  return {
    color: chartColors.value,
    textStyle: { color: chartText.value },
    tooltip: { trigger: 'axis', ...tooltipStyle.value },
    legend: {
      data: ['Fibonacci 计划', '我的曲线'],
      textStyle: { color: chartText.value },
    },
    grid: { left: 48, right: 24, top: 42, bottom: 36 },
    xAxis: {
      type: 'category',
      name: '距上次复习天数',
      nameTextStyle: { color: chartText.value },
      data: points.map((point) => point.day),
      axisLabel: { color: chartText.value },
      axisLine: { lineStyle: { color: chartGrid.value } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value}%', color: chartText.value },
      splitLine: { lineStyle: { color: chartGrid.value } },
    },
    series: [
      {
        name: 'Fibonacci 计划',
        type: 'line',
        smooth: false,
        showSymbol: false,
        data: points.map((point) => Number((point.fibonacci_retention * 100).toFixed(1))),
        lineStyle: { width: 2 },
        markLine: {
          silent: true,
          symbol: 'none',
          label: { show: false },
          lineStyle: { color: chartGrid.value, type: 'dashed' },
          data: (curve?.fibonacci_review_days ?? []).map((day) => ({
            xAxis: day,
          })),
        },
      },
      {
        name: '我的曲线',
        type: 'line',
        smooth: true,
        showSymbol: false,
        connectNulls: false,
        data: points.map((point) =>
          point.my_retention === null ? null : Number((point.my_retention * 100).toFixed(1)),
        ),
        lineStyle: { width: 2 },
      },
    ],
  }
})
</script>

<template>
  <PageHeader
    title="分析"
    description="按训练类型、技能与时间范围查看表现；每个指标都标注口径、来源与样本量。"
  >
    <template #actions>
      <RouterLink class="btn btn-ghost" to="/practice">继续训练</RouterLink>
    </template>
  </PageHeader>

  <div class="card" style="margin-bottom: 16px">
    <div class="topbar-actions" style="justify-content: space-between; flex-wrap: wrap">
      <div class="topbar-actions">
        <button
          v-for="option in [7, 30, 90]"
          :key="option"
          class="btn"
          :class="{ 'btn-primary': days === option }"
          type="button"
          @click="days = option"
        >
          {{ option }} 天
        </button>
      </div>
      <span class="badge">
        样本量 {{ overview?.sample_size ?? 0 }}
        <template v-if="overview?.insufficient_data">· 样本不足</template>
      </span>
    </div>
  </div>

  <LoadingState v-if="loading" />
  <ErrorState v-else-if="error" :message="error" @retry="load" />
  <template v-else>
    <div class="notice notice-accent" style="margin-bottom: 16px">
      耗时按训练类型与难度相对个人历史基准归一化，不做跨算法绝对比较；技能分数不是 FSRS 难度。
    </div>

    <div v-if="overview?.insufficient_data" class="notice" style="margin-bottom: 16px">
      当前时间范围样本不足（少于 3 次），部分指标仅作参考，技能分数显示为空。
    </div>

    <section class="card" style="margin-bottom: 16px">
      <div class="topbar-actions" style="justify-content: space-between">
        <div>
          <span class="eyebrow">Memory decay</span>
          <h2>遗忘曲线对比</h2>
        </div>
        <span class="badge"> Fibonacci vs 我的 FSRS </span>
      </div>
      <div class="topbar-actions" style="margin-top: 12px; flex-wrap: wrap">
        <span class="badge"> Fibonacci：{{ forgetting?.fibonacci_intervals.join(' / ') }} 天 </span>
        <span class="badge">样本技能 {{ forgetting?.sample_size ?? 0 }}</span>
        <span class="badge">
          我的平均稳定度
          {{
            forgetting?.avg_stability_days ? `${forgetting.avg_stability_days.toFixed(1)} 天` : '—'
          }}
        </span>
      </div>
      <p style="color: var(--text-muted); margin-top: 10px">
        Fibonacci 计划按 1/1/2/3/5/8/13/21 天复习，虚线为复习节点；我的曲线取当前技能 FSRS
        稳定度均值。样本不足时仅作参考。
      </p>
      <EChart v-if="forgetting?.points.length" :option="forgettingOption" height="320px" />
      <p v-else style="color: var(--text-subtle); margin-top: 12px">暂无个人遗忘曲线数据。</p>
    </section>

    <div v-if="hasSessions" class="stat-grid">
      <StatCard
        label="完成训练"
        :value="String(overview?.sessions_completed ?? 0)"
        hint="所选时间范围"
      />
      <StatCard
        label="正确率"
        :value="percent(overview?.correctness_rate ?? null)"
        hint="自动判题 / 识别判分"
      />
      <StatCard
        label="独立完成"
        :value="percent(overview?.independent_rate ?? null)"
        hint="最高提示 ≤1"
      />
      <StatCard
        label="提示依赖"
        :value="fixed(overview?.hint_dependency ?? null)"
        hint="平均最高提示 / 5"
      />
      <StatCard
        label="归一化耗时"
        :value="`${fixed(overview?.avg_normalized_time ?? null)}×`"
        hint="相对个人基准"
      />
      <StatCard label="今日到期" :value="String(overview?.due_count ?? 0)" hint="FSRS 队列" />
    </div>

    <EmptyState
      v-else
      title="当前时间范围没有完成记录"
      description="完成一次训练后，这里会展示正确率、独立程度、提示依赖和趋势。"
    >
      <RouterLink class="btn btn-primary" to="/practice">开始训练</RouterLink>
    </EmptyState>

    <div v-if="hasSessions" class="grid grid-2" style="margin-top: 16px">
      <section class="card">
        <h2>正确率与独立比例趋势</h2>
        <EChart :option="trendOption" height="300px" />
      </section>
      <section class="card">
        <h2>训练类型分布</h2>
        <EChart :option="typeOption" height="300px" />
      </section>
      <section class="card">
        <h2>错误类型分布</h2>
        <EChart v-if="errors.length" :option="errorOption" height="280px" />
        <p v-else style="color: var(--text-muted); margin-top: 12px">
          当前时间范围没有记录错误类型。
        </p>
      </section>
      <section class="card">
        <h2>复习状态</h2>
        <div class="topbar-actions" style="margin-top: 12px; flex-wrap: wrap">
          <span class="badge">今日到期 {{ overview?.due_count ?? 0 }}</span>
          <span class="badge">已复习 {{ overview?.reviewed_count ?? 0 }}</span>
        </div>
        <p style="color: var(--text-muted); margin-top: 12px">
          FSRS 只负责复习调度；技能分数与 FSRS 难度分开展示。
        </p>
      </section>
    </div>

    <section v-if="skills.length" class="card" style="margin-top: 16px">
      <h2>技能表现</h2>
      <div class="data-table">
        <div class="data-row data-head">
          <span>技能</span>
          <span>技能分数</span>
          <span>样本</span>
          <span>正确率</span>
          <span>独立比例</span>
          <span>提示依赖</span>
        </div>
        <div v-for="skill in skills" :key="skill.skill_id" class="data-row">
          <span>
            <strong>{{ skill.skill_name }}</strong>
            <span style="color: var(--text-muted)"> · {{ skill.algorithm_name }}</span>
          </span>
          <span>
            {{ scoreValue(skill.skill_score) }}
            <span v-if="skill.insufficient_data" class="badge">样本不足</span>
            <span v-else-if="skill.sample_size < 10" class="badge">初步数据</span>
          </span>
          <span>{{ skill.sample_size }}</span>
          <span>{{ percent(skill.correctness_rate) }}</span>
          <span>{{ percent(skill.independence_score) }}</span>
          <span>{{ fixed(skill.hint_dependency) }}</span>
        </div>
      </div>
    </section>

    <section class="card" style="margin-top: 16px">
      <h2>指标定义</h2>
      <div class="grid grid-2" style="margin-top: 12px">
        <article v-for="definition in definitions" :key="definition.key" class="card card-muted">
          <h3>{{ definition.name }}</h3>
          <p style="color: var(--text-muted); margin-top: 4px">{{ definition.formula }}</p>
          <p style="color: var(--text-subtle); margin-top: 8px; font-size: 12px">
            来源：{{ definition.source }} · 范围：{{ definition.time_range }}
          </p>
          <p style="color: var(--text-subtle); margin-top: 4px; font-size: 12px">
            {{ definition.notes }}
          </p>
        </article>
      </div>
    </section>
  </template>
</template>
