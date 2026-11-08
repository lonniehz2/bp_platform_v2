<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const bills = ref([])
const contracts = ref([])
const houses = ref([])
const alerts = ref([])
const error = ref('')
const busy = ref(false)
const lastRun = ref('')

const today = new Date()
const dateKey = (d) => String(d).slice(0, 10)
const daysBetween = (a, b) => Math.ceil((new Date(b) - new Date(a)) / 86400000)

const findings = computed(() => {
  const out = []
  const overdue = bills.value.filter(b => b.billStatus === 'OVERDUE' || (b.billStatus !== 'PAID' && b.periodEnd && daysBetween(b.periodEnd, today) > 0))
  if (overdue.length) {
    out.push({ key: 'OVERDUE', level: '高', title: `逾期账单 ${overdue.length} 笔`, detail: `欠费金额约 ¥${overdue.reduce((s, b) => s + Math.max(0, Number(b.payableAmount || b.amount || 0) - Number(b.paidAmount || 0)), 0).toLocaleString('zh-CN')}`, suggestion: '生成催缴告警' })
  }
  const vacant = houses.value.filter(h => h.houseStatus === 'VACANT')
  if (vacant.length > 10) out.push({ key: 'VACANT', level: '中', title: `空置房源 ${vacant.length} 套`, detail: '空置率偏高，建议安排配租', suggestion: '生成风险提示' })
  const expiring = contracts.value.filter(c => c.contractStatus === 'ACTIVE' && c.endDate && daysBetween(today, c.endDate) >= 0 && daysBetween(today, c.endDate) <= 60)
  if (expiring.length) out.push({ key: 'EXPIRING', level: '中', title: `60 天内到期合同 ${expiring.length} 份`, detail: '建议提前发起续租或退租', suggestion: '生成续租提醒' })
  const pending = alerts.value.filter(a => a.alertStatus === 'PENDING')
  if (pending.length) out.push({ key: 'ALERT', level: '低', title: `待处理告警 ${pending.length} 条`, detail: '存在未闭环告警', suggestion: '进入告警中心' })
  return out
})

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
    const [b, c, h, a] = await Promise.all([api.bills(id), api.contracts(id), api.houses(id), api.alerts(id)])
    bills.value = b; contracts.value = c; houses.value = h; alerts.value = a
    lastRun.value = new Date().toLocaleString('zh-CN')
  } catch (e) { error.value = e.message }
}

async function runPatrol() {
  busy.value = true; error.value = ''
  try {
    for (const f of findings.value) {
      if (f.key === 'ALERT') continue
      await api.createAlert({
        projectId: project.value.id,
        alertType: f.key === 'OVERDUE' ? 'OVERDUE' : 'RISK',
        alertLevel: f.level === '高' ? 'HIGH' : 'NORMAL',
        title: `自动巡查：${f.title}`,
        content: f.detail
      })
    }
    lastRun.value = new Date().toLocaleString('zh-CN')
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>自动巡查</h2><p>{{ project?.orgName || '未选择项目' }} · 欠费、空置、合同到期、告警闭环</p></div>
        <div class="row"><span class="small muted">最近巡查 {{ lastRun || '-' }}</span><button class="primary" :disabled="busy" @click="runPatrol">执行巡查</button></div>
      </div>
      <div class="grid cards">
        <div class="card"><div class="label">巡查规则</div><div class="value">4</div><div class="hint">欠费/空置/到期/告警</div></div>
        <div class="card"><div class="label">发现问题</div><div class="value">{{ findings.length }}</div><div class="hint">当前规则</div></div>
        <div class="card"><div class="label">待处理告警</div><div class="value">{{ alerts.filter(a => a.alertStatus === 'PENDING').length }}</div><div class="hint">未闭环</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>巡查结果</h2><span class="small muted">执行巡查会生成告警</span></div>
      <div v-if="!findings.length" class="empty">未发现异常</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>级别</th><th>问题</th><th>说明</th><th>建议</th></tr></thead>
          <tbody>
            <tr v-for="f in findings" :key="f.key">
              <td><span class="badge" :class="f.level === '高' ? 'red' : f.level === '中' ? 'orange' : 'blue'">{{ f.level }}</span></td>
              <td>{{ f.title }}</td><td>{{ f.detail }}</td><td>{{ f.suggestion }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
