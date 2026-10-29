<template>
  <div class="trend">
    <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none" class="trend-svg">
      <!-- 横向网格 -->
      <line v-for="(g, i) in gridLines" :key="'g' + i"
            :x1="PAD_L" :x2="W - PAD_R" :y1="g.y" :y2="g.y"
            stroke="var(--el-border-color-lighter)" stroke-width="1" />
      <text v-for="(g, i) in gridLines" :key="'t' + i"
            :x="PAD_L - 6" :y="g.y + 4" text-anchor="end" class="axis-text">
        {{ g.label }}
      </text>

      <!-- 面积 + 折线 -->
      <polygon :points="areaPoints" :fill="color" fill-opacity="0.10" />
      <polyline :points="linePoints" fill="none" :stroke="color" stroke-width="2"
                stroke-linejoin="round" stroke-linecap="round" />

      <!-- 数据点 -->
      <g v-for="(p, i) in points" :key="'p' + i">
        <circle :cx="p.x" :cy="p.y" r="4" :fill="color" />
        <circle :cx="p.x" :cy="p.y" r="8" fill="transparent">
          <title>{{ p.label }}：{{ p.text }}</title>
        </circle>
        <text :x="p.x" :y="H - 8" text-anchor="middle" class="axis-text">{{ p.label }}</text>
        <text :x="p.x" :y="p.y - 10" text-anchor="middle" class="value-text">
          {{ p.text }}
        </text>
      </g>
    </svg>
  </div>
</template>

<script setup>
/**
 * 轻量折线图（纯 SVG，无第三方图表库依赖）。
 *
 * 用于能耗分析的月度趋势：数据点可选 3~24 个。
 */
import { computed } from 'vue'

const props = defineProps({
  // [{ label: '2026-08', value: 123.45 }]
  rows: { type: Array, default: () => [] },
  color: { type: String, default: '#409eff' },
  unit: { type: String, default: '' },
  height: { type: Number, default: 220 }
})

const W = 620
const H = computed(() => props.height)
const PAD_L = 62
const PAD_R = 44
const PAD_T = 26

const nums = computed(() => props.rows.map((r) => Number(r.value) || 0))
const maxV = computed(() => Math.max(1, ...nums.value))
const minV = computed(() => 0)

const xOf = (i) => {
  const n = props.rows.length
  if (n <= 1) return PAD_L + (W - PAD_L - PAD_R) / 2
  return PAD_L + ((W - PAD_L - PAD_R) * i) / (n - 1)
}
const yOf = (v) => {
  const plot = H.value - PAD_T - 24
  const ratio = (v - minV.value) / (maxV.value - minV.value || 1)
  return PAD_T + plot * (1 - ratio)
}

function fmt(v) {
  const n = Number(v) || 0
  if (n >= 10000) return (n / 10000).toFixed(1) + ' 万'
  if (n >= 100) return String(Math.round(n))
  return String(Math.round(n * 100) / 100)
}

const points = computed(() => props.rows.map((r, i) => ({
  x: xOf(i),
  y: yOf(Number(r.value) || 0),
  label: String(r.label || ''),
  // 0 值不显示标签，避免与坐标轴重叠
  text: (Number(r.value) || 0) === 0 ? '' : fmt(r.value)
})))

const linePoints = computed(() => points.value.map((p) => `${p.x},${p.y}`).join(' '))
const areaPoints = computed(() => {
  if (!points.value.length) return ''
  const base = H.value - 24
  const first = points.value[0]
  const last = points.value[points.value.length - 1]
  return `${first.x},${base} ` + linePoints.value + ` ${last.x},${base}`
})

const gridLines = computed(() => {
  const out = []
  for (let i = 0; i <= 4; i++) {
    const v = (maxV.value * i) / 4
    out.push({ y: yOf(v), label: fmt(v) })
  }
  return out
})
</script>

<style scoped>
.trend { width: 100%; }
.trend-svg { width: 100%; height: auto; display: block; }
.axis-text { font-size: 11px; fill: var(--el-text-color-secondary); }
.value-text { font-size: 11px; fill: var(--el-text-color-regular); font-weight: 600; }
</style>
