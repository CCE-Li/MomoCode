import { api } from './client'
import type { CurrentUser } from '@/types/api'

interface UserDto {
  id: string
  email: string
  display_name: string | null
  status: string
  email_verified_at: string | null
  created_at: string
}

interface AuthResponseDto {
  user: UserDto
  csrf_token: string
}

function mapUser(dto: UserDto): CurrentUser {
  return {
    id: dto.id,
    email: dto.email,
    displayName: dto.display_name ?? dto.email.split('@')[0] ?? dto.email,
    status: dto.status,
    emailVerifiedAt: dto.email_verified_at,
    createdAt: dto.created_at,
  }
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  displayName?: string
}

export interface AuthSession {
  id: string
  user_agent: string | null
  created_at: string
  last_used_at: string | null
  expires_at: string
  is_current: boolean
}

export async function login(payload: LoginPayload): Promise<CurrentUser> {
  const response = await api.post<AuthResponseDto>('/auth/login', {
    email: payload.email,
    password: payload.password,
  })
  return mapUser(response.user)
}

export async function register(payload: RegisterPayload): Promise<CurrentUser> {
  const response = await api.post<AuthResponseDto>('/auth/register', {
    email: payload.email,
    password: payload.password,
    display_name: payload.displayName || null,
  })
  return mapUser(response.user)
}

export async function fetchCurrentUser(): Promise<CurrentUser> {
  const user = await api.get<UserDto>('/auth/me')
  return mapUser(user)
}

export async function logout(): Promise<void> {
  await api.post<void>('/auth/logout')
}

export async function fetchSessions(): Promise<AuthSession[]> {
  return api.get<AuthSession[]>('/auth/sessions')
}

export async function revokeSession(sessionId: string): Promise<void> {
  await api.delete<void>(`/auth/sessions/${sessionId}`)
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await api.post<void>('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

export async function logoutAll(): Promise<void> {
  await api.post<void>('/auth/logout-all')
}

export async function verifyEmail(token: string): Promise<void> {
  await api.post<void>('/auth/verify-email', { token })
}

export async function resendVerification(): Promise<void> {
  await api.post<void>('/auth/verify-email/resend')
}

export async function requestPasswordReset(email: string): Promise<string> {
  const response = await api.post<{ message: string }>('/auth/password-reset/request', {
    email,
  })
  return response.message
}

export async function resetPassword(
  token: string,
  newPassword: string,
): Promise<void> {
  await api.post<void>('/auth/password-reset/confirm', {
    token,
    new_password: newPassword,
  })
}

export async function deleteAccount(password: string): Promise<void> {
  await api.post<void>('/auth/account/delete', {
    password,
    confirmation: 'DELETE',
  })
}
