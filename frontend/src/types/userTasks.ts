import type { TaskSummary, TrainingType } from './catalog'

export type UserTaskPlatform = 'codeforces' | 'luogu' | 'atcoder' | 'other'
export type UserTaskEvaluationMode =
  | 'auto_recognition'
  | 'self_assessment'
  | 'auto_tests'

export interface UserTaskInput {
  title: string
  training_type: TrainingType
  evaluation_mode: UserTaskEvaluationMode
  difficulty: number
  source_ref?: string | null
  oj_platform?: UserTaskPlatform | null
  oj_problem_ref?: string | null
  oj_problem_url?: string | null
  statement_md: string
  constraints_md?: string | null
  input_spec?: Record<string, unknown> | null
  expected_output_spec?: Record<string, unknown> | null
  code_scaffold?: string | null
  reference_solution_md?: string | null
  language?: string
  hints?: Record<string, string>
  max_hint_level: number
  error_types?: string[]
  tags?: string[]
  target_skills: string[]
  related_skills?: string[]
}

export interface UserTaskImportResult {
  created: TaskSummary[]
  total: number
}
