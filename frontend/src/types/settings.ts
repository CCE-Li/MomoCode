export interface UserPreferences {
  timezone: string
  daily_review_limit: number
  desired_retention: number
  theme: string
  locale: string
}

export interface PreferencesUpdate {
  timezone?: string
  daily_review_limit?: number
  desired_retention?: number
  theme?: 'dark' | 'light' | 'system'
  locale?: string
}

export interface ProfileUpdate {
  display_name?: string
}

export interface Profile {
  id: string
  email: string
  display_name: string | null
  status: string
}
