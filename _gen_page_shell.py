# -*- coding: utf-8 -*-
"""统一页面骨架组件 + 驾驶舱按参考系统风格重做"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'

# ================= ① PageShell：统一页头 + 卡片骨架 =================
SHELL = '''<template>
  <div class="bp-page">
    <div class="bp-page-head">
      <div>
        <h2>{{ title }}</h2>
        <div v-if="desc" class="desc">{{ desc }}</div>
      </div>
      <div class="actions">
        <slot name="actions" />
      </div>
    </div>

    <!-- 搜索/筛选区 -->
    <div v-if="$slots.search" class="bp-card">
      <div class="bp-search">
        <slot name="search" />
      </div>
    </div>

    <!-- 主内容 -->
    <div class="bp-card">
      <div v-if="$slots.title || $slots.toolbar" class="head">
        <slot name="title" />
        <div class="actions">
          <slot name="toolbar" />
        </div>
      </div>
      <slot />
    </div>

    <slot name="extra" />
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  desc: { type: String, default: '' }
})
</script>
'''
io.open(os.path.join(FE, 'components', 'PageShell.vue'), 'w',
        encoding='utf-8').write(SHELL)
print('  ✓ components/PageShell.vue')

# ================= ② Dashboard 重做 =================
DASH = '''<template>
  <PageShell title="运营驾驶舱"
             :desc="`数据实时聚合 · 刷新间隔 ${screen?.refreshSeconds || 60}s`">
    <template #actions>
      <el-button type="primary" :loading="loading" @click="load">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
      <el-button @click="openScreen">全屏大屏</el-button>
    </template>

    <!-- 指标卡 -->
    <div class="bp-stat-row">
      <div v-for="w in widgets" :key="w.code" :class="['bp-stat', toneOf(w)]">
        <div class="label">{{ w.title }}</div>
        <div class="value">
          {{ fmt(w.value) }}<span v-if="w.unit" class="unit">{{ w.unit }}</span>
        </div>
      </div>
    </div>

    <!-- 资产与收支概览：图表区 -->
    <div class="bp-card">
      <div class="head">
        资产与收支概览
        <div class="actions">
          <el-radio-group v-model="chartMode" size="small">
            <el-radio-button value="house">房源结构</el-radio-button>
            <el-radio-button value="money">收支对比</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div ref="chartRef" style="height:300px" />
    </div>

    <!-- 指标明细 -->
    <div class="bp-card">
      <div class="head">指标明细</div>
      <el-table :data="metricRows" size="small" border>
        <el-table-column prop="label" label="指标名称" width="180" />
        <el-table-column prop="code" label="编码" width="240" />
        <el-table-column prop="value" label="当前值" align="right">
          <template #default="{ row }">
            <span class="num">{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="hint" label="说明" min-width="200" />
      </el-table>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { rptApi } from '@/api/modules'
import PageShell from '@/components/PageShell.vue'
import { metricLabel, metricUnit } from '@/constants/metrics'

const HINTS = {
  HOUSE_TOTAL: '组织范围内全部房源',
  HOUSE_OCCUPIED: '已出租（含已配租）',
  HOUSE_VACANT: '可配租的空置房源',
  OCCUPANCY_RATE: '已出租 / 房源总数',
  BILL_UNPAID_AMOUNT: '未核销的应收金额',
  BILL_UNPAID_COUNT: '未缴清的账单数',
  PAYMENT_TOTAL_AMOUNT: '累计登记收款',
  ACCESS_TODAY_COUNT: '当日门禁开门次数',
  ACCESS_ABNORMAL_COUNT: '重复/尾随/超时等异常'
}

const loading = ref(false)
const screen = ref(null)
const widgets = ref([])
const metrics = ref({})
const chartMode = ref('house')
const chartRef = ref()
let chart = null

function fmt(v) {
  if (v === null || v === undefined) return '-'
  const n = Number(v)
  return Number.isFinite(n) ? n.toLocaleString('zh-CN') : v
}

function toneOf(w) {
  const n = Number(w.value)
  if (w.code === 'ACCESS_ABNORMAL_COUNT' && n > 0) return 'danger'
  if (w.code === 'BILL_UNPAID_COUNT' && n > 0) return 'warn'
  if (w.code === 'OCCUPANCY_RATE') return 'ok'
  return ''
}

const metricRows = computed(() =>
  Object.entries(metrics.value)
    .filter(([k]) => k !== 'generatedAt')
    .map(([code, value]) => ({
      code,
      label: metricLabel(code),
      value: fmt(value) + (metricUnit(code) || ''),
      hint: HINTS[code] || '-'
    }))
)

function valueOf(code) {
  return Number(metrics.value[code] || 0)
}

function renderChart() {
  if (!chart) return
  const axis = {
    axisLine: { lineStyle: { color: '#d9d9d9' } },
    axisLabel: { color: 'rgba(0,0,0,0.45)', fontSize: 12 },
    splitLine: { lineStyle: { color: '#f0f0f0' } }
  }
  if (chartMode.value === 'house') {
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: 'rgba(0,0,0,0.65)' } },
      series: [{
        type: 'pie', radius: ['45%', '68%'], center: ['50%', '45%'],
        label: { formatter: '{b}\\n{c}', color: 'rgba(0,0,0,0.65)' },
        data: [
          { name: '已出租', value: valueOf('HOUSE_OCCUPIED'), itemStyle: { color: '#1890ff' } },
          { name: '空置', value: valueOf('HOUSE_VACANT'), itemStyle: { color: '#faad14' } },
          { name: '其他', itemStyle: { color: '#d9d9d9' },
            value: Math.max(0, valueOf('HOUSE_TOTAL') - valueOf('HOUSE_OCCUPIED')
              - valueOf('HOUSE_VACANT')) }
        ]
      }]
    }, true)
  } else {
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 70, right: 20, top: 20, bottom: 30 },
      xAxis: { type: 'category', data: ['欠费金额', '累计收款', '今日开门'],
               ...axis },
      yAxis: { type: 'value', ...axis },
      series: [{
        type: 'bar', barWidth: 36,
        itemStyle: { color: '#1890ff', borderRadius: [2, 2, 0, 0] },
        data: [valueOf('BILL_UNPAID_AMOUNT'), valueOf('PAYMENT_TOTAL_AMOUNT'),
               valueOf('ACCESS_TODAY_COUNT')]
      }]
    }, true)
  }
}

watch(chartMode, renderChart)

async function load() {
  loading.value = true
  try {
    const data = await rptApi.screenData('OVERVIEW')
    screen.value = data
    widgets.value = (data.widgets || []).map((w) => ({
      ...w,
      title: (!w.title || w.title === w.code ? metricLabel(w.code) : w.title),
      unit: metricUnit(w.code)
    }))
    metrics.value = await rptApi.metrics()
    await nextTick()
    if (!chart) {
      chart = echarts.init(chartRef.value)
      window.addEventListener('resize', onResize)
    }
    renderChart()
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

function onResize() { chart && chart.resize() }
function openScreen() {
  window.open('./view-screen.html', 'bp-screen', 'width=1600,height=900')
}

onMounted(load)
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart && chart.dispose()
})
</script>

<style scoped>
.num { font-variant-numeric: tabular-nums; }
</style>
'''
io.open(os.path.join(FE, 'views', 'Dashboard.vue'), 'w',
        encoding='utf-8').write(DASH)
print('  ✓ Dashboard.vue 重做（页头 + 指标卡 + 图表 + 明细）')
