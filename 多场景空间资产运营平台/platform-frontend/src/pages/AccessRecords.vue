<script setup>
import { onMounted, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const records = ref([])
const error = ref('')
const busy = ref(false)

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) records.value = await api.accessRecords(project.value.id)
  } catch (e) { error.value = e.message }
}

async function approve(r, status) {
  busy.value = true; error.value = ''
  try { await api.approveAccessRecord(r.id, status); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('accessRecords.title') }}</h2><p>{{ project?.orgName || t('accessRecords.noProject') }} · {{ t('accessRecords.subtitle') }}</p></div><span class="badge blue">{{ records.length }} {{ t('accessRecords.count') }}</span></div>
      <div class="row"><RouterLink to="/access-records">{{ t('accessRecords.register') }}</RouterLink></div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>{{ t('accessRecords.list') }}</h2><span class="small muted">{{ t('accessRecords.hint') }}</span></div>
      <div v-if="!records.length" class="empty">{{ t('accessRecords.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('accessRecords.visitor') }}</th><th>{{ t('accessRecords.phone') }}</th><th>{{ t('accessRecords.house') }}</th><th>{{ t('accessRecords.person') }}</th><th>{{ t('accessRecords.validity') }}</th><th>{{ t('accessRecords.status') }}</th><th>{{ t('accessRecords.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ r.visitorName }}</td><td>{{ r.visitorPhone || '-' }}</td><td>{{ r.houseName || '-' }}</td>
              <td>{{ r.personName || '-' }}</td><td class="small">{{ r.validStart || '-' }} ~ {{ r.validEnd || '-' }}</td>
              <td><span class="badge" :class="r.accessStatus === 'APPROVED' ? 'green' : r.accessStatus === 'REJECTED' ? 'red' : 'orange'">{{ enumLabel(r.accessStatus) }}</span></td>
              <td class="row">
                <button v-if="r.accessStatus === 'PENDING'" class="sm" :disabled="busy" @click="approve(r, 'APPROVED')">{{ t('accessRecords.approve') }}</button>
                <button v-if="r.accessStatus === 'PENDING'" class="sm danger" :disabled="busy" @click="approve(r, 'REJECTED')">{{ t('accessRecords.reject') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
