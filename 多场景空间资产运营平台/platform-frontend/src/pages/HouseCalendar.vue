<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const houses = ref([])
const contracts = ref([])
const orders = ref([])
const error = ref('')
const start = ref(new Date())

const days = computed(() => Array.from({ length: 14 }, (_, i) => {
  const d = new Date(start.value)
  d.setDate(d.getDate() + i)
  return d
}))
const dateKey = (d) => {
  const x = new Date(d)
  const m = String(x.getMonth() + 1).padStart(2, '0')
  const day = String(x.getDate()).padStart(2, '0')
  return `${x.getFullYear()}-${m}-${day}`
}
const rows = computed(() => houses.value.slice(0, 60).map(h => {
  const cells = days.value.map(d => {
    const key = dateKey(d)
    const contract = contracts.value.find(c => c.contractStatus === 'ACTIVE' && c.houseId === h.id && key >= String(c.startDate).slice(0, 10) && key <= String(c.endDate).slice(0, 10))
    if (contract) return { key, status: 'CONTRACT', label: contract.personName }
    const order = orders.value.find(o => o.houseId === h.id && ['CONFIRMED', 'CHECKED_IN'].includes(o.orderStatus) && key >= String(o.startDate).slice(0, 10) && key < String(o.endDate).slice(0, 10))
    if (order) return { key, status: 'SHORT', label: order.guestName }
    return { key, status: 'VACANT', label: '' }
  })
  return { house: h, cells }
}))

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
    const [h, c, o] = await Promise.all([api.houses(id), api.contracts(id), api.shortRentOrders(id)])
    houses.value = h; contracts.value = c; orders.value = o
  } catch (e) { error.value = e.message }
}

function move(delta) {
  const d = new Date(start.value)
  d.setDate(d.getDate() + delta)
  start.value = d
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>日房态</h2><p>{{ project?.orgName || '未选择项目' }} · 未来 14 天房屋占用</p></div>
        <div class="row"><button class="sm" @click="move(-7)">前 7 天</button><button class="sm" @click="start = new Date()">今天</button><button class="sm" @click="move(7)">后 7 天</button></div>
      </div>
      <div class="row" style="margin-bottom:10px">
        <span class="badge green">空置</span><span class="badge blue">合同</span><span class="badge orange">短租</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>房屋</th><th v-for="d in days" :key="dateKey(d)" class="small">{{ dateKey(d).slice(5) }}</th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.house.id">
              <td class="mono">{{ r.house.houseCode }}<div class="small muted">{{ r.house.houseName }}</div></td>
              <td v-for="c in r.cells" :key="c.key" :title="c.label">
                <span class="cal-cell" :class="c.status === 'CONTRACT' ? 'blue' : c.status === 'SHORT' ? 'orange' : 'green'" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="!rows.length" class="empty">暂无房源</div>
    </div>
  </div>
</template>
