<script setup lang="ts">
import {
  computed,
  defineAsyncComponent,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue'
import { galaxyApi } from '@/api/galaxy'
import { getApiErrorMessage } from '@/api/client'
import type { GalaxyResponse } from '@/types/galaxy'

const GalaxyScene = defineAsyncComponent(() => import('./GalaxyScene.vue'))

const open = defineModel<boolean>('open', { default: false })

const progress = ref(0)
const dragging = ref(false)
const settling = ref(false)
const atTop = ref(true)
const data = ref<GalaxyResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const closeButton = ref<HTMLButtonElement | null>(null)

const visible = computed(
  () => open.value || progress.value > 0 || settling.value,
)

let startY = 0
let startProgress = 0
let settleTimer: number | undefined
let lastLoadedAt = 0
let wheelGesture = false
let wheelTimer: number | undefined
let previousFocus: HTMLElement | null = null
let previousBodyOverflow = ''
let previousBodyPaddingRight = ''

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value))
}

async function refresh(): Promise<void> {
  if (loading.value) return
  loading.value = true
  error.value = null
  try {
    data.value = await galaxyApi.get()
    lastLoadedAt = Date.now()
  } catch (err) {
    error.value = getApiErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function requestData(): void {
  if (!data.value || Date.now() - lastLoadedAt > 15_000) void refresh()
}

function lockBody(): void {
  previousBodyOverflow = document.body.style.overflow
  previousBodyPaddingRight = document.body.style.paddingRight
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
  document.body.style.overflow = 'hidden'
  if (scrollbarWidth > 0) {
    document.body.style.paddingRight = `${scrollbarWidth}px`
  }
}

function unlockBody(): void {
  document.body.style.overflow = previousBodyOverflow
  document.body.style.paddingRight = previousBodyPaddingRight
}

function cancelWheelGesture(): void {
  wheelGesture = false
  if (wheelTimer !== undefined) {
    window.clearTimeout(wheelTimer)
    wheelTimer = undefined
  }
}

function settleTo(target: boolean): void {
  cancelWheelGesture()
  settling.value = true
  if (target) {
    if (!open.value) progress.value = 0.002
    open.value = true
    window.requestAnimationFrame(() => {
      progress.value = 1
    })
  } else {
    open.value = false
    progress.value = 0
  }
  if (settleTimer !== undefined) window.clearTimeout(settleTimer)
  settleTimer = window.setTimeout(() => {
    settling.value = false
  }, 340)
}

function close(): void {
  settleTo(false)
}

function startDrag(event: PointerEvent): void {
  if (event.button !== 0) return
  event.preventDefault()
  cancelWheelGesture()
  requestData()
  dragging.value = true
  settling.value = false
  startY = event.clientY
  startProgress = open.value ? 1 : progress.value
  const handle = event.currentTarget
  if (handle instanceof HTMLElement) {
    handle.setPointerCapture?.(event.pointerId)
  }
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp, { once: true })
  window.addEventListener('pointercancel', onPointerUp, { once: true })
}

function onPointerMove(event: PointerEvent): void {
  if (!dragging.value) return
  const delta = (event.clientY - startY) / Math.max(1, window.innerHeight)
  progress.value = clamp01(startProgress + delta)
}

function onPointerUp(): void {
  if (!dragging.value) return
  dragging.value = false
  window.removeEventListener('pointermove', onPointerMove)
  const shouldOpen =
    startProgress === 1 ? progress.value > 0.65 : progress.value > 0.3
  settleTo(shouldOpen)
}

function finishWheelGesture(): void {
  if (!wheelGesture) return
  wheelGesture = false
  wheelTimer = undefined

  if (progress.value <= 0.001) {
    open.value = false
    progress.value = 0
    settling.value = false
    if (settleTimer !== undefined) {
      window.clearTimeout(settleTimer)
      settleTimer = undefined
    }
    return
  }

  settleTo(progress.value >= 0.3)
}

function handleWheel(event: WheelEvent): void {
  if (event.ctrlKey) return
  if (open.value) return

  if (!wheelGesture) {
    if (window.scrollY > 0) return
    if (event.deltaY >= 0) return
    wheelGesture = true
    settling.value = false
    if (settleTimer !== undefined) {
      window.clearTimeout(settleTimer)
      settleTimer = undefined
    }
    requestData()
  }

  progress.value = clamp01(
    progress.value - event.deltaY / Math.max(1, window.innerHeight),
  )
  event.preventDefault()
  event.stopPropagation()
  if (wheelTimer !== undefined) window.clearTimeout(wheelTimer)
  wheelTimer = window.setTimeout(finishWheelGesture, 180)
}

function handleKey(event: KeyboardEvent): void {
  if (event.key === 'Escape' && open.value) close()
}

function handleScroll(): void {
  atTop.value = window.scrollY <= 2
}

watch(open, (value) => {
  if (settling.value) return
  if (value) {
    requestData()
    settleTo(true)
  } else if (progress.value > 0) {
    settleTo(false)
  }
})

watch(visible, async (value) => {
  if (value) {
    previousFocus =
      document.activeElement instanceof HTMLElement ? document.activeElement : null
    lockBody()
    await nextTick()
    closeButton.value?.focus()
  } else {
    unlockBody()
    previousFocus?.focus()
  }
})

onMounted(() => {
  handleScroll()
  window.addEventListener('wheel', handleWheel, {
    passive: false,
    capture: true,
  })
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('keydown', handleKey)
})

onBeforeUnmount(() => {
  window.removeEventListener('wheel', handleWheel, true)
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('keydown', handleKey)
  window.removeEventListener('pointermove', onPointerMove)
  if (settleTimer !== undefined) window.clearTimeout(settleTimer)
  cancelWheelGesture()
  if (visible.value) unlockBody()
})
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="galaxy-backdrop" @click="close"></div>

    <div
      v-if="visible"
      class="galaxy-curtain"
      :class="{ 'is-settling': settling }"
      :style="{
        clipPath: `inset(0 0 ${(1 - progress) * 100}% 0)`,
        maskImage: `linear-gradient(to bottom, black 0%, black calc(${progress * 100}% - 14%), transparent ${progress * 100}%)`,
        WebkitMaskImage: `linear-gradient(to bottom, black 0%, black calc(${progress * 100}% - 14%), transparent ${progress * 100}%)`,
      }"
      role="dialog"
      aria-modal="true"
      aria-label="记忆星图"
    >
      <div class="galaxy-curtain-scene">
        <Suspense v-if="data">
          <GalaxyScene
            :skills="data.skills"
            :progress="data.progress"
            :active="visible"
          />
          <template #fallback>
            <div class="galaxy-curtain-loading"><span class="galaxy-pulse"></span></div>
          </template>
        </Suspense>
        <div v-else class="galaxy-curtain-loading">
          <span v-if="loading" class="galaxy-pulse"></span>
          <button
            v-else
            class="galaxy-retry"
            type="button"
            aria-label="重试加载星图"
            @click="refresh"
          >
            ↻
          </button>
        </div>
      </div>

      <div class="galaxy-fade galaxy-fade-left" aria-hidden="true"></div>
      <div class="galaxy-fade galaxy-fade-right" aria-hidden="true"></div>

      <div class="galaxy-close-zone" aria-hidden="true" @click="close"></div>

      <button
        ref="closeButton"
        class="galaxy-close"
        type="button"
        aria-label="收起星图"
        @click="close"
      >
        ✕
      </button>
    </div>

    <button
      v-if="atTop || visible"
      class="galaxy-handle"
      :class="{ 'is-dragging': dragging, 'is-settling': settling }"
      type="button"
      aria-label="向下拉动打开星图"
      :aria-expanded="open"
      :style="{
        top: `calc(${progress * 100}vh + ${(1 - progress) * 9}px)`,
      }"
      @pointerdown="startDrag"
    ></button>
  </Teleport>
</template>

<style scoped>
.galaxy-backdrop {
  position: fixed;
  inset: 0;
  z-index: 69;
  background: oklch(0.05 0.005 260 / 0.5);
  backdrop-filter: blur(18px) saturate(0.65);
  cursor: pointer;
}

.galaxy-curtain {
  position: fixed;
  inset: 0;
  z-index: 70;
  overflow: hidden;
  background: #06070b;
  will-change: clip-path;
}

.galaxy-curtain.is-settling {
  transition: clip-path 300ms var(--ease-out);
}

.galaxy-curtain-scene {
  position: absolute;
  inset: 0;
}

.galaxy-curtain-loading {
  display: grid;
  place-content: center;
  justify-items: center;
  width: 100%;
  height: 100%;
  color: var(--text-subtle);
}

.galaxy-pulse {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 12px var(--accent);
  animation: galaxy-pulse 1.4s ease-in-out infinite;
}

@keyframes galaxy-pulse {
  0%,
  100% {
    opacity: 0.35;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

.galaxy-retry {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid var(--border-strong);
  border-radius: 50%;
  background: var(--surface);
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1;
}

.galaxy-retry:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.galaxy-close {
  position: fixed;
  top: 18px;
  right: 20px;
  z-index: 3;
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-strong);
  border-radius: 2px;
  background: oklch(0.1 0.006 260 / 0.55);
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1;
  backdrop-filter: blur(10px);
  transition:
    border-color var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out),
    background var(--duration-fast) var(--ease-out);
}

.galaxy-close:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent);
}

.galaxy-fade {
  position: absolute;
  z-index: 2;
  pointer-events: none;
}

.galaxy-fade-left,
.galaxy-fade-right {
  top: 0;
  bottom: 0;
  width: 18%;
}

.galaxy-fade-left {
  left: 0;
  background: linear-gradient(90deg, #06070b 0%, transparent 100%);
}

.galaxy-fade-right {
  right: 0;
  background: linear-gradient(270deg, #06070b 0%, transparent 100%);
}

.galaxy-close-zone {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 2;
  height: 160px;
  cursor: pointer;
  pointer-events: auto;
}

.galaxy-handle {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 80;
  width: 100%;
  height: 18px;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: grab;
  transform: translateY(-50%);
  touch-action: none;
}

.galaxy-handle.is-settling {
  transition: top 300ms var(--ease-out);
}

.galaxy-handle.is-dragging {
  cursor: grabbing;
}
</style>
