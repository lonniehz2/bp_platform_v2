<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const persons = ref([])
const records = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ personId: '', creditType: 'VIOLATION', scoreChange: -5, reason: '', effectiveDate: '', expireDate: '' })
const typeName = (v) => ({ VIOLATION: t('credit.violation'), ARREARS: t('credit.arrears'), OTHER: t('credit.other') }[v] || v)

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
    const [p, c] = await Promise.all([api.persons(), api.credits(project.value.id)])
    persons.value = p; records.value = c
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.personId) throw new Error(t('credit.required'))
    await api.createCredit({
      projectId: project.value.id, personId: form.personId, creditType: form.creditType,
      scoreChange: Number(form.scoreChange || 0), reason: form.reason,
      effectiveDate: form.effectiveDate || null, expireDate: form.expireDate || null
    })
    form.reason = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revoke(r) {
  busy.value = true; error.value = ''
  try { await api.revokeCredit(r.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('credit.title') }}</h2><p>{{ project?.orgName || t('credit.noProject') }} · {{ t('credit.subtitle') }}</p></div><span class="badge blue">{{ records.length }} {{ t('credit.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('credit.person') }}</label><SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('credit.searchPerson')" /></div>
        <div class="field"><label>{{ t('credit.type') }}</label><select v-model="form.creditType"><option value="VIOLATION">{{ t('credit.violation') }}</option><option value="ARREARS">{{ t('credit.arrears') }}</option><option value="OTHER">{{ t('credit.other') }}</option></select></div>
        <div class="field"><label>{{ t('credit.score') }}</label><input v-model.number="form.scoreChange" type="number" /></div>
        <div class="field" style="flex:2"><label>{{ t('credit.reason') }}</label><input v-model="form.reason" /></div>
        <div class="field"><label>{{ t('credit.effective') }}</label><input v-model="form.effectiveDate" type="date" /></div>
        <div class="field"><label>{{ t('credit.expire') }}</label><input v-model="form.expireDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('credit')" class="primary" :disabled="busy" @click="create">{{ t('credit.add') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('credit.records') }}</h2><span class="small muted">{{ t('credit.hint') }}</span></div>
      <div v-if="!records.length" class="empty">{{ t('credit.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('credit.person') }}</th><th>{{ t('credit.type') }}</th><th>{{ t('credit.score') }}</th><th>{{ t('credit.reason') }}</th><th>{{ t('credit.validity') }}</th><th>{{ t('credit.status') }}</th><th>{{ t('credit.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ r.personName }}</td><td>{{ typeName(r.creditType) }}</td>
              <td><span :class="r.scoreChange < 0 ? 'badge red' : 'badge green'">{{ r.scoreChange }}</span></td>
              <td>{{ r.reason || '-' }}</td><td class="small">{{ r.effectiveDate || '-' }} ~ {{ r.expireDate || '-' }}</td>
              <td><span class="badge" :class="r.recordStatus === 'ACTIVE' ? 'orange' : 'blue'">{{ r.recordStatus }}</span></td>
              <td><button v-if="can('credit') && r.recordStatus === 'ACTIVE'" class="sm danger" @click="revoke(r)">{{ t('credit.revoke') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
