import { api } from './client'
import type {
  PreferencesUpdate,
  Profile,
  ProfileUpdate,
  UserPreferences,
} from '@/types/settings'

export const settingsApi = {
  getPreferences(): Promise<UserPreferences> {
    return api.get<UserPreferences>('/settings/preferences')
  },
  updatePreferences(payload: PreferencesUpdate): Promise<UserPreferences> {
    return api.patch<UserPreferences>('/settings/preferences', payload)
  },
  updateProfile(payload: ProfileUpdate): Promise<Profile> {
    return api.patch<Profile>('/settings/profile', payload)
  },
}
