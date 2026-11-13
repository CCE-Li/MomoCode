export type ReviewItemKind = 'skill' | 'custom'

export interface DueItem {
  kind: ReviewItemKind
  due_at: string
  overdue: boolean
  skill_id: string | null
  skill_slug: string | null
  skill_name: string | null
  algorithm_slug: string | null
  algorithm_name: string | null
  task_id: string | null
  task_slug: string | null
  task_title: string | null
  max_hint_level: number
  custom_item_id: string | null
  title: string | null
  content_preview: string | null
}

export interface DueQueue {
  items: DueItem[]
  due_count: number
  daily_limit: number
  timezone: string
}

export interface TodayReview {
  due_count: number
  overdue_count: number
  reviewed_today: number
  timezone: string
  next_due_at: string | null
}

export interface ReviewHistoryItem {
  kind: ReviewItemKind
  id: string
  rating: number
  reviewed_at: string
  review_duration_ms: number | null
  skill_slug: string | null
  skill_name: string | null
  algorithm_name: string | null
  custom_item_id: string | null
  title: string | null
}

export interface CustomReviewItem {
  id: string
  title: string
  content_md: string
  tags: string[]
  source_url: string | null
  is_active: boolean
  due_at: string | null
  last_review_at: string | null
  created_at: string
  updated_at: string
}

export interface CustomReviewItemPayload {
  title: string
  content_md: string
  tags: string[]
  source_url?: string | null
}

export interface CustomReviewResult {
  item_id: string
  rating: number
  reviewed_at: string
  next_due_at: string
}
