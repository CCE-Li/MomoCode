import { describe, expect, it } from 'vitest'
import { activityLevel, buildHeatmap, type TrendDay } from '@/lib/heatmap'

const DAY_MS = 86_400_000

function iso(date: Date): string {
  return date.toISOString().slice(0, 10)
}

describe('activity heatmap', () => {
  it('maps session counts to five levels', () => {
    expect([0, 1, 2, 3, 4, 6, 7, 12].map(activityLevel)).toEqual([
      0, 1, 2, 2, 3, 3, 4, 4,
    ])
  })

  it('aligns the first cell to the Sunday before the first day', () => {
    const days: TrendDay[] = [
      { date: '2026-11-09', sessions: 1 },
      { date: '2026-11-10', sessions: 3 },
      { date: '2026-11-15', sessions: 0 },
    ]
    const data = buildHeatmap(days)
    const first = new Date('2026-11-09T00:00:00Z')
    const sunday = new Date(first.getTime() - first.getUTCDay() * DAY_MS)

    expect(data.cells[0]?.date).toBe(iso(sunday))
    expect(data.cells).toHaveLength(data.weeks * 7)
    expect(data.monthLabels[0]).toBe('11月')

    const firstCell = data.cells[first.getUTCDay()]
    expect(firstCell?.date).toBe('2026-11-09')
    expect(firstCell?.count).toBe(1)
    expect(firstCell?.level).toBe(1)
    expect(firstCell?.inRange).toBe(true)

    expect(data.total).toBe(4)
    expect(data.activeDays).toBe(2)
  })

  it('marks padding days outside the range', () => {
    const data = buildHeatmap([{ date: '2026-11-09', sessions: 2 }])
    expect(data.cells.some((cell) => !cell.inRange)).toBe(true)
    expect(
      data.cells.filter((cell) => !cell.inRange).every((cell) => cell.level === 0),
    ).toBe(true)
  })

  it('returns an empty layout without days', () => {
    expect(buildHeatmap([])).toMatchObject({
      cells: [],
      weeks: 0,
      monthLabels: [],
      total: 0,
      activeDays: 0,
    })
  })
})
