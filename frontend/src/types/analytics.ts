export interface TrainingTypeMetrics {
  training_type: string
  sessions: number
  correctness_rate: number | null
  independent_rate: number | null
  avg_hint_level: number | null
}

export interface Overview {
  range_days: number
  sample_size: number
  insufficient_data: boolean
  sessions_completed: number
  correctness_rate: number | null
  independent_rate: number | null
  hint_dependency: number | null
  avg_normalized_time: number | null
  reviewed_count: number
  due_count: number
  training_types: TrainingTypeMetrics[]
}

export interface TrendPoint {
  date: string
  sessions: number
  correctness_rate: number | null
  independent_rate: number | null
}

export interface Trends {
  range_days: number
  points: TrendPoint[]
}

export interface ForgettingCurvePoint {
  day: number
  fibonacci_retention: number
  my_retention: number | null
}

export interface ForgettingCurve {
  horizon_days: number
  sample_size: number
  insufficient_data: boolean
  avg_stability_days: number | null
  fibonacci_intervals: number[]
  fibonacci_review_days: number[]
  points: ForgettingCurvePoint[]
  notes: string
}

export interface ErrorDistributionItem {
  error_type: string
  count: number
}

export interface SkillStat {
  skill_id: string
  skill_slug: string
  skill_name: string
  algorithm_name: string
  sample_size: number
  correctness_rate: number | null
  independence_score: number | null
  hint_dependency: number | null
  avg_normalized_time: number | null
  skill_score: number | null
  insufficient_data: boolean
  score_version: string
  computed_at: string
}

export interface MetricDefinition {
  key: string
  name: string
  formula: string
  source: string
  time_range: string
  notes: string
}
