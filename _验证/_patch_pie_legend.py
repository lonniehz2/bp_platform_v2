# -*- coding: utf-8 -*-
import io

p = r'..\frontend\src\views\Dashboard.vue'
s = io.open(p, encoding='utf-8').read()

# 1) 图例数据
if 'const pieItems' not in s:
    s = s.replace('''/** 按图表容器（逐级向上）的实际背景挑选可读的文字颜色 */''',
'''/** 房源结构饼图数据（图例与图表共用） */
const pieItems = computed(() => {
  const occupied = Number(metrics.value.HOUSE_OCCUPIED || houseStat.value.occupied || 0)
  const vacant = Number(metrics.value.HOUSE_VACANT || houseStat.value.vacant || 0)
  const pending = Number(metrics.value.PENDING_ALLOC || houseStat.value.pending || 0)
  return [
    { name: '已出租', value: occupied, color: '#1890ff' },
    { name: '空置', value: vacant, color: '#faad14' },
    { name: '待配租', value: pending, color: '#722ed1' }
  ]
})

/** 按图表容器（逐级向上）的实际背景挑选可读的文字颜色 */''', 1)

# 2) 模板：图表下加图例
if 'class="pie-legend"' not in s:
    s = s.replace('''        <div ref="chartRef" class="chart" />
      </div>''','''        <div ref="chartRef" class="chart" />
        <div class="pie-legend">
          <span v-for="x in pieItems" :key="x.name" class="pie-legend-item">
            <i :style="{ background: x.color }" />
            <em>{{ x.name }}</em>
            <b>{{ x.value }}</b>
          </span>
        </div>
      </div>''', 1)

# 3) 图表配置：图例交给 HTML，饼图缩小并上移
old = '''  const occupied = Number(metrics.value.HOUSE_OCCUPIED || houseStat.value.occupied || 0)
  const vacant = Number(metrics.value.HOUSE_VACANT || houseStat.value.vacant || 0)
  const pending = Number(metrics.value.PENDING_ALLOC || houseStat.value.pending || 0)
  // 文字颜色跟随容器背景亮度：深色卡片用浅色字，浅色卡片用深色字，
  // 否则深色风格下标签几乎看不见（此前硬编码 rgba(0,0,0,0.75)）
  const textColor = contrastText()'''
new = '''  // 文字颜色跟随容器背景亮度：深色卡片用浅色字，浅色卡片用深色字
  const textColor = contrastText()'''
if old in s:
    s = s.replace(old, new, 1)

old_legend = '''  legend: {
    bottom: 0,
    left: 'center',
    orient: 'horizontal',
    // 三个色块强制排成一行：缩小字号与间距，且图例不带数量（数量在 tooltip 里）
    itemGap: 10,
    itemWidth: 10,
    itemHeight: 10,
    textStyle: { color: textColor, fontSize: 11, textBorderColor: 'rgba(255,255,255,0.9)', textBorderWidth: 2 }
  },'''
new_legend = '''  legend: { show: false },'''
if old_legend in s:
    s = s.replace(old_legend, new_legend, 1)

s = s.replace("type: 'pie',\n      radius: ['46%', '68%'],\n      center: ['50%', '42%'],",
              "type: 'pie',\n      radius: ['42%', '62%'],\n      center: ['50%', '46%'],", 1)

old_label = '''    label: {
      show: true,
      // 名称 + 百分比；文字带白色描边光晕，浅色/深色底都能看清
      // （此前按背景亮度选色，在「浏览器强制暗色」等情况下会失效）
      formatter: '{b}\\n{d}%',
      color: '#1f1f1f',
      textBorderColor: 'rgba(255,255,255,0.95)',
      textBorderWidth: 3,
      fontSize: 12,
      lineHeight: 16,
      overflow: 'none'
    },'''
new_label = '''    label: {
      show: true,
      formatter: '{d}%',
      color: textColor,
      fontSize: 11,
      lineHeight: 14,
      overflow: 'none'
    },'''
if old_label in s:
    s = s.replace(old_label, new_label, 1)

old_data = '''    data: [
      { name: '已出租', value: occupied, itemStyle: { color: '#1890ff' } },
      { name: '空置', value: vacant, itemStyle: { color: '#faad14' } },
      // 原 #52c41a（绿）与空置橙在视觉上偏近，改为紫色拉开色相差
      { name: '待配租', value: pending, itemStyle: { color: '#722ed1' } }
    ]'''
new_data = '''    data: pieItems.value.map((x) => ({
      name: x.name, value: x.value, itemStyle: { color: x.color }
    }))'''
if old_data in s:
    s = s.replace(old_data, new_data, 1)

# 4) 样式
if '.pie-legend' not in s:
    s = s.replace('''.chart { flex: 1; min-height: 150px; }''','''.chart { flex: 1; min-height: 118px; }
.pie-legend {
  display: flex; justify-content: center; flex-wrap: wrap;
  gap: 6px 16px; padding: 4px 0 2px;
  font-size: 12px; color: var(--el-text-color-regular);
}
.pie-legend-item { display: inline-flex; align-items: center; gap: 5px; }
.pie-legend-item i {
  width: 8px; height: 8px; border-radius: 2px; display: inline-block;
}
.pie-legend-item em { font-style: normal; }
.pie-legend-item b { color: var(--el-text-color-primary); font-weight: 600; }''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('pie legend redesigned')
