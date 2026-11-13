<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { buildGalaxy } from '@/lib/galaxy'
import type { GalaxySkillStar } from '@/types/galaxy'

const props = defineProps<{
  skills: GalaxySkillStar[]
  progress: number
  active: boolean
}>()

const TAU = Math.PI * 2
const canvas = ref<HTMLCanvasElement | null>(null)
const layout = computed(() => buildGalaxy(props.skills))
const display = new Map<string, number>()
let context: CanvasRenderingContext2D | null = null
let frame = 0
let width = 0
let height = 0
let observer: ResizeObserver | null = null
let reducedMotion = false

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value))
}

function colorFor(tone: 'warm' | 'cool', alpha: number): string {
  return tone === 'warm'
    ? `rgba(255, 184, 120, ${alpha})`
    : `rgba(158, 184, 222, ${alpha})`
}

function resize(): void {
  const element = canvas.value
  if (!element) return
  const rect = element.getBoundingClientRect()
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  width = Math.max(1, rect.width)
  height = Math.max(1, rect.height)
  element.width = Math.round(width * dpr)
  element.height = Math.round(height * dpr)
  context = element.getContext('2d')
  context?.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function drawDiamond(
  x: number,
  y: number,
  size: number,
  tone: 'warm' | 'cool',
  alpha: number,
  filled: boolean,
): void {
  if (!context || alpha <= 0.002) return
  const ctx = context
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(Math.PI / 4)
  const half = size / 2
  ctx.globalAlpha = alpha
  if (filled) {
    ctx.fillStyle = colorFor(tone, 1)
    ctx.fillRect(-half, -half, size, size)
  } else {
    ctx.strokeStyle = colorFor(tone, 1)
    ctx.lineWidth = 1
    ctx.strokeRect(-half, -half, size, size)
  }
  ctx.restore()
}

function draw(now: number): void {
  if (!context) return
  const ctx = context
  ctx.clearRect(0, 0, width, height)

  const radius = Math.min(width, height) * 0.46
  const centerX = width / 2
  const centerY = height / 2
  const scale = Math.min(width, height) / 520

  const vignette = ctx.createRadialGradient(
    centerX,
    centerY,
    radius * 0.05,
    centerX,
    centerY,
    radius * 1.15,
  )
  vignette.addColorStop(0, `rgba(255, 150, 80, ${0.015 + props.progress * 0.05})`)
  vignette.addColorStop(1, 'rgba(0, 0, 0, 0)')
  ctx.fillStyle = vignette
  ctx.fillRect(0, 0, width, height)

  ctx.lineWidth = 1
  for (const ring of layout.value.rings) {
    ctx.strokeStyle = 'rgba(205, 218, 240, 0.055)'
    ctx.beginPath()
    ctx.arc(centerX, centerY, ring * radius, 0, TAU)
    ctx.stroke()
  }

  for (let index = 0; index < layout.value.spokes; index += 1) {
    const angle = (index / layout.value.spokes) * TAU
    const cos = Math.cos(angle)
    const sin = Math.sin(angle)
    ctx.strokeStyle = 'rgba(205, 218, 240, 0.022)'
    ctx.beginPath()
    ctx.moveTo(centerX + cos * radius * 0.24, centerY + sin * radius * 0.24)
    ctx.lineTo(centerX + cos * radius * 0.82, centerY + sin * radius * 0.82)
    ctx.stroke()

    ctx.strokeStyle = 'rgba(205, 218, 240, 0.06)'
    ctx.beginPath()
    ctx.moveTo(centerX + cos * radius * 0.82, centerY + sin * radius * 0.82)
    ctx.lineTo(centerX + cos * radius * 0.845, centerY + sin * radius * 0.845)
    ctx.stroke()
  }

  const start = -Math.PI / 2
  ctx.lineWidth = 2
  ctx.strokeStyle = 'rgba(255, 140, 80, 0.12)'
  ctx.beginPath()
  ctx.arc(centerX, centerY, radius * 0.19, 0, TAU)
  ctx.stroke()
  if (props.progress > 0) {
    ctx.strokeStyle = 'rgba(255, 150, 90, 0.65)'
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius * 0.19, start, start + props.progress * TAU)
    ctx.stroke()
  }

  ctx.strokeStyle = 'rgba(255, 190, 140, 0.75)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(centerX - 6 * scale, centerY)
  ctx.lineTo(centerX + 6 * scale, centerY)
  ctx.moveTo(centerX, centerY - 6 * scale)
  ctx.lineTo(centerX, centerY + 6 * scale)
  ctx.stroke()
  ctx.fillStyle = 'rgba(255, 180, 120, 0.85)'
  ctx.beginPath()
  ctx.arc(centerX, centerY, 2 * scale, 0, TAU)
  ctx.fill()

  const rotation = reducedMotion ? 0 : now * 0.000006
  ctx.save()
  ctx.translate(centerX, centerY)
  ctx.rotate(rotation)
  ctx.translate(-centerX, -centerY)

  for (const cluster of layout.value.clusters) {
    const px = centerX + cluster.x * radius
    const py = centerY + cluster.y * radius
    const target = cluster.state === 'lit' ? Math.max(0.4, cluster.brightness) : 0.2
    const previous = display.get(cluster.key) ?? 0
    const value = reducedMotion ? target : previous + (target - previous) * 0.06
    display.set(cluster.key, value)
    const warm = cluster.state === 'lit'
    const pulse = reducedMotion ? 1 : 0.9 + 0.1 * Math.sin(now * 0.0011 + cluster.angle)

    ctx.lineWidth = warm ? 1 : 0.8
    ctx.strokeStyle = warm
      ? `rgba(255, 176, 112, ${0.18 + value * 0.22})`
      : 'rgba(150, 176, 214, 0.1)'
    ctx.beginPath()
    cluster.satellites.forEach((satellite, index) => {
      const sx = px + satellite.dx * radius
      const sy = py + satellite.dy * radius
      if (index === 0) ctx.moveTo(sx, sy)
      else ctx.lineTo(sx, sy)
    })
    ctx.closePath()
    ctx.stroke()

    for (const satellite of cluster.satellites) {
      const sx = px + satellite.dx * radius
      const sy = py + satellite.dy * radius
      const size = (warm ? 1.4 + value * 2.6 : 1.1) * (0.6 + satellite.size * 0.5) * scale
      const alpha = warm ? clamp01(value * pulse) : 0.28
      drawDiamond(sx, sy, size, warm ? 'warm' : 'cool', alpha, warm)
    }

    if (warm) {
      ctx.strokeStyle = `rgba(255, 160, 100, ${0.08 + value * 0.14})`
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.arc(px, py, (5 + value * 5) * scale, 0, TAU)
      ctx.stroke()
    }
  }

  for (const node of layout.value.residual) {
    const px = centerX + node.x * radius
    const py = centerY + node.y * radius
    const pulse = reducedMotion ? 1 : 0.85 + 0.15 * Math.sin(now * 0.0008 + node.phase)
    const alpha = clamp01(node.brightness * pulse)
    drawDiamond(px, py, (1.1 + node.brightness * 2.4) * scale, node.tone, alpha, true)
  }

  ctx.restore()
}

function tick(now: number): void {
  draw(now)
  frame = requestAnimationFrame(tick)
}

function start(): void {
  if (!frame) frame = requestAnimationFrame(tick)
}

function stop(): void {
  if (frame) {
    cancelAnimationFrame(frame)
    frame = 0
  }
}

function renderOnce(): void {
  if (reducedMotion) draw(performance.now())
}

function handleVisibility(): void {
  if (document.hidden) stop()
  else if (props.active) start()
}

onMounted(() => {
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  resize()
  const element = canvas.value
  if (element) {
    observer = new ResizeObserver(() => {
      resize()
      renderOnce()
    })
    observer.observe(element)
  }

  if (props.active && !reducedMotion) start()
  else renderOnce()
  document.addEventListener('visibilitychange', handleVisibility)
})

watch(
  () => props.active,
  (active) => {
    if (active) {
      resize()
      if (reducedMotion) renderOnce()
      else start()
    } else {
      stop()
    }
  },
)

watch(layout, () => renderOnce())

onBeforeUnmount(() => {
  stop()
  observer?.disconnect()
  document.removeEventListener('visibilitychange', handleVisibility)
  context = null
})
</script>

<template>
  <canvas ref="canvas" class="galaxy-canvas" aria-hidden="true" />
</template>

<style scoped>
.galaxy-canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
