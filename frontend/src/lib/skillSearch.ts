import { pinyin } from 'pinyin-pro'

export interface SearchableSkill {
  name: string
  algorithmName: string
  slug?: string
  algorithmSlug?: string
}

export interface IndexedSkill<T> {
  item: T
  haystacks: string[]
  initials: string
}

function strip(value: string): string {
  return value.toLowerCase().replace(/[\s_\-·/（）()：:，,。.]/g, '')
}

function normalizedVariants(value: string): string[] {
  if (!value) return []
  const full = pinyin(value, { toneType: 'none', type: 'array' }) as string[]
  const initials = pinyin(value, {
    toneType: 'none',
    type: 'array',
    pattern: 'first',
  }) as string[]
  return [strip(value), full.join(''), full.join(' '), initials.join('')]
}

export function buildSkillIndex<T extends SearchableSkill>(items: T[]): IndexedSkill<T>[] {
  return items.map((item) => {
    const texts = [item.name, item.algorithmName, item.slug ?? '', item.algorithmSlug ?? '']
    const variants = texts.flatMap(normalizedVariants).filter(Boolean)
    return {
      item,
      haystacks: Array.from(new Set(variants)),
      initials: strip(
        Array.from(item.algorithmName + item.name)
          .map(
            (char) =>
              pinyin(char, { toneType: 'none', pattern: 'first', type: 'array' })[0] ?? char,
          )
          .join(''),
      ),
    }
  })
}

export function matchesSkillQuery<T>(indexed: IndexedSkill<T>, rawQuery: string): boolean {
  const query = strip(rawQuery)
  if (!query) return true

  const tokens = rawQuery.split(/\s+/).map(strip).filter(Boolean)
  if (tokens.length > 1) {
    return tokens.every((token) => indexed.haystacks.some((haystack) => haystack.includes(token)))
  }

  if (indexed.haystacks.some((haystack) => haystack.includes(query))) {
    return true
  }

  return indexed.initials.includes(query)
}
