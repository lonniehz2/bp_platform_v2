<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const meters = ref([])
const summary = ref([])
const readings = ref({})
const error = ref('')

const detail = computed(() => meters.value.map(m => {
  const list = readings.value[m.id] || []
  const last = list[0]
  return { ...m, lastUsage: last ? Number(last.usageAmount || 0) : 0, lastDate: last?.readingDate || '-' }
}).sort((a, b) => b.lastUsage - a.lastUsage))
const totalUsage = computed(() => detail.value.reduce((s, m) => s + m.lastUsage, 0))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const id = project.value.id
    const [m, s] = await Promise.all([api.meters(id), api.meterSummary(id)])
    meters.value = m; summary.value = s
    const map = {}
    for (const meter of m.slice(0, 30)) {
      try { map[meter.id] = await api.meterReadings(meter.id) } catch { map[meter.id] = [] }
    }
    readings.value = map
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card"><div class="label">表计数量</div><div class="value">{{ meters.length }}</div><div class="hint">{{ project?.orgName || '未选择项目' }}</div></div>
      <div v-for="s in summary" :key="s.meterType" class="card">
        <div class="label">{{ s.meterType }}</div><div class="value">{{ Number(s.usageAmount || 0).toLocaleString('zh-CN') }}</div><div class="hint">{{ s.meterCount }} 只表</div>
      </div>
      <div class="card"><div class="label">最近用量合计</div><div class="value">{{ totalUsage.toLocaleString('zh-CN') }}</div><div class="hint">按最近一次抄表</div></div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>表计用量</h2><p>按最近一次抄表用量排序</p></div><RouterLink to="/meters">去抄表</RouterLink></div>
      <div v-if="!detail.length" class="empty">暂无表计数据</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>表号</th><th>类型</th><th>房屋</th><th>当前读数</th><th>最近用量</th><th>抄表日期</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="m in detail" :key="m.id">
              <td class="mono">{{ m.meterNo }}</td><td>{{ m.meterType }}</td><td>{{ m.houseName }}</td>
              <td>{{ Number(m.currentReading || 0).toLocaleString('zh-CN') }}</td>
              <td><strong>{{ m.lastUsage.toLocaleString('zh-CN') }}</strong></td>
              <td class="small">{{ m.lastDate }}</td>
              <td><span class="badge green">{{ m.meterStatus }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
