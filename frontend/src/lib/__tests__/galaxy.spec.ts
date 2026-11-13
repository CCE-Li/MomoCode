import { describe, expect, it } from 'vitest'
import { buildGalaxy, buildResidualNodes, hashString } from '@/lib/galaxy'
import type { GalaxySkillStar } from '@/types/galaxy'

function skill(overrides: Partial<GalaxySkillStar> = {}): GalaxySkillStar {
  return {
    skill_id: '00000000-0000-0000-0000-000000000001',
    skill_slug: 'binary-search-recognition',
    skill_name: '识别二分查找适用场景',
    algorithm_slug: 'binary-search',
    algorithm_name: '二分查找',
    category_slug: 'basic',
    category_name: '基础算法',
    skill_type: 'recognition',
    retrievability: 0.9,
    mastery: 90,
    review_count: 3,
    star_state: 'lit',
    brightness: 0.9,
    star_updated_at: null,
    ...overrides,
  }
}

describe('abstract galaxy layout', () => {
  it('hashes deterministically and distinguishes values', () => {
    expect(hashString('binary-search')).toBe(hashString('binary-search'))
    expect(hashString('binary-search')).not.toBe(hashString('two-pointers'))
  })

  it('builds one cluster per skill on the instrument rings', () => {
    const layout = buildGalaxy([
      skill({ skill_slug: 'a' }),
      skill({ skill_slug: 'b' }),
    ])
    expect(layout.clusters).toHaveLength(2)
    expect(layout.rings).toEqual([0.3, 0.46, 0.62, 0.78])
    expect(layout.spokes).toBe(24)
    expect(layout.clusters.every((cluster) => cluster.satellites.length === 4)).toBe(
      true,
    )
  })

  it('keeps one category on one ring', () => {
    const layout = buildGalaxy([
      skill({ skill_slug: 'a', category_slug: 'basic' }),
      skill({ skill_slug: 'b', category_slug: 'basic' }),
      skill({ skill_slug: 'c', category_slug: 'graph' }),
    ])
    const basic = layout.clusters.filter((cluster) => cluster.category === 'basic')
    expect(basic[0]?.radius).toBe(basic[1]?.radius)
  })

  it('marks lit clusters warm and dark clusters cool', () => {
    const layout = buildGalaxy([
      skill({ skill_slug: 'a', star_state: 'lit' }),
      skill({ skill_slug: 'b', star_state: 'dark' }),
    ])
    const lit = layout.clusters.find((cluster) => cluster.key === 'a')
    const dark = layout.clusters.find((cluster) => cluster.key === 'b')
    expect(lit?.tone).toBe('warm')
    expect(dark?.tone).toBe('cool')
    expect(lit?.state).toBe('lit')
    expect(dark?.state).toBe('dark')
  })

  it('keeps a few abstract residual nodes before any skill is mastered', () => {
    const first = buildResidualNodes()
    const second = buildResidualNodes()
    expect(first).toEqual(second)
    expect(first).toHaveLength(24)
    expect(first.every((node) => node.brightness >= 0.35)).toBe(true)
    expect(first.some((node) => node.tone === 'warm')).toBe(true)
    expect(first.some((node) => node.tone === 'cool')).toBe(true)
  })
})
