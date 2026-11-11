<script setup>
import { onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const houses = ref([])
const persons = ref([])
const records = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ alertType: 'RISK', alertLevel: 'NORMAL', title: '', content: '', houseId: '', personId: '' })
const handleForm = reactive({ id: '', alertStatus: 'PROCESSING', handlerName: t('alerts.handlerName'), handleResult: '' })

const levelClass = (l) => ({ URGENT: 'red', HIGH: 'orange', NORMAL: 'blue' }[l] || '')
const statusClass = (s) => ({ RESOLVED: 'green', IGNORED: 'blue', PROCESSING: 'orange' }[s] || '')

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
    const [h, p, a] = await Promise.all([api.houses(id), api.persons(), api.alerts(id)])
    houses.value = h; persons.value = p; records.value = a
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error(t('alerts.required'))
    await api.createAlert({
      projectId: project.value.id, alertType: form.alertType, alertLevel: form.alertLevel,
      title: form.title.trim(), content: form.content, houseId: form.houseId || null, personId: form.personId || null
    })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openHandle(r) {
  handleForm.id = r.id; handleForm.alertStatus = 'PROCESSING'; handleForm.handleResult = ''
}

async function handle() {
  busy.value = true; error.value = ''
  try {
    await api.handleAlert(handleForm.id, {
      alertStatus: handleForm.alertStatus, handlerName: handleForm.handlerName, handleResult: handleForm.handleResult
    })
    handleForm.id = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('alerts.title') }}</h2><p>{{ project?.orgName || t('alerts.noProject') }} · {{ t('alerts.subtitle') }}</p></div><span class="badge blue">{{ records.length }} {{ t('alerts.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('alerts.type') }}</label><select v-model="form.alertType"><option value="RISK">{{ t('alerts.risk') }}</option><option value="OVERDUE">{{ t('alerts.overdue') }}</option><option value="DEVICE">{{ t('alerts.device') }}</option><option value="OTHER">{{ t('alerts.other') }}</option></select></div>
        <div class="field"><label>{{ t('alerts.level') }}</label><select v-model="form.alertLevel"><option value="LOW">{{ t('alerts.low') }}</option><option value="NORMAL">{{ t('alerts.normal') }}</option><option value="HIGH">{{ t('alerts.high') }}</option><option value="URGENT">{{ t('alerts.urgent') }}</option></select></div>
        <div class="field" style="flex:2"><label>{{ t('alerts.titleCol') }}</label><input v-model="form.title" /></div>
        <div class="field"><label>{{ t('alerts.house') }}</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('alerts.searchHouse')" clearable /></div>
        <div class="field"><label>{{ t('alerts.person') }}</label><SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('alerts.searchPerson')" clearable /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('alert')" class="primary" :disabled="busy" @click="create">{{ t('alerts.add') }}</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>{{ t('alerts.content') }}</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('alerts.list') }}</h2><span class="small muted">{{ t('alerts.hint') }}</span></div>
      <div v-if="!records.length" class="empty">{{ t('alerts.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('alerts.type') }}</th><th>{{ t('alerts.level') }}</th><th>{{ t('alerts.titleCol') }}</th><th>{{ t('alerts.house') }}</th><th>{{ t('alerts.person') }}</th><th>{{ t('alerts.status') }}</th><th>{{ t('alerts.handler') }}</th><th>{{ t('alerts.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ enumLabel(r.alertType) }}</td><td><span class="badge" :class="levelClass(r.alertLevel)">{{ enumLabel(r.alertLevel) }}</span></td>
              <td>{{ r.title }}</td><td>{{ r.houseName || '-' }}</td><td>{{ r.personName || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.alertStatus)">{{ enumLabel(r.alertStatus) }}</span></td>
              <td>{{ r.handlerName || '-' }}</td>
              <td><button v-if="can('alert') && r.alertStatus !== 'RESOLVED' && r.alertStatus !== 'IGNORED'" class="sm" @click="openHandle(r)">{{ t('alerts.handle') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="handleForm.id" class="panel">
      <div class="panel-head"><h2>{{ t('alerts.handleTitle') }}</h2><button class="sm" @click="handleForm.id = ''">{{ t('alerts.close') }}</button></div>
      <div class="row">
        <div class="field"><label>{{ t('alerts.status') }}</label><select v-model="handleForm.alertStatus"><option value="PROCESSING">{{ t('alerts.processing') }}</option><option value="RESOLVED">{{ t('alerts.resolved') }}</option><option value="IGNORED">{{ t('alerts.ignored') }}</option></select></div>
        <div class="field"><label>{{ t('alerts.handler') }}</label><input v-model="handleForm.handlerName" /></div>
        <div class="field" style="flex:2"><label>{{ t('alerts.result') }}</label><input v-model="handleForm.handleResult" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="handle">{{ t('alerts.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
