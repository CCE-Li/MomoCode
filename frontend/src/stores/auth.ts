import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import {
  changePassword as apiChangePassword,
  deleteAccount as apiDeleteAccount,
  fetchCurrentUser,
  fetchSessions,
  login as apiLogin,
  logout as apiLogout,
  logoutAll as apiLogoutAll,
  register as apiRegister,
  revokeSession as apiRevokeSession,
  type AuthSession,
  type LoginPayload,
  type RegisterPayload,
} from '@/api/auth'
import { ApiError, getApiErrorMessage } from '@/api/client'
import type { CurrentUser } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<CurrentUser | null>(null)
  const initialized = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const sessions = ref<AuthSession[]>([])
  const sessionsLoading = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  async function fetchMe(): Promise<void> {
    error.value = null
    try {
      user.value = await fetchCurrentUser()
    } catch (err) {
      user.value = null
      sessions.value = []
      if (!(err instanceof ApiError) || err.status !== 401) {
        error.value = getApiErrorMessage(err)
      }
    } finally {
      initialized.value = true
    }
  }

  async function login(payload: LoginPayload): Promise<void> {
    loading.value = true
    error.value = null
    try {
      user.value = await apiLogin(payload)
      initialized.value = true
    } catch (err) {
      error.value = getApiErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload): Promise<void> {
    loading.value = true
    error.value = null
    try {
      user.value = await apiRegister(payload)
      initialized.value = true
    } catch (err) {
      error.value = getApiErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await apiLogout()
      user.value = null
      sessions.value = []
    } catch (err) {
      error.value = getApiErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function loadSessions(): Promise<void> {
    sessionsLoading.value = true
    try {
      sessions.value = await fetchSessions()
    } finally {
      sessionsLoading.value = false
    }
  }

  async function revokeSession(sessionId: string): Promise<void> {
    const target = sessions.value.find((item) => item.id === sessionId)
    await apiRevokeSession(sessionId)
    if (target?.is_current) {
      user.value = null
      sessions.value = []
    } else {
      await loadSessions()
    }
  }

  async function changePassword(
    currentPassword: string,
    newPassword: string,
  ): Promise<void> {
    await apiChangePassword(currentPassword, newPassword)
    await loadSessions()
  }

  async function logoutAll(): Promise<void> {
    await apiLogoutAll()
    user.value = null
    sessions.value = []
  }

  async function deleteAccount(password: string): Promise<void> {
    await apiDeleteAccount(password)
    user.value = null
    sessions.value = []
  }

  function clear(): void {
    user.value = null
    sessions.value = []
    error.value = null
  }

  function markInitialized(): void {
    initialized.value = true
  }

  return {
    user,
    initialized,
    loading,
    error,
    sessions,
    sessionsLoading,
    isAuthenticated,
    fetchMe,
    login,
    register,
    logout,
    loadSessions,
    revokeSession,
    changePassword,
    logoutAll,
    deleteAccount,
    clear,
    markInitialized,
  }
})
