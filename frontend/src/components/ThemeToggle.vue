<script setup lang="ts">
import { computed } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { mode, cycleTheme } = useTheme()

const label = computed(() => {
  if (mode.value === 'light') return '浅色'
  if (mode.value === 'dark') return '深色'
  return '跟随系统'
})

const shortLabel = computed(() => {
  if (mode.value === 'light') return '浅色'
  if (mode.value === 'dark') return '深色'
  return '跟随'
})

const glyph = computed(() => {
  if (mode.value === 'light') return '☼'
  if (mode.value === 'dark') return '◐'
  return '◑'
})
</script>

<template>
  <button
    class="btn btn-ghost theme-toggle"
    type="button"
    :aria-label="`切换主题，当前${label}`"
    :title="`主题：${label}`"
    @click="cycleTheme"
  >
    <span class="theme-glyph" aria-hidden="true">{{ glyph }}</span>
    <span>{{ shortLabel }}</span>
  </button>
</template>

<style scoped>
.theme-glyph {
  color: var(--accent);
  font-size: 13px;
  line-height: 1;
}
</style>
