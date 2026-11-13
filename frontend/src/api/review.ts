import { api } from './client'
import type {
  CustomReviewItem,
  CustomReviewItemPayload,
  CustomReviewResult,
  DueQueue,
  ReviewHistoryItem,
  TodayReview,
} from '@/types/review'

export const reviewApi = {
  due(): Promise<DueQueue> {
    return api.get<DueQueue>('/reviews/due')
  },
  today(): Promise<TodayReview> {
    return api.get<TodayReview>('/reviews/today')
  },
  history(limit = 50): Promise<ReviewHistoryItem[]> {
    return api.get<ReviewHistoryItem[]>(`/reviews/history?limit=${limit}`)
  },
  customItems(includeInactive = false): Promise<CustomReviewItem[]> {
    const suffix = includeInactive ? '?include_inactive=true' : ''
    return api.get<CustomReviewItem[]>(`/reviews/custom-items${suffix}`)
  },
  createCustomItem(payload: CustomReviewItemPayload): Promise<CustomReviewItem> {
    return api.post<CustomReviewItem>('/reviews/custom-items', payload)
  },
  updateCustomItem(
    itemId: string,
    payload: Partial<CustomReviewItemPayload> & { is_active?: boolean },
  ): Promise<CustomReviewItem> {
    return api.patch<CustomReviewItem>(
      `/reviews/custom-items/${encodeURIComponent(itemId)}`,
      payload,
    )
  },
  deleteCustomItem(itemId: string): Promise<void> {
    return api.delete<void>(`/reviews/custom-items/${encodeURIComponent(itemId)}`)
  },
  reviewCustomItem(
    itemId: string,
    rating: number,
    reviewDurationMs?: number,
  ): Promise<CustomReviewResult> {
    return api.post<CustomReviewResult>(
      `/reviews/custom-items/${encodeURIComponent(itemId)}/review`,
      {
        rating,
        review_duration_ms: reviewDurationMs,
      },
    )
  },
}
