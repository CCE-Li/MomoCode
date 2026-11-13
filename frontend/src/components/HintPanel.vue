<script setup lang="ts">
import type { HintUsed } from '@/types/practice'

const props = withDefaults(
  defineProps<{
    maxHintLevel: number
    hintsUsed: HintUsed[]
    loading?: boolean
  }>(),
  {
    loading: false,
  },
)

const emit = defineEmits<{
  request: [level: number]
}>()

function used(level: number): HintUsed | undefined {
  return props.hintsUsed.find((hint) => hint.level === level)
}
</script>

<template>
  <section class="card">
    <div class="topbar-actions" style="justify-content: space-between">
      <h2>提示</h2>
      <span class="badge">最高 {{ props.maxHintLevel }} 级</span>
    </div>
    <p style="color: var(--text-muted); margin-top: 4px">
      提示会记录为独立程度证据；使用后不可撤销。
    </p>

    <div class="topbar-actions" style="margin-top: 12px; flex-wrap: wrap">
      <button
        v-for="level in props.maxHintLevel"
        :key="level"
        class="btn btn-ghost"
        type="button"
        :disabled="props.loading"
        @click="emit('request', level)"
      >
        {{ level }} 级{{ used(level) ? '（已用）' : '' }}
      </button>
    </div>

    <div
      v-for="hint in props.hintsUsed"
      :key="hint.level"
      class="notice"
      style="margin-top: 12px"
    >
      <div>
        <strong>{{ hint.level }} 级提示</strong>
        <div style="white-space: pre-wrap">{{ hint.content }}</div>
      </div>
    </div>
  </section>
</template>
