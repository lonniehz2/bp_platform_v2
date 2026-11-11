<script setup>
import { computed, onMounted, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const alerts = ref([])
const error = ref('')
const deviceAlerts = computed(() => alerts.value.filter(a => a.alertType === 'DEVICE'))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) alerts.value = await api.alerts(project.value.id)
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('deviceEvents.title') }}</h2><p>{{ project?.orgName || t('deviceEvents.noProject') }} · {{ t('deviceEvents.subtitle') }}</p></div><span class="badge blue">{{ deviceAlerts.length }} {{ t('deviceEvents.count') }}</span></div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>{{ t('deviceEvents.list') }}</h2><RouterLink to="/alerts">{{ t('deviceEvents.all') }}</RouterLink></div>
      <div v-if="!deviceAlerts.length" class="empty">{{ t('deviceEvents.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('deviceEvents.level') }}</th><th>{{ t('deviceEvents.alertTitle') }}</th><th>{{ t('deviceEvents.house') }}</th><th>{{ t('deviceEvents.status') }}</th><th>{{ t('deviceEvents.handler') }}</th><th>{{ t('deviceEvents.time') }}</th></tr></thead>
          <tbody>
            <tr v-for="a in deviceAlerts" :key="a.id">
              <td><span class="badge" :class="a.alertLevel === 'HIGH' || a.alertLevel === 'URGENT' ? 'red' : 'orange'">{{ enumLabel(a.alertLevel) }}</span></td>
              <td>{{ a.title }}</td><td>{{ a.houseName || '-' }}</td>
              <td><span class="badge" :class="a.alertStatus === 'RESOLVED' ? 'green' : 'orange'">{{ enumLabel(a.alertStatus) }}</span></td>
              <td>{{ a.handlerName || '-' }}</td><td class="small">{{ a.createTime }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
