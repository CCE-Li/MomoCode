export interface Category {
  id: string
  slug: string
  name: string
  description: string | null
  sort_order: number
}

export interface SkillRef {
  id: string
  slug: string
  name: string
  skill_type: string
  algorithm_slug: string
  algorithm_name: string
}

export interface SkillSummary extends SkillRef {
  learning_objective: string | null
}

export interface SkillDetail extends SkillSummary {
  description_md: string | null
  mastery_evidence_md: string | null
  common_mistakes_md: string | null
  prerequisites: string[]
}

export interface AlgorithmSummary {
  id: string
  slug: string
  name: string
  category_slug: string
  category_name: string
  summary: string | null
  difficulty: number
  skill_count: number
}

export interface AlgorithmDetail extends AlgorithmSummary {
  description_md: string | null
  prerequisites: string[]
  skills: SkillSummary[]
}

export interface TaskSummary {
  id: string
  slug: string
  title: string
  training_type: string
  evaluation_mode: string
  difficulty: number
  source_type: string
  language: string
  max_hint_level: number
  oj_platform: string | null
  oj_problem_url: string | null
  target_skills: SkillRef[]
  tags: string[]
}

export interface TaskDetail extends TaskSummary {
  statement_md: string
  constraints_md: string | null
  input_spec: Record<string, unknown> | null
  expected_output_spec: Record<string, unknown> | null
  code_scaffold: string | null
  error_types: string[]
  related_skills: SkillRef[]
}

export type TrainingType = 'recognition' | 'template' | 'variant' | 'correction'
