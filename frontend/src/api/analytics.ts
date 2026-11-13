import { api } from './client'
import type {
  ErrorDistributionItem,
  ForgettingCurve,
  MetricDefinition,
  Overview,
  SkillStat,
  Trends,
} from '@/types/analytics'

export const analyticsApi = {
  overview(days: number): Promise<Overview> {
    return api.get<Overview>(`/analytics/overview?days=${days}`)
  },
  trends(days: number): Promise<Trends> {
    return api.get<Trends>(`/analytics/trends?days=${days}`)
  },
  errors(days: number): Promise<ErrorDistributionItem[]> {
    return api.get<ErrorDistributionItem[]>(`/analytics/errors?days=${days}`)
  },
  skills(days: number): Promise<SkillStat[]> {
    return api.get<SkillStat[]>(`/analytics/skills?days=${days}`)
  },
  definitions(): Promise<MetricDefinition[]> {
    return api.get<MetricDefinition[]>('/analytics/definitions')
  },
  forgettingCurve(horizonDays = 30): Promise<ForgettingCurve> {
    return api.get<ForgettingCurve>(`/analytics/forgetting-curve?horizon_days=${horizonDays}`)
  },
}
