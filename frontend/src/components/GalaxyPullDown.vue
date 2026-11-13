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

const RING_PX = 220
const TWEEN_MS = 420
const RING_CIRCUMFERENCE = 2 * Math.PI * 34
const SCROLL_COOLDOWN_MS = 400

const open = defineModel<boolean>('open', { default: false })

const pull = ref(0)
const viewportHeight = ref(
  typeof window !== 'undefined' ? window.innerHeight : 800,
)
const atTop = ref(true)
const dragging = ref(false)
const closing = ref(false)
const data = ref<GalaxyResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const closeButton = ref<HTMLButtonElement | null>(null)

const ringProgress = computed(() => clamp01(pull.value / RING_PX))
const stage2 = computed(() =>
  clamp01(
    (pull.value - RING_PX) / Math.max(1, viewportHeight.value - RING_PX),
  ),
)
const galaxyOpacity = computed(() => clamp01(stage2.value * 1.35))
const ringOpacity = computed(() => {
  if (closing.value || pull.value <= 0) return 0
  return clamp01(Math.min(pull.value / 18, 1 - stage2.value))
})
const ringVisible = computed(() => ringOpacity.value > 0.01)
const closeVisible = computed(() => open.value || pull.value > RING_PX)
const sceneActive = computed(() => pull.value > 0)
const ringOffset = computed(
  () => RING_CIRCUMFERENCE * (1 - ringProgress.value),
)
const ringTop = computed(() => `${Math.max(52, pull.value / 2)}px`)
const slideClip = computed(
  () => `inset(0 0 ${Math.max(0, viewportHeight.value - pull.value)}px 0)`,
)

let suppressOpenWatch = false
let tweenFrame = 0
let wheelGesture = false
let wheelTimer: number | undefined
let startY = 0
let startPull = 0
let lastScrollAt = 0
let lastLoadedAt = 0
let bodyLocked = false
let previousFocus: HTMLElement | null = null
let previousBodyOverflow = ''
let previousBodyPaddingRight = ''

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value))
}

function getShell(): HTMLElement | null {
  return document.querySelector<HTMLElement>('.app-shell')
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
  if (bodyLocked) return
  previousBodyOverflow = document.body.style.overflow
  previousBodyPaddingRight = document.body.style.paddingRight
  const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
  document.body.style.overflow = 'hidden'
  if (scrollbarWidth > 0) {
    document.body.style.paddingRight = `${scrollbarWidth}px`
  }
  bodyLocked = true
}

function unlockBody(): void {
  if (!bodyLocked) return
  document.body.style.overflow = previousBodyOverflow
  document.body.style.paddingRight = previousBodyPaddingRight
  bodyLocked = false
}

function cancelTween(): void {
  if (tweenFrame) {
    cancelAnimationFrame(tweenFrame)
    tweenFrame = 0
  }
}

function cancelWheelGesture(): void {
  wheelGesture = false
  if (wheelTimer !== undefined) {
    window.clearTimeout(wheelTimer)
    wheelTimer = undefined
  }
}

function animateTo(target: number): void {
  cancelWheelGesture()
  cancelTween()
  const start = pull.value
  if (Math.abs(target - start) < 0.5) {
    pull.value = target
    return
  }

  const startedAt = performance.now()
  const step = (now: number) => {
    const progress = Math.min(1, (now - startedAt) / TWEEN_MS)
    const eased = 1 - Math.pow(1 - progress, 3)
    pull.value = start + (target - start) * eased
    if (progress < 1) {
      tweenFrame = requestAnimationFrame(step)
    } else {
      tweenFrame = 0
    }
  }
  tweenFrame = requestAnimationFrame(step)
}

function requestOpen(value: boolean): void {
  closing.value = !value && pull.value > 0
  if (open.value !== value) {
    suppressOpenWatch = true
    open.value = value
    void nextTick(() => {
      suppressOpenWatch = false
    })
  }
  animateTo(value ? viewportHeight.value : 0)
}

function close(): void {
  requestOpen(false)
}

function startDrag(event: PointerEvent): void {
  if (event.button !== 0) return
  event.preventDefault()
  cancelTween()
  cancelWheelGesture()
  closing.value = false
  requestData()
  dragging.value = true
  startY = event.clientY
  startPull = pull.value
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
  pull.value = Math.max(
    0,
    Math.min(
      viewportHeight.value,
      startPull + (event.clientY - startY),
    ),
  )
}

function onPointerUp(): void {
  if (!dragging.value) return
  dragging.value = false
  window.removeEventListener('pointermove', onPointerMove)
  requestOpen(pull.value >= RING_PX)
}

function finishWheelGesture(): void {
  if (!wheelGesture) return
  wheelGesture = false
  wheelTimer = undefined
  requestOpen(pull.value >= RING_PX)
}

function handleWheel(event: WheelEvent): void {
  if (event.ctrlKey || open.value) return

  if (!wheelGesture) {
    if (window.scrollY > 0) {
      lastScrollAt = performance.now()
      return
    }
    if (event.deltaY >= 0) return
    if (
      lastScrollAt > 0 &&
      performance.now() - lastScrollAt < SCROLL_COOLDOWN_MS
    ) {
      lastScrollAt = performance.now()
      return
    }
    wheelGesture = true
    closing.value = false
    cancelTween()
    requestData()
  }

  pull.value = Math.max(
    0,
    Math.min(viewportHeight.value, pull.value - event.deltaY),
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
  lastScrollAt = performance.now()
}

function handleResize(): void {
  viewportHeight.value = window.innerHeight
  if (pull.value > viewportHeight.value) {
    pull.value = viewportHeight.value
  }
}

watch(pull, (value) => {
  const shell = getShell()
  if (shell) {
    shell.style.transform = value > 0 ? `translateY(${value}px)` : ''
    shell.style.willChange = value > 0 ? 'transform' : ''
  }
  if (value > 0) lockBody()
  else {
    unlockBody()
    closing.value = false
  }
})

watch(open, async (value) => {
  const shell = getShell()
  if (shell) {
    shell.toggleAttribute('inert', value)
    if (value) shell.setAttribute('aria-hidden', 'true')
    else shell.removeAttribute('aria-hidden')
  }

  if (!suppressOpenWatch) {
    closing.value = !value
    animateTo(value ? viewportHeight.value : 0)
  }

  if (value) {
    previousFocus =
      document.activeElement instanceof HTMLElement ? document.activeElement : null
    await nextTick()
    closeButton.value?.focus()
  } else {
    previousFocus?.focus()
    previousFocus = null
  }
})

onMounted(() => {
  atTop.value = window.scrollY <= 2
  void refresh()
  void import('./GalaxyScene.vue')
  window.addEventListener('wheel', handleWheel, {
    passive: false,
    capture: true,
  })
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('resize', handleResize, { passive: true })
  window.addEventListener('keydown', handleKey)
})

onBeforeUnmount(() => {
  window.removeEventListener('wheel', handleWheel, true)
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKey)
  window.removeEventListener('pointermove', onPointerMove)
  cancelTween()
  cancelWheelGesture()
  const shell = getShell()
  if (shell) {
    shell.style.transform = ''
    shell.style.willChange = ''
    shell.removeAttribute('inert')
    shell.removeAttribute('aria-hidden')
  }
  unlockBody()
})
</script>

<template>
  <Teleport to="body">
    <div
      class="galaxy-scene-layer"
      :style="{ opacity: galaxyOpacity, clipPath: slideClip }"
      :aria-hidden="!open"
      role="dialog"
      aria-modal="true"
      aria-label="记忆星图"
    >
      <Suspense v-if="data">
        <GalaxyScene
          :skills="data.skills"
          :progress="data.progress"
          :active="sceneActive"
        />
        <template #fallback>
          <div class="galaxy-stage-loading"><span class="galaxy-pulse"></span></div>
        </template>
      </Suspense>
      <div v-else class="galaxy-stage-loading">
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

    <div
      v-if="ringVisible"
      class="galaxy-ring"
      :style="{ opacity: ringOpacity, top: ringTop }"
      aria-hidden="true"
    >
      <svg viewBox="0 0 80 80">
        <circle class="galaxy-ring-track" cx="40" cy="40" r="34" />
        <circle
          class="galaxy-ring-value"
          cx="40"
          cy="40"
          r="34"
          :style="{ strokeDashoffset: ringOffset }"
        />
      </svg>
    </div>

    <button
      v-if="closeVisible"
      ref="closeButton"
      class="galaxy-close"
      type="button"
      aria-label="收起星图"
      @click="close"
    >
      ✕
    </button>

    <button
      v-if="atTop && !open"
      class="galaxy-handle"
      type="button"
      aria-label="向下拉动打开星图"
      :aria-expanded="open"
      @pointerdown="startDrag"
    ></button>
  </Teleport>
</template>

<style scoped>
.galaxy-scene-layer {
  position: fixed;
  inset: 0;
  z-index: 70;
  overflow: hidden;
  background: #06070b;
  will-change: clip-path, opacity;
}

.galaxy-stage-loading {
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

.galaxy-ring {
  position: fixed;
  top: 50%;
  left: 50%;
  z-index: 90;
  width: 96px;
  height: 96px;
  transform: translate(-50%, -50%);
  pointer-events: none;
  filter: drop-shadow(0 0 8px color-mix(in oklch, var(--accent) 45%, transparent));
}

.galaxy-ring svg {
  display: block;
  width: 100%;
  height: 100%;
}

.galaxy-ring-track {
  fill: none;
  stroke: var(--border-strong);
  stroke-width: 3;
  opacity: 0.35;
}

.galaxy-ring-value {
  fill: none;
  stroke: var(--accent);
  stroke-width: 3;
  stroke-linecap: round;
  stroke-dasharray: 213.628;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
  transition: stroke-dashoffset 80ms linear;
}

.galaxy-close {
  position: fixed;
  top: 18px;
  right: 20px;
  z-index: 91;
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
  touch-action: none;
}

.galaxy-handle:active {
  cursor: grabbing;
}

@media (max-width: 767px) {
  .galaxy-ring {
    width: 76px;
    height: 76px;
  }
}
</style>
