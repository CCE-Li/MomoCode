import type { GalaxySkillStar } from '@/types/galaxy'

export interface GalaxySatellite {
  key: string
  dx: number
  dy: number
  size: number
  phase: number
}

export interface GalaxyCluster {
  key: string
  category: string
  angle: number
  radius: number
  x: number
  y: number
  state: 'lit' | 'dark'
  brightness: number
  tone: 'warm' | 'cool'
  satellites: GalaxySatellite[]
}

export interface GalaxyNode {
  key: string
  x: number
  y: number
  size: number
  phase: number
  brightness: number
  tone: 'warm' | 'cool'
}

export interface GalaxyLayout {
  clusters: GalaxyCluster[]
  residual: GalaxyNode[]
  rings: number[]
  spokes: number
}

const TAU = Math.PI * 2
const RINGS = [0.3, 0.46, 0.62, 0.78]
const SPOKES = 24
const RESIDUAL_SEED = 20261112
const SATELLITES_PER_SKILL = 4

export function hashString(value: string): number {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

export function mulberry32(seed: number): () => number {
  let state = seed >>> 0
  return () => {
    state = (state + 0x6d2b79f5) >>> 0
    let value = state
    value = Math.imul(value ^ (value >>> 15), value | 1)
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61)
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296
  }
}

export function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value))
}

export function buildResidualNodes(count = 24): GalaxyNode[] {
  const random = mulberry32(RESIDUAL_SEED)
  const nodes: GalaxyNode[] = []
  for (let index = 0; index < count; index += 1) {
    const ring = RINGS[Math.floor(random() * RINGS.length)] ?? 0.46
    const angle = random() * TAU
    nodes.push({
      key: `residual:${index}`,
      x: Math.cos(angle) * ring,
      y: Math.sin(angle) * ring,
      size: 0.8 + random() * 1.0,
      phase: random() * TAU,
      brightness: 0.35 + random() * 0.3,
      tone: random() > 0.65 ? 'warm' : 'cool',
    })
  }
  return nodes
}

export function buildGalaxy(skills: GalaxySkillStar[]): GalaxyLayout {
  const grouped = new Map<string, GalaxySkillStar[]>()
  for (const skill of skills) {
    const list = grouped.get(skill.category_slug)
    if (list) {
      list.push(skill)
    } else {
      grouped.set(skill.category_slug, [skill])
    }
  }

  const clusters: GalaxyCluster[] = []
  for (const [category, items] of grouped) {
    const ringIndex = hashString(category) % RINGS.length
    const radius = RINGS[ringIndex] ?? 0.46
    const base = ((hashString(category) % 360) / 360) * TAU
    const sorted = [...items].sort((a, b) => a.skill_slug.localeCompare(b.skill_slug))

    sorted.forEach((skill, index) => {
      const random = mulberry32(hashString(skill.skill_slug))
      const jitter = (random() - 0.5) * 0.08
      const angle = base + (index / sorted.length) * TAU + jitter

      const satellites: GalaxySatellite[] = []
      for (let sat = 0; sat < SATELLITES_PER_SKILL; sat += 1) {
        const satelliteAngle = random() * TAU
        const satelliteRadius = 0.012 + random() * 0.022
        satellites.push({
          key: `${skill.skill_slug}:${sat}`,
          dx: Math.cos(satelliteAngle) * satelliteRadius,
          dy: Math.sin(satelliteAngle) * satelliteRadius,
          size: 0.65 + random() * 0.8,
          phase: random() * TAU,
        })
      }

      clusters.push({
        key: skill.skill_slug,
        category,
        angle,
        radius,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        state: skill.star_state,
        brightness: clamp01(skill.brightness),
        tone: skill.star_state === 'lit' ? 'warm' : 'cool',
        satellites,
      })
    })
  }

  return {
    clusters,
    residual: buildResidualNodes(),
    rings: RINGS,
    spokes: SPOKES,
  }
}
