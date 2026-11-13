export type OJPlatform = 'codeforces' | 'luogu' | 'atcoder' | 'other'

export type OJVerdict =
  | 'accepted'
  | 'wrong_answer'
  | 'time_limit_exceeded'
  | 'memory_limit_exceeded'
  | 'runtime_error'
  | 'compilation_error'
  | 'partially_accepted'
  | 'other'

export interface OJAccount {
  id: string
  platform: string
  handle: string
  display_name: string | null
  is_active: boolean
  last_synced_at: string | null
  created_at: string
}

export interface SyncResult {
  fetched: number
  created: number
  skipped: number
  last_synced_at: string
}

export interface Submission {
  id: string
  session_id: string | null
  platform: string
  external_id: string | null
  problem_ref: string | null
  problem_url: string | null
  verdict: string | null
  verdict_raw: string | null
  language: string | null
  time_ms: number | null
  memory_kb: number | null
  submitted_at: string | null
  source: string
  created_at: string
}

export interface ManualSubmissionResult {
  submission: Submission
  duplicate: boolean
}

export interface ManualSubmissionPayload {
  platform: OJPlatform
  external_id: string
  problem_ref?: string
  problem_url?: string
  verdict?: OJVerdict
  verdict_raw?: string
  language?: string
  time_ms?: number
  memory_kb?: number
  submitted_at?: string
  oj_account_id?: string
}
