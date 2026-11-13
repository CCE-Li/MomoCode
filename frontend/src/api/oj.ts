import { api } from './client'
import type {
  ManualSubmissionPayload,
  ManualSubmissionResult,
  OJAccount,
  Submission,
  SyncResult,
} from '@/types/oj'

interface SubmissionQuery {
  platform?: string
  session_id?: string
}

function queryString(params: SubmissionQuery): string {
  const search = new URLSearchParams()
  if (params.platform) search.set('platform', params.platform)
  if (params.session_id) search.set('session_id', params.session_id)
  const value = search.toString()
  return value ? `?${value}` : ''
}

export const ojApi = {
  accounts(): Promise<OJAccount[]> {
    return api.get<OJAccount[]>('/oj/accounts')
  },
  createAccount(payload: {
    platform: string
    handle: string
    display_name?: string
  }): Promise<OJAccount> {
    return api.post<OJAccount>('/oj/accounts', payload)
  },
  deleteAccount(accountId: string): Promise<void> {
    return api.delete<void>(`/oj/accounts/${accountId}`)
  },
  syncAccount(accountId: string): Promise<SyncResult> {
    return api.post<SyncResult>(`/oj/accounts/${accountId}/sync`)
  },
  submissions(params: SubmissionQuery = {}): Promise<Submission[]> {
    return api.get<Submission[]>(`/submissions${queryString(params)}`)
  },
  createManualSubmission(
    payload: ManualSubmissionPayload,
  ): Promise<ManualSubmissionResult> {
    return api.post<ManualSubmissionResult>('/submissions/manual', payload)
  },
  sessionSubmissions(sessionId: string): Promise<Submission[]> {
    return api.get<Submission[]>(`/sessions/${sessionId}/submissions`)
  },
  linkSubmission(sessionId: string, submissionId: string): Promise<Submission> {
    return api.post<Submission>(`/sessions/${sessionId}/submissions`, {
      submission_id: submissionId,
    })
  },
}
