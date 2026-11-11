<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'
import { currentScene } from '../scene'

const { t } = useI18n()
const projects = ref([])
const users = ref([])
const roles = ref([])
const auditLogs = ref([])
const error = ref('')

onMounted(async () => {
  try {
    projects.value = await api.projects()
    users.value = await api.users()
    roles.value = await api.roles(currentScene())
    auditLogs.value = await api.auditLogs(20).catch(() => [])
  } catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('sys.title') }}</h2><p>{{ t('sys.subtitle') }}</p></div><span class="badge blue">SYSTEM</span></div>
      <div class="grid cards">
        <div class="card"><div class="label">{{ t('sys.projects') }}</div><div class="value">{{ projects.length }}</div><div class="hint">{{ t('sys.projectHint') }}</div></div>
        <div class="card"><div class="label">{{ t('sys.users') }}</div><div class="value">{{ users.length }}</div><div class="hint">{{ t('sys.userHint') }}</div></div>
        <div class="card"><div class="label">{{ t('sys.roles') }}</div><div class="value">{{ roles.length }}</div><div class="hint">{{ t('sys.roleHint') }}</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('sys.audit') }}</h2><span class="small muted">{{ t('sys.auditHint') }}</span></div>
      <div v-if="!auditLogs.length" class="empty">{{ t('sys.empty') }}</div>
      <div class="table-wrap" v-else>
        <table><thead><tr><th>{{ t('sys.time') }}</th><th>{{ t('sys.users') }}</th><th>{{ t('sys.method') }}</th><th>{{ t('sys.path') }}</th><th>{{ t('sys.status') }}</th><th>IP</th></tr></thead>
          <tbody><tr v-for="l in auditLogs" :key="l.id">
            <td class="small">{{ l.createTime }}</td><td>{{ l.username }}</td><td class="mono">{{ l.method }}</td>
            <td class="mono small">{{ l.path }}</td><td>{{ l.statusCode }}</td><td class="small">{{ l.ip }}</td>
          </tr></tbody>
        </table>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">
      <div class="panel"><div class="panel-head"><h2>{{ t('sys.permissions') }}</h2></div><div class="row"><RouterLink class="badge blue" to="/users">{{ t('sys.userMgmt') }}</RouterLink><RouterLink class="badge blue" to="/menus">{{ t('sys.menus') }}</RouterLink></div></div>
      <div class="panel"><div class="panel-head"><h2>{{ t('sys.open') }}</h2></div><div class="row"><RouterLink class="badge blue" to="/open-apps">{{ t('sys.openApps') }}</RouterLink><RouterLink class="badge blue" to="/migration-exceptions">{{ t('sys.migration') }}</RouterLink></div></div>
      <div class="panel"><div class="panel-head"><h2>{{ t('sys.runtime') }}</h2></div><div class="row"><RouterLink class="badge blue" to="/platform-info">{{ t('sys.platformInfo') }}</RouterLink><RouterLink class="badge blue" to="/help">{{ t('sys.help') }}</RouterLink></div></div>
      <div class="panel"><div class="panel-head"><h2>{{ t('sys.business') }}</h2></div><div class="row"><RouterLink class="badge blue" to="/translations">{{ t('sys.translations') }}</RouterLink><RouterLink class="badge blue" to="/reports">{{ t('sys.reports') }}</RouterLink></div></div>
    </div>
  </div>
</template>
