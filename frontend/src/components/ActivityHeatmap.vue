<script setup lang="ts">
import { computed } from 'vue'
import {
  buildHeatmap,
  type HeatmapCell,
  type TrendDay,
} from '@/lib/heatmap'

const props = defineProps<{
  points: TrendDay[]
}>()

const heatmap = computed(() => buildHeatmap(props.points))
const weekdayLabels = ['', '一', '', '三', '', '五', '']
const legendLevels = [0, 1, 2, 3, 4]

function cellTitle(cell: HeatmapCell): string {
  if (!cell.inRange) return ''
  return `${cell.date} · ${cell.count > 0 ? `${cell.count} 次训练` : '无训练'}`
}
</script>

<template>
  <div
    v-if="heatmap.weeks === 0"
    class="stat-hint"
  >
    暂无训练记录
  </div>

  <div
    v-else
    class="heatmap"
    role="group"
    :aria-label="`过去一年训练热力图，共 ${heatmap.total} 次训练`"
  >
    <div class="heatmap-scroll">
      <div class="heatmap-inner">
        <div class="heatmap-months-row">
          <span class="heatmap-month-spacer" aria-hidden="true"></span>
          <div class="heatmap-months" aria-hidden="true">
            <span
              v-for="(label, index) in heatmap.monthLabels"
              :key="index"
              class="heatmap-month"
            >
              {{ label }}
            </span>
          </div>
        </div>

        <div class="heatmap-body">
          <div class="heatmap-weekdays" aria-hidden="true">
            <span
              v-for="(label, index) in weekdayLabels"
              :key="index"
              class="heatmap-weekday"
            >
              {{ label }}
            </span>
          </div>

          <div
            class="heatmap-grid"
            :style="{
              gridTemplateColumns: `repeat(${heatmap.weeks}, var(--cell))`,
            }"
          >
            <span
              v-for="cell in heatmap.cells"
              :key="cell.date"
              class="heatmap-cell"
              :class="[
                `level-${cell.level}`,
                { 'is-outside': !cell.inRange },
              ]"
              :title="cellTitle(cell)"
              :aria-label="cellTitle(cell) || undefined"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="heatmap-footer">
      <span>共 {{ heatmap.total }} 次训练 · {{ heatmap.activeDays }} 天有记录</span>
      <span class="heatmap-legend" aria-hidden="true">
        少
        <i
          v-for="level in legendLevels"
          :key="level"
          :class="`level-${level}`"
        ></i>
        多
      </span>
    </div>
  </div>
</template>

<style scoped>
.heatmap {
  --cell: 12px;
  --gap: 3px;

  display: grid;
  gap: 12px;
}

.heatmap-scroll {
  overflow-x: auto;
  padding-bottom: 4px;
}

.heatmap-inner {
  width: max-content;
}

.heatmap-months-row {
  display: flex;
  gap: 7px;
  height: 15px;
  margin-bottom: 4px;
}

.heatmap-month-spacer {
  flex: none;
  width: 28px;
}

.heatmap-months {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: var(--cell);
  gap: var(--gap);
}

.heatmap-month {
  color: var(--text-subtle);
  font-size: 9px;
  line-height: 15px;
  white-space: nowrap;
}

.heatmap-body {
  display: flex;
  gap: 7px;
}

.heatmap-weekdays {
  display: grid;
  flex: none;
  grid-template-rows: repeat(7, var(--cell));
  gap: var(--gap);
  width: 28px;
}

.heatmap-weekday {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  color: var(--text-subtle);
  font-size: 9px;
}

.heatmap-grid {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: var(--cell);
  grid-template-rows: repeat(7, var(--cell));
  gap: var(--gap);
}

.heatmap-cell {
  width: var(--cell);
  height: var(--cell);
  border: 1px solid var(--border);
  border-radius: 2px;
  background: var(--surface-muted);
}

.heatmap-cell.is-outside {
  border-color: transparent;
  background: transparent;
}

.heatmap-cell.level-1,
.heatmap-legend i.level-1 {
  border-color: transparent;
  background: color-mix(in oklch, var(--accent) 24%, var(--surface-muted));
}

.heatmap-cell.level-2,
.heatmap-legend i.level-2 {
  border-color: transparent;
  background: color-mix(in oklch, var(--accent) 46%, var(--surface-muted));
}

.heatmap-cell.level-3,
.heatmap-legend i.level-3 {
  border-color: transparent;
  background: color-mix(in oklch, var(--accent) 68%, var(--surface-muted));
}

.heatmap-cell.level-4,
.heatmap-legend i.level-4 {
  border-color: transparent;
  background: color-mix(in oklch, var(--accent) 92%, var(--surface-muted));
}

.heatmap-cell:not(.is-outside):hover {
  outline: 1px solid var(--accent);
  outline-offset: 1px;
}

.heatmap-cell.is-outside:hover {
  outline: none;
}

.heatmap-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--text-subtle);
  font-size: 11px;
}

.heatmap-legend {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.heatmap-legend i {
  display: inline-block;
  width: 10px;
  height: 10px;
  border: 1px solid var(--border);
  border-radius: 2px;
  background: var(--surface-muted);
}
</style>
