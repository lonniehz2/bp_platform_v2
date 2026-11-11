<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()
const forcedType = computed(() => route.meta?.complaintType || '')
const pageTitle = computed(() => ({ APPEAL: t('complaints.appealTitle'), VISIT: t('complaints.visitTitle') }[forcedType.value] || t('complaints.title')))
const visibleRecords = computed(() => forcedType.value ? records.value.filter(r => r.complaintType === forcedType.value) : records.value)
const project = ref(null)
const houses = ref([])
const persons = ref([])
const records = ref([])
const type = ref(forcedType.value || '')
const error = ref('')
const busy = ref(false)
const form = reactive({ complaintType: forcedType.value || 'COMPLAINT', title: '', content: '', houseId: '', personId: '' })
const handleForm = reactive({ id: '', complaintStatus: 'PROCESSING', handlerName: t('complaints.defaultHandler'), handleResult: '' })

const typeName = (v) => ({ COMPLAINT: t('complaints.complaint'), APPEAL: t('complaints.appeal'), VISIT: t('complaints.visit') }[v] || v)
const statusClass = (s) => ({ RESOLVED: 'green', CLOSED: 'blue', PROCESSING: 'orange' }[s] || '')

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
    const [h, p, c] = await Promise.all([api.houses(id), api.persons(), api.complaints(id, type.value)])
    houses.value = h; persons.value = p; records.value = c
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
    if (forcedType.value) type.value = forcedType.value
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error(t('complaints.required'))
    await api.createComplaint({
      projectId: project.value.id, complaintType: form.complaintType, title: form.title.trim(),
      content: form.content, houseId: form.houseId || null, personId: form.personId || null
    })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openHandle(r) {
  handleForm.id = r.id
  handleForm.complaintStatus = 'PROCESSING'
  handleForm.handleResult = ''
}

async function handle() {
  busy.value = true; error.value = ''
  try {
    await api.handleComplaint(handleForm.id, {
      complaintStatus: handleForm.complaintStatus,
      handlerName: handleForm.handlerName,
      handleResult: handleForm.handleResult
    })
    handleForm.id = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

watch(forcedType, v => { if (v) { type.value = v; form.complaintType = v; load() } })
onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ pageTitle }}</h2><p>{{ project?.orgName || t('complaints.noProject') }} · {{ t('complaints.subtitle') }}</p></div>
        <select v-if="!forcedType" v-model="type" @change="load" style="width:140px"><option value="">{{ t('complaints.all') }}</option><option value="COMPLAINT">{{ t('complaints.complaint') }}</option><option value="APPEAL">{{ t('complaints.appeal') }}</option><option value="VISIT">{{ t('complaints.visit') }}</option></select>
      </div>
      <div class="row">
        <div class="field" v-if="!forcedType"><label>{{ t('complaints.type') }}</label><select v-model="form.complaintType"><option value="COMPLAINT">{{ t('complaints.complaint') }}</option><option value="APPEAL">{{ t('complaints.appeal') }}</option><option value="VISIT">{{ t('complaints.visit') }}</option></select></div>
        <div class="field" style="flex:2"><label>{{ t('complaints.titleCol') }}</label><input v-model="form.title" /></div>
        <div class="field"><label>{{ t('complaints.house') }}</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('complaints.searchHouse')" clearable /></div>
        <div class="field"><label>{{ t('complaints.person') }}</label><SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('complaints.searchPerson')" clearable /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('complaint')" class="primary" :disabled="busy" @click="create">{{ t('complaints.add') }}</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>{{ t('complaints.content') }}</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('complaints.list') }}</h2><span class="small muted">{{ records.length }} {{ t('complaints.count') }}</span></div>
      <div v-if="!records.length" class="empty">{{ t('complaints.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('complaints.type') }}</th><th>{{ t('complaints.titleCol') }}</th><th>{{ t('complaints.house') }}</th><th>{{ t('complaints.person') }}</th><th>{{ t('complaints.status') }}</th><th>{{ t('complaints.handler') }}</th><th>{{ t('complaints.result') }}</th><th>{{ t('complaints.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in visibleRecords" :key="r.id">
              <td>{{ typeName(r.complaintType) }}</td><td>{{ r.title }}</td>
              <td>{{ r.houseName || '-' }}</td><td>{{ r.personName || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.complaintStatus)">{{ r.complaintStatus }}</span></td>
              <td>{{ r.handlerName || '-' }}</td><td class="small">{{ r.handleResult || '-' }}</td>
              <td><button v-if="can('complaint') && r.complaintStatus !== 'CLOSED'" class="sm" @click="openHandle(r)">{{ t('complaints.handle') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="handleForm.id" class="panel">
      <div class="panel-head"><h2>{{ t('complaints.handleTitle') }}</h2><button class="sm" @click="handleForm.id = ''">{{ t('complaints.close') }}</button></div>
      <div class="row">
        <div class="field"><label>{{ t('complaints.status') }}</label><select v-model="handleForm.complaintStatus"><option value="PROCESSING">{{ t('complaints.processing') }}</option><option value="RESOLVED">{{ t('complaints.resolved') }}</option><option value="CLOSED">{{ t('complaints.closed') }}</option></select></div>
        <div class="field"><label>{{ t('complaints.handler') }}</label><input v-model="handleForm.handlerName" /></div>
        <div class="field" style="flex:2"><label>{{ t('complaints.handleResult') }}</label><input v-model="handleForm.handleResult" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="handle">{{ t('complaints.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
