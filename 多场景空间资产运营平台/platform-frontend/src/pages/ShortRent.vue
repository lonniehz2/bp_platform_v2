<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'

const project = ref(null)
const houses = ref([])
const orders = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ houseId: '', guestName: '', guestPhone: '', startDate: '', endDate: '', amount: 0, remark: '' })
const statusClass = (s) => ({ CONFIRMED: 'blue', CHECKED_IN: 'orange', COMPLETED: 'green', CANCELLED: 'red' }[s] || '')

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
    const [h, o] = await Promise.all([api.houses(project.value.id), api.shortRentOrders(project.value.id)])
    houses.value = h; orders.value = o
    if (!form.houseId && h.length) form.houseId = h[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.guestName.trim() || !form.startDate || !form.endDate) throw new Error('请填写入住人和起止日期')
    await api.createShortRentOrder({
      projectId: project.value.id, houseId: form.houseId || null, guestName: form.guestName.trim(),
      guestPhone: form.guestPhone, startDate: form.startDate, endDate: form.endDate,
      amount: Number(form.amount || 0), remark: form.remark
    })
    form.guestName = ''; form.guestPhone = ''; form.remark = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function update(o, status) {
  busy.value = true; error.value = ''
  try { await api.updateShortRentStatus(o.id, status); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>短租订单</h2><p>{{ project?.orgName || '未选择项目' }} · 短租、日房态</p></div><span class="badge blue">{{ orders.length }} 单</span></div>
      <div class="row">
        <div class="field"><label>房屋</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索房屋" /></div>
        <div class="field"><label>入住人</label><input v-model="form.guestName" /></div>
        <div class="field"><label>手机号</label><input v-model="form.guestPhone" /></div>
        <div class="field"><label>入住</label><input v-model="form.startDate" type="date" /></div>
        <div class="field"><label>离店</label><input v-model="form.endDate" type="date" /></div>
        <div class="field"><label>金额</label><input v-model.number="form.amount" type="number" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('shortrent')" class="primary" :disabled="busy" @click="create">新建订单</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>订单列表</h2><span class="small muted">待确认 → 已确认 → 入住 → 完成 / 取消</span></div>
      <div v-if="!orders.length" class="empty">暂无短租订单</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>订单号</th><th>房屋</th><th>入住人</th><th>入住/离店</th><th>晚数</th><th>金额</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id">
              <td class="mono">{{ o.orderNo }}</td><td>{{ o.houseName || '-' }}</td><td>{{ o.guestName }}</td>
              <td class="small">{{ o.startDate }} ~ {{ o.endDate }}</td><td>{{ o.nights }}</td><td>¥{{ Number(o.amount || 0).toFixed(2) }}</td>
              <td><span class="badge" :class="statusClass(o.orderStatus)">{{ o.orderStatus }}</span></td>
              <td class="row">
                <button v-if="can('shortrent') && o.orderStatus === 'PENDING'" class="sm" @click="update(o, 'CONFIRMED')">确认</button>
                <button v-if="can('shortrent') && o.orderStatus === 'CONFIRMED'" class="sm" @click="update(o, 'CHECKED_IN')">入住</button>
                <button v-if="can('shortrent') && o.orderStatus === 'CHECKED_IN'" class="sm" @click="update(o, 'COMPLETED')">完成</button>
                <button v-if="can('shortrent') && ['PENDING','CONFIRMED'].includes(o.orderStatus)" class="sm danger" @click="update(o, 'CANCELLED')">取消</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
