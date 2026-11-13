import { api } from './client'
import type { TaskDetail, TaskSummary, TrainingType } from '@/types/catalog'
import type { UserTaskImportResult, UserTaskInput } from '@/types/userTasks'

interface UserTaskQuery {
  training_type?: TrainingType | ''
  difficulty?: number | ''
  skill?: string
  tag?: string
  search?: string
}

function queryString(params: UserTaskQuery): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value))
    }
  }
  const value = search.toString()
  return value ? `?${value}` : ''
}

export const userTasksApi = {
  list(params: UserTaskQuery = {}): Promise<TaskSummary[]> {
    return api.get<TaskSummary[]>(`/user-tasks${queryString(params)}`)
  },
  create(payload: UserTaskInput): Promise<TaskSummary> {
    return api.post<TaskSummary>('/user-tasks', payload)
  },
  bulkImport(tasks: UserTaskInput[]): Promise<UserTaskImportResult> {
    return api.post<UserTaskImportResult>('/user-tasks/import', { tasks })
  },
  get(taskId: string): Promise<TaskDetail> {
    return api.get<TaskDetail>(`/user-tasks/${encodeURIComponent(taskId)}`)
  },
  update(taskId: string, payload: Partial<UserTaskInput>): Promise<TaskSummary> {
    return api.patch<TaskSummary>(`/user-tasks/${encodeURIComponent(taskId)}`, payload)
  },
  delete(taskId: string): Promise<void> {
    return api.delete<void>(`/user-tasks/${encodeURIComponent(taskId)}`)
  },
}
