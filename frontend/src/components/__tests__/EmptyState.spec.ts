import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import EmptyState from '../EmptyState.vue'

describe('EmptyState', () => {
  it('renders title and description', () => {
    const wrapper = mount(EmptyState, {
      props: {
        title: '暂无内容',
        description: '完成一次训练后这里会出现记录。',
      },
    })

    expect(wrapper.text()).toContain('暂无内容')
    expect(wrapper.text()).toContain('完成一次训练后这里会出现记录。')
  })
})
