<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getHealth } from '@/api/health'

type HealthState = 'loading' | 'ok' | 'error'

const state = ref<HealthState>('loading')
const message = ref('正在检查 API')

async function check(): Promise<void> {
  state.value = 'loading'
  message.value = '正在检查 API'

  try {
    const result = await getHealth()
    state.value = result.status === 'ok' ? 'ok' : 'error'
    message.value = result.status === 'ok' ? 'API 正常' : 'API 状态异常'
  } catch {
    state.value = 'error'
    message.value = 'API 不可达'
  }
}

onMounted(check)

defineExpose({ check })
</script>

<template>
  <span
    class="badge"
    :class="{
      'badge-success': state === 'ok',
      'badge-danger': state === 'error',
    }"
    role="status"
    aria-live="polite"
  >
    {{ message }}
  </span>
</template>
