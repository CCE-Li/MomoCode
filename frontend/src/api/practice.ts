import { api } from './client'
import type {
  AiReviewResult,
  AnswerPayload,
  PracticeResult,
  PracticeSession,
  RunTestsResult,
  SessionMode,
} from '@/types/practice'

export const practiceApi = {
  createSession(taskId: string, mode: SessionMode): Promise<PracticeSession> {
    return api.post<PracticeSession>('/sessions', {
      task_id: taskId,
      mode,
    })
  },
  getSession(sessionId: string): Promise<PracticeSession> {
    return api.get<PracticeSession>(`/sessions/${sessionId}`)
  },
  requestHint(
    sessionId: string,
    level: number,
  ): Promise<{
    level: number
    content: string
    max_hint_level: number
  }> {
    return api.post<{ level: number; content: string; max_hint_level: number }>(
      `/sessions/${sessionId}/hints`,
      { level },
    )
  },
  submitAnswer(sessionId: string, payload: AnswerPayload): Promise<PracticeSession> {
    return api.post<PracticeSession>(`/sessions/${sessionId}/answers`, payload)
  },
  runTests(
    sessionId: string,
    code: string,
    cases: Array<{ input: string; expected_output?: string }>,
  ): Promise<RunTestsResult> {
    return api.post<RunTestsResult>(`/sessions/${sessionId}/run`, {
      code,
      cases,
    })
  },
  aiReview(sessionId: string, code: string): Promise<AiReviewResult> {
    return api.post<AiReviewResult>(`/sessions/${sessionId}/ai-review`, {
      code,
    })
  },
  completeSession(sessionId: string, markAsReview: boolean): Promise<PracticeResult> {
    return api.post<PracticeResult>(`/sessions/${sessionId}/complete`, {
      mark_as_review: markAsReview,
    })
  },
  getResult(sessionId: string): Promise<PracticeResult> {
    return api.get<PracticeResult>(`/sessions/${sessionId}/result`)
  },
}
