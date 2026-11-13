export interface HealthStatus {
  status: string
}

export interface CurrentUser {
  id: string
  email: string
  displayName: string
  status: string
  emailVerifiedAt: string | null
  createdAt: string
}

export interface ApiErrorPayload {
  error?: {
    code?: string
    message?: string
    details?: Record<string, unknown>
    request_id?: string
  }
}
