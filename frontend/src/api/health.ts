import { api } from './client'
import type { HealthStatus } from '@/types/api'

export function getHealth(): Promise<HealthStatus> {
  return api.get<HealthStatus>('/health')
}
