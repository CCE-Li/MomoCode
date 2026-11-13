import { api } from './client'
import type { GalaxyResponse } from '@/types/galaxy'

export const galaxyApi = {
  get(): Promise<GalaxyResponse> {
    return api.get<GalaxyResponse>('/analytics/galaxy')
  },
}
