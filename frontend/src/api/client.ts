import type { ApiErrorPayload } from '@/types/api'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string

  constructor(
    message: string,
    options: { status: number; code: string; requestId?: string },
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
    this.requestId = options.requestId
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let payload: ApiErrorPayload | undefined
  try {
    payload = (await response.json()) as ApiErrorPayload
  } catch {
    payload = undefined
  }

  return new ApiError(payload?.error?.message ?? '请求失败', {
    status: response.status,
    code: payload?.error?.code ?? 'UNKNOWN_ERROR',
    requestId: payload?.error?.request_id,
  })
}

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') {
    return null
  }

  const match = document.cookie.match(/(?:^|;\s*)momo_csrf=([^;]+)/)
  return match?.[1] ? decodeURIComponent(match[1]) : null
}

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 429) return '尝试次数过多，请稍后再试。'
    return error.message
  }

  return '无法连接服务器，请检查网络后重试。'
}

export async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  const method = (init.method ?? 'GET').toUpperCase()
  if (method !== 'GET' && method !== 'HEAD' && !headers.has('X-CSRF-Token')) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      headers.set('X-CSRF-Token', csrfToken)
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...init,
    headers,
  })

  if (!response.ok) {
    throw await parseError(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>(path)
  },
  post<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
      method: 'POST',
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  },
  patch<T>(path: string, body?: unknown): Promise<T> {
    return request<T>(path, {
      method: 'PATCH',
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  },
  delete<T>(path: string): Promise<T> {
    return request<T>(path, { method: 'DELETE' })
  },
}
