export interface TrendDay {
  date: string
  sessions: number
}

export interface HeatmapCell {
  date: string
  count: number
  level: number
  inRange: boolean
  week: number
  weekday: number
}

export interface HeatmapData {
  cells: HeatmapCell[]
  weeks: number
  monthLabels: string[]
  total: number
  activeDays: number
  startDate: string
  endDate: string
}

const DAY_MS = 86_400_000

function parseDate(value: string): Date {
  return new Date(`${value}T00:00:00Z`)
}

function formatDate(value: Date): string {
  return value.toISOString().slice(0, 10)
}

export function activityLevel(count: number): number {
  if (count <= 0) return 0
  if (count === 1) return 1
  if (count <= 3) return 2
  if (count <= 6) return 3
  return 4
}

export function buildHeatmap(days: TrendDay[]): HeatmapData {
  if (days.length === 0) {
    return {
      cells: [],
      weeks: 0,
      monthLabels: [],
      total: 0,
      activeDays: 0,
      startDate: '',
      endDate: '',
    }
  }

  const sorted = [...days].sort((a, b) => a.date.localeCompare(b.date))
  const firstDay = sorted[0]
  const lastDay = sorted[sorted.length - 1]
  if (!firstDay || !lastDay) {
    return {
      cells: [],
      weeks: 0,
      monthLabels: [],
      total: 0,
      activeDays: 0,
      startDate: '',
      endDate: '',
    }
  }

  const counts = new Map(sorted.map((day) => [day.date, day.sessions]))
  const first = parseDate(firstDay.date)
  const last = parseDate(lastDay.date)
  const start = new Date(first.getTime() - first.getUTCDay() * DAY_MS)
  const totalDays = Math.ceil(
    (last.getTime() - start.getTime() + DAY_MS) / DAY_MS,
  )
  const weeks = Math.max(1, Math.ceil(totalDays / 7))
  const monthLabels: string[] = new Array(weeks).fill('')
  const cells: HeatmapCell[] = []

  for (let index = 0; index < weeks * 7; index += 1) {
    const date = new Date(start.getTime() + index * DAY_MS)
    const key = formatDate(date)
    const inRange =
      date.getTime() >= first.getTime() && date.getTime() <= last.getTime()
    const count = inRange ? (counts.get(key) ?? 0) : 0
    const level = inRange ? activityLevel(count) : 0
    const week = Math.floor(index / 7)

    cells.push({
      date: key,
      count,
      level,
      inRange,
      week,
      weekday: index % 7,
    })

    if (inRange && date.getUTCDate() === 1) {
      monthLabels[week] = `${date.getUTCMonth() + 1}月`
    }
  }

  if (!monthLabels[0]) {
    monthLabels[0] = `${first.getUTCMonth() + 1}月`
  }

  const total = sorted.reduce((sum, day) => sum + day.sessions, 0)
  const activeDays = sorted.filter((day) => day.sessions > 0).length

  return {
    cells,
    weeks,
    monthLabels,
    total,
    activeDays,
    startDate: formatDate(start),
    endDate: formatDate(last),
  }
}
