import type { SkillRef } from './catalog'

export type SessionMode = 'review' | 'free'
export type SelfAssessment = 'correct' | 'partial' | 'incorrect'

export interface HintUsed {
  level: number
  content: string
  requested_at: string
}

export interface JudgeCaseResult {
  input: string
  expected_output: string | null
  actual_output: string
  status: string
}

export interface SampleCase {
  input: string
  expected_output: string
}

export interface RunTestsResult {
  result: string
  passed: number
  total: number
  score?: number
  message?: string
  compile_output?: string
  cases?: JudgeCaseResult[]
}

export interface AiReviewResult {
  verdict: string
  score: number | null
  summary: string
  issues: string[]
  suggestions: string[]
}

export interface AutoGrade {
  result?: string
  overlap_score?: number
  target_skill_ids?: string[]
  selected_skill_ids?: string[]
  passed?: number
  total?: number
  score?: number
  compile_output?: string
  message?: string
  cases?: JudgeCaseResult[]
  [key: string]: unknown
}

export interface SessionTaskView {
  id: string
  slug: string
  title: string
  training_type: string
  evaluation_mode: string
  difficulty: number
  statement_md: string
  constraints_md: string | null
  input_spec: Record<string, unknown> | null
  expected_output_spec: Record<string, unknown> | null
  code_scaffold: string | null
  language: string
  max_hint_level: number
  error_types: string[]
  target_skills: SkillRef[]
  related_skills: SkillRef[]
  sample_cases: SampleCase[]
}

export interface PracticeSession {
  id: string
  task: SessionTaskView
  training_type: string
  mode: SessionMode
  status: string
  started_at: string | null
  submitted_at: string | null
  completed_at: string | null
  time_spent_ms: number | null
  max_hint_level: number
  mark_as_review: boolean
  hints_used: HintUsed[]
  self_assessment: SelfAssessment | null
  auto_grade: AutoGrade | null
  draft_code: string | null
  draft_saved_at: string | null
  submitted_code: string | null
}

export interface PracticeResult extends PracticeSession {
  self_assessment_note: string | null
  error_types: string[]
  reference_solution_md: string | null
  next_review_at: string | null
}

export interface AnswerPayload {
  answer_payload: Record<string, unknown>
  self_assessment?: SelfAssessment
  self_assessment_note?: string
  error_types?: string[]
}
