<script setup lang="ts">
import type { TaskSummary } from '@/types/catalog'

const props = withDefaults(
  defineProps<{
    task: TaskSummary
    actionLabel?: string
    deletable?: boolean
  }>(),
  {
    actionLabel: '开始练习',
    deletable: false,
  },
)

const emit = defineEmits<{
  start: [task: TaskSummary]
  delete: [task: TaskSummary]
}>()

const typeLabels: Record<string, string> = {
  recognition: '识别',
  template: '模板',
  variant: '变体',
  correction: '纠错',
}

const platformLabels: Record<string, string> = {
  codeforces: 'Codeforces',
  luogu: '洛谷',
  atcoder: 'AtCoder',
  other: '其他',
}
</script>

<template>
  <article class="card">
    <div class="topbar-actions" style="justify-content: space-between">
      <h3>{{ props.task.title }}</h3>
      <div class="topbar-actions" style="flex-wrap: wrap">
        <span v-if="props.task.source_type === 'user'" class="badge badge-accent">自建</span>
        <span class="badge badge-accent">
          {{ typeLabels[props.task.training_type] ?? props.task.training_type }}
        </span>
      </div>
    </div>

    <div class="topbar-actions" style="margin-top: 8px; flex-wrap: wrap">
      <span class="badge">难度 {{ props.task.difficulty }}</span>
      <span class="badge">{{ props.task.language }}</span>
      <span v-if="props.task.oj_platform" class="badge">
        {{ platformLabels[props.task.oj_platform] ?? props.task.oj_platform }}
      </span>
    </div>

    <div
      v-if="props.task.tags.length"
      class="topbar-actions"
      style="margin-top: 8px; flex-wrap: wrap"
    >
      <span v-for="tag in props.task.tags" :key="tag" class="badge badge-accent">
        #{{ tag }}
      </span>
    </div>

    <p
      v-if="props.task.target_skills.length"
      style="color: var(--text-muted); margin-top: 8px"
    >
      目标技能：{{ props.task.target_skills.map((skill) => skill.name).join('、') }}
    </p>

    <div class="topbar-actions" style="margin-top: 12px; flex-wrap: wrap">
      <button class="btn btn-ghost" type="button" @click="emit('start', props.task)">
        {{ props.actionLabel }}
      </button>
      <button
        v-if="props.deletable"
        class="btn btn-ghost"
        type="button"
        @click="emit('delete', props.task)"
      >
        删除
      </button>
    </div>
  </article>
</template>
