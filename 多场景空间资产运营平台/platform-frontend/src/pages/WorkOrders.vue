<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const houses = ref([])
const persons = ref([])
const orders = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ orderType: 'REPAIR', title: '', description: '', houseId: '', personId: '', priority: 'NORMAL', assigneeName: '维修班组' })

const statusClass = (s) => ({ DONE: 'green', PROCESSING: 'orange', CLOSED: 'blue' }[s] || '')

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
    const [h, p, o] = await Promise.all([api.houses(id), api.persons(), api.workOrders(id)])
    houses.value = h; persons.value = p; orders.value = o
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error('请填写工单标题')
    await api.createWorkOrder({
      projectId: project.value.id, orderType: form.orderType, title: form.title.trim(),
      description: form.description, houseId: form.houseId || null, personId: form.personId || null,
      priority: form.priority, assigneeName: form.assigneeName
    })
    form.title = ''; form.description = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function update(order, status) {
  busy.value = true; error.value = ''
  try {
    await api.updateWorkOrder(order.id, { orderStatus: status, assigneeName: order.assigneeName || '维修班组' })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>服务工单</h2><p>{{ project?.orgName || '未选择项目' }} · 报修、投诉、巡检</p></div><span class="badge blue">{{ orders.length }} 单</span></div>
      <div class="row">
        <div class="field"><label>类型</label><select v-model="form.orderType"><option value="REPAIR">报修</option><option value="COMPLAINT">投诉</option><option value="INSPECTION">巡检</option><option value="OTHER">其他</option></select></div>
        <div class="field" style="flex:2"><label>标题</label><input v-model="form.title" placeholder="如 厨房漏水" /></div>
        <div class="field"><label>房屋</label><select v-model="form.houseId"><option value="">不关联</option><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>
        <div class="field"><label>人员</label><select v-model="form.personId"><option value="">不关联</option><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select></div>
        <div class="field"><label>优先级</label><select v-model="form.priority"><option value="LOW">低</option><option value="NORMAL">普通</option><option value="HIGH">高</option></select></div>
        <div class="field"><label>处理人</label><input v-model="form.assigneeName" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('service')" class="primary" :disabled="busy" @click="create">新建工单</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>工单列表</h2><span class="small muted">处理中 → 完成 / 关闭</span></div>
      <div v-if="!orders.length" class="empty">暂无工单</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>工单号</th><th>类型</th><th>标题</th><th>房屋</th><th>人员</th><th>处理人</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id">
              <td class="mono">{{ o.orderNo }}</td><td>{{ o.orderType }}</td><td>{{ o.title }}</td>
              <td>{{ o.houseName || '-' }}</td><td>{{ o.personName || '-' }}</td><td>{{ o.assigneeName || '-' }}</td>
              <td><span class="badge" :class="statusClass(o.orderStatus)">{{ o.orderStatus }}</span></td>
              <td class="row">
                <button v-if="can('service') && o.orderStatus === 'PENDING'" class="sm" @click="update(o, 'PROCESSING')">受理</button>
                <button v-if="can('service') && o.orderStatus === 'PROCESSING'" class="sm" @click="update(o, 'DONE')">完成</button>
                <button v-if="can('service') && o.orderStatus === 'DONE'" class="sm" @click="update(o, 'CLOSED')">关闭</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
