<script setup>
import { onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const records = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ publicityType: 'ALLOCATION', title: '', content: '', startDate: '', endDate: '' })
const typeName = (v) => ({ ALLOCATION: t('publicity.allocation'), QUALIFICATION: t('publicity.qualification'), EXIT: t('publicity.exit'), POLICY: t('publicity.policy') }[v] || v)
const statusClass = (s) => ({ PUBLISHED: 'green', CLOSED: 'blue' }[s] || 'orange')

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) records.value = await api.publicities(project.value.id)
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error(t('publicity.required'))
    await api.createPublicity({
      projectId: project.value.id, publicityType: form.publicityType, title: form.title.trim(),
      content: form.content, startDate: form.startDate || null, endDate: form.endDate || null
    })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function update(r, status) {
  busy.value = true; error.value = ''
  try {
    await api.updatePublicityStatus(r.id, status)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('publicity.title') }}</h2><p>{{ project?.orgName || t('publicity.noProject') }} · {{ t('publicity.subtitle') }}</p></div><span class="badge blue">{{ records.length }} {{ t('publicity.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('publicity.type') }}</label><select v-model="form.publicityType"><option value="ALLOCATION">{{ t('publicity.allocation') }}</option><option value="QUALIFICATION">{{ t('publicity.qualification') }}</option><option value="EXIT">{{ t('publicity.exit') }}</option><option value="POLICY">{{ t('publicity.policy') }}</option></select></div>
        <div class="field" style="flex:2"><label>{{ t('publicity.titleCol') }}</label><input v-model="form.title" /></div>
        <div class="field"><label>{{ t('publicity.start') }}</label><input v-model="form.startDate" type="date" /></div>
        <div class="field"><label>{{ t('publicity.end') }}</label><input v-model="form.endDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('publicity')" class="primary" :disabled="busy" @click="create">{{ t('publicity.add') }}</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>{{ t('publicity.content') }}</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('publicity.list') }}</h2><span class="small muted">{{ t('publicity.hint') }}</span></div>
      <div v-if="!records.length" class="empty">{{ t('publicity.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('publicity.type') }}</th><th>{{ t('publicity.titleCol') }}</th><th>{{ t('publicity.period') }}</th><th>{{ t('publicity.status') }}</th><th>{{ t('publicity.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ typeName(r.publicityType) }}</td><td>{{ r.title }}</td>
              <td class="small">{{ r.startDate || '-' }} ~ {{ r.endDate || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.publicityStatus)">{{ enumLabel(r.publicityStatus) }}</span></td>
              <td class="row">
                <button v-if="can('publicity') && r.publicityStatus === 'DRAFT'" class="sm" @click="update(r, 'PUBLISHED')">{{ t('publicity.publish') }}</button>
                <button v-if="can('publicity') && r.publicityStatus === 'PUBLISHED'" class="sm" @click="update(r, 'CLOSED')">{{ t('publicity.close') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
