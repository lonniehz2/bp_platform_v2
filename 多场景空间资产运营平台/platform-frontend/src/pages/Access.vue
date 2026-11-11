<script setup>
import { onMounted, reactive, ref } from 'vue'
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
const form = reactive({ visitorName: '', visitorPhone: '', purpose: t('access.visitPurpose'), houseId: '', personId: '', validStart: '', validEnd: '' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red' }[s] || 'orange')

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
    const [h, p, r] = await Promise.all([api.houses(id), api.persons(), api.accessRecords(id)])
    houses.value = h; persons.value = p; records.value = r
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.visitorName.trim()) throw new Error(t('access.required'))
    await api.createAccessRecord({
      projectId: project.value.id, houseId: form.houseId || null, personId: form.personId || null,
      visitorName: form.visitorName.trim(), visitorPhone: form.visitorPhone, purpose: form.purpose,
      validStart: form.validStart || null, validEnd: form.validEnd || null
    })
    form.visitorName = ''; form.visitorPhone = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function approve(r, status) {
  busy.value = true; error.value = ''
  try {
    await api.approveAccessRecord(r.id, status)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('access.title') }}</h2><p>{{ project?.orgName || t('access.noProject') }} · {{ t('access.subtitle') }}</p></div><span class="badge blue">{{ records.length }} {{ t('access.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('access.visitor') }}</label><input v-model="form.visitorName" /></div>
        <div class="field"><label>{{ t('access.phone') }}</label><input v-model="form.visitorPhone" /></div>
        <div class="field"><label>{{ t('access.purpose') }}</label><input v-model="form.purpose" /></div>
        <div class="field"><label>{{ t('access.house') }}</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('access.searchHouse')" clearable /></div>
        <div class="field"><label>{{ t('access.person') }}</label><SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('access.searchPerson')" clearable /></div>
        <div class="field"><label>{{ t('access.start') }}</label><input v-model="form.validStart" type="datetime-local" /></div>
        <div class="field"><label>{{ t('access.end') }}</label><input v-model="form.validEnd" type="datetime-local" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('access')" class="primary" :disabled="busy" @click="create">{{ t('access.register') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('access.records') }}</h2><span class="small muted">{{ t('access.hint') }}</span></div>
      <div v-if="!records.length" class="empty">{{ t('access.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('access.visitor') }}</th><th>{{ t('access.phone') }}</th><th>{{ t('access.house') }}</th><th>{{ t('access.person') }}</th><th>{{ t('access.purpose') }}</th><th>{{ t('access.validity') }}</th><th>{{ t('access.status') }}</th><th>{{ t('access.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ r.visitorName }}</td><td>{{ r.visitorPhone || '-' }}</td>
              <td>{{ r.houseName || '-' }}</td><td>{{ r.personName || '-' }}</td><td>{{ r.purpose || '-' }}</td>
              <td class="small">{{ r.validStart || '-' }} ~ {{ r.validEnd || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.accessStatus)">{{ r.accessStatus }}</span></td>
              <td class="row">
                <button v-if="can('access') && r.accessStatus === 'PENDING'" class="sm" @click="approve(r, 'APPROVED')">{{ t('access.approve') }}</button>
                <button v-if="can('access') && r.accessStatus === 'PENDING'" class="sm danger" @click="approve(r, 'REJECTED')">{{ t('access.reject') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
