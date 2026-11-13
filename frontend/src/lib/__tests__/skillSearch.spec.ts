import { describe, expect, it } from 'vitest'

import { buildSkillIndex, matchesSkillQuery, type IndexedSkill } from '../skillSearch'

const items = [
  { name: '独立复现二分模板', algorithmName: '二分查找', slug: 'binary-search-template' },
  { name: '识别前缀和适用场景', algorithmName: '前缀和', slug: 'prefix-sum-recognition' },
  { name: '双指针识别', algorithmName: '双指针', slug: 'two-pointers-recognition' },
  { name: '图论与搜索基础', algorithmName: 'BFS', slug: 'bfs-template' },
]

const index = buildSkillIndex(items)

function visible(query: string): string[] {
  return index
    .filter((entry: IndexedSkill<(typeof items)[number]>) => matchesSkillQuery(entry, query))
    .map((entry) => entry.item.slug)
}

describe('skill search', () => {
  it('matches chinese substring', () => {
    expect(visible('二分')).toEqual(['binary-search-template'])
    expect(visible('前缀')).toEqual(['prefix-sum-recognition'])
  })

  it('matches full pinyin and spaced pinyin', () => {
    expect(visible('erfen')).toEqual(['binary-search-template'])
    expect(visible('er fen')).toEqual(['binary-search-template'])
    expect(visible('shuangzhizhen')).toEqual(['two-pointers-recognition'])
  })

  it('matches pinyin initials', () => {
    expect(visible('efcz')).toEqual(['binary-search-template'])
    expect(visible('qzh')).toEqual(['prefix-sum-recognition'])
  })

  it('matches English slug and acronym', () => {
    expect(visible('binary')).toEqual(['binary-search-template'])
    expect(visible('BFS')).toEqual(['bfs-template'])
    expect(visible('prefix sum')).toEqual(['prefix-sum-recognition'])
  })

  it('does not match scattered initials', () => {
    expect(visible('efcz')).toEqual(['binary-search-template'])
    expect(visible('fcz')).not.toContain('two-pointers-recognition')
  })

  it('returns all for empty query and nothing for nonsense', () => {
    expect(visible('')).toHaveLength(items.length)
    expect(visible('zzzzz')).toEqual([])
  })
})
