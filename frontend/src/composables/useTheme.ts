import { computed, ref } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

const STORAGE_KEY = 'momocode-theme'

function getStoredTheme(): ThemeMode {
  if (typeof window === 'undefined') {
    return 'dark'
  }

  const stored = window.localStorage.getItem(STORAGE_KEY)
  return stored === 'light' || stored === 'dark' || stored === 'system'
    ? stored
    : 'dark'
}

function prefersDark(): boolean {
  if (typeof window === 'undefined') {
    return false
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

const mode = ref<ThemeMode>(getStoredTheme())
const systemPrefersDark = ref(prefersDark())

const resolved = computed<ResolvedTheme>(() => {
  if (mode.value === 'system') {
    return systemPrefersDark.value ? 'dark' : 'light'
  }
  return mode.value
})

function applyTheme(): void {
  if (typeof document === 'undefined') {
    return
  }
  document.documentElement.dataset.theme = resolved.value
}

function setTheme(next: ThemeMode): void {
  mode.value = next
  window.localStorage.setItem(STORAGE_KEY, next)
  applyTheme()
}

function cycleTheme(): void {
  const order: ThemeMode[] = ['system', 'light', 'dark']
  const index = order.indexOf(mode.value)
  setTheme(order[(index + 1) % order.length] ?? 'system')
}

if (typeof window !== 'undefined') {
  applyTheme()
  const media = window.matchMedia('(prefers-color-scheme: dark)')
  media.addEventListener('change', (event) => {
    systemPrefersDark.value = event.matches
    if (mode.value === 'system') {
      applyTheme()
    }
  })
}

export function useTheme() {
  return {
    mode,
    resolved,
    setTheme,
    cycleTheme,
  }
}
