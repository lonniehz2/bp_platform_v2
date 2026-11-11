<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const houses = ref([])
const persons = ref([])
const orders = ref([])
const detailOrder = ref(null)
const error = ref('')
const busy = ref(false)
const form = reactive({ orderType: 'REPAIR', title: '', description: '', houseId: '', personId: '', priority: 'NORMAL', assigneeName: t('workOrders.defaultAssignee') })

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
    if (!form.title.trim()) throw new Error(t('workOrders.required'))
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
    await api.updateWorkOrder(order.id, { orderStatus: status, assigneeName: order.assigneeName || t('workOrders.defaultAssignee') })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('workOrders.title') }}</h2><p>{{ project?.orgName || t('workOrders.noProject') }} · {{ t('workOrders.subtitle') }}</p></div><span class="badge blue">{{ orders.length }} {{ t('workOrders.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('workOrders.type') }}</label><select v-model="form.orderType"><option value="REPAIR">{{ t('workOrders.repair') }}</option><option value="COMPLAINT">{{ t('workOrders.complaint') }}</option><option value="INSPECTION">{{ t('workOrders.inspection') }}</option><option value="OTHER">{{ t('workOrders.other') }}</option></select></div>
        <div class="field" style="flex:2"><label>{{ t('workOrders.titleCol') }}</label><input v-model="form.title" :placeholder="t('workOrders.titlePlaceholder')" /></div>
        <div class="field"><label>{{ t('workOrders.house') }}</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('workOrders.searchHouse')" clearable /></div>
        <div class="field"><label>{{ t('workOrders.person') }}</label><SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('workOrders.searchPerson')" clearable /></div>
        <div class="field"><label>{{ t('workOrders.priority') }}</label><select v-model="form.priority"><option value="LOW">{{ t('workOrders.low') }}</option><option value="NORMAL">{{ t('workOrders.normal') }}</option><option value="HIGH">{{ t('workOrders.high') }}</option></select></div>
        <div class="field"><label>{{ t('workOrders.assignee') }}</label><input v-model="form.assigneeName" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('service')" class="primary" :disabled="busy" @click="create">{{ t('workOrders.add') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('workOrders.list') }}</h2><span class="small muted">{{ t('workOrders.hint') }}</span></div>
      <div v-if="!orders.length" class="empty">{{ t('workOrders.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('workOrders.orderNo') }}</th><th>{{ t('workOrders.type') }}</th><th>{{ t('workOrders.titleCol') }}</th><th>{{ t('workOrders.house') }}</th><th>{{ t('workOrders.person') }}</th><th>{{ t('workOrders.assignee') }}</th><th>{{ t('workOrders.status') }}</th><th>{{ t('workOrders.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id">
              <td class="mono">{{ o.orderNo }}</td><td>{{ o.orderType }}</td><td>{{ o.title }}</td>
              <td>{{ o.houseName || '-' }}</td><td>{{ o.personName || '-' }}</td><td>{{ o.assigneeName || '-' }}</td>
              <td><span class="badge" :class="statusClass(o.orderStatus)">{{ o.orderStatus }}</span></td>
              <td class="row">
                <RouterLink class="sm" :to="`/guarantee/detail/WORK_ORDER/${o.id}`">{{ t('workOrders.detail') }}</RouterLink>
                <button v-if="can('service') && o.orderStatus === 'PENDING'" class="sm" :disabled="busy" @click="update(o, 'PROCESSING')">{{ t('workOrders.accept') }}</button>
                <button v-if="can('service') && o.orderStatus === 'PROCESSING'" class="sm" :disabled="busy" @click="update(o, 'DONE')">{{ t('workOrders.complete') }}</button>
                <button v-if="can('service') && o.orderStatus === 'DONE'" class="sm" :disabled="busy" @click="update(o, 'CLOSED')">{{ t('workOrders.close') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="detailOrder" class="modal-mask" @click.self="detailOrder = null">
      <div class="modal" style="max-width:720px">
        <div class="panel-head"><div><h2>{{ detailOrder.orderNo }}</h2><p class="small muted">{{ t('workOrders.related') }}</p></div><button class="sm" @click="detailOrder = null">{{ t('workOrders.close') }}</button></div>
        <EntityDetailTabs type="WORK_ORDER" :entity-id="detailOrder.id" />
      </div>
    </div>
  </div>
</template>
