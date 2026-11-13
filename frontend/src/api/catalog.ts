import { api } from './client'
import type {
  AlgorithmDetail,
  AlgorithmSummary,
  Category,
  SkillDetail,
  SkillSummary,
  TaskDetail,
  TaskSummary,
  TrainingType,
} from '@/types/catalog'

interface QueryParams {
  category?: string
  search?: string
  algorithm?: string
  skill?: string
  skill_type?: string
  training_type?: TrainingType | ''
  difficulty?: number | ''
  tag?: string
}

function queryString(params: QueryParams): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value))
    }
  }
  const value = search.toString()
  return value ? `?${value}` : ''
}

export const catalogApi = {
  categories(): Promise<Category[]> {
    return api.get<Category[]>('/catalog/categories')
  },
  algorithms(params: QueryParams = {}): Promise<AlgorithmSummary[]> {
    return api.get<AlgorithmSummary[]>(`/catalog/algorithms${queryString(params)}`)
  },
  algorithm(slug: string): Promise<AlgorithmDetail> {
    return api.get<AlgorithmDetail>(`/catalog/algorithms/${encodeURIComponent(slug)}`)
  },
  skills(params: QueryParams = {}): Promise<SkillSummary[]> {
    return api.get<SkillSummary[]>(`/catalog/skills${queryString(params)}`)
  },
  skill(slug: string): Promise<SkillDetail> {
    return api.get<SkillDetail>(`/catalog/skills/${encodeURIComponent(slug)}`)
  },
  tasks(params: QueryParams = {}): Promise<TaskSummary[]> {
    return api.get<TaskSummary[]>(`/catalog/tasks${queryString(params)}`)
  },
  task(slug: string): Promise<TaskDetail> {
    return api.get<TaskDetail>(`/catalog/tasks/${encodeURIComponent(slug)}`)
  },
}
