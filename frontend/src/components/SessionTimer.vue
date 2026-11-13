<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps<{
  startedAt: string | null
}>()

const now = ref(Date.now())
let timer: number | undefined

onMounted(() => {
  timer = window.setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onBeforeUnmount(() => {
  if (timer !== undefined) {
    window.clearInterval(timer)
  }
})

const elapsed = computed(() => {
  if (!props.startedAt) return '00:00'
  const started = new Date(props.startedAt).getTime()
  if (Number.isNaN(started)) return '00:00'
  const totalSeconds = Math.max(0, Math.floor((now.value - started) / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
})
</script>

<template>
  <span class="badge" role="timer" aria-label="已用时间">{{ elapsed }}</span>
</template>
