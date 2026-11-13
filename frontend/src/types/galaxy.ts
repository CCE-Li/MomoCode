export interface GalaxySkillStar {
  skill_id: string
  skill_slug: string
  skill_name: string
  algorithm_slug: string
  algorithm_name: string
  category_slug: string
  category_name: string
  skill_type: string
  retrievability: number
  mastery: number
  review_count: number
  star_state: 'dark' | 'lit'
  brightness: number
  star_updated_at: string | null
}

export interface GalaxyResponse {
  total_skills: number
  lit_count: number
  progress: number
  skills: GalaxySkillStar[]
  computed_at: string
}
