<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import {
  AxisPointerComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { useTheme } from '@/composables/useTheme'

echarts.use([
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  AxisPointerComponent,
  CanvasRenderer,
])

const props = withDefaults(
  defineProps<{
    option: EChartsOption
    height?: string
  }>(),
  {
    height: '320px',
  },
)

const { resolved } = useTheme()
const container = ref<HTMLElement | null>(null)
let chart: ReturnType<typeof echarts.init> | null = null

function render(): void {
  if (!container.value) return
  chart?.dispose()
  chart = echarts.init(
    container.value,
    resolved.value === 'dark' ? 'dark' : undefined,
    { renderer: 'canvas' },
  )
  chart.setOption(props.option)
}

function handleResize(): void {
  chart?.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', handleResize)
})

watch(
  () => props.option,
  (option) => {
    chart?.setOption(option, true)
  },
  { deep: true },
)

watch(resolved, render)

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="container" :style="{ width: '100%', height: props.height }" />
</template>
