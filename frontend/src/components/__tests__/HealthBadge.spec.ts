import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import HealthBadge from '../HealthBadge.vue'

vi.mock('@/api/health', () => ({
  getHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
}))

describe('HealthBadge', () => {
  it('shows the API status after loading', async () => {
    const wrapper = mount(HealthBadge)
    await flushPromises()

    expect(wrapper.text()).toContain('API 正常')
    expect(wrapper.attributes('role')).toBe('status')
  })
})
