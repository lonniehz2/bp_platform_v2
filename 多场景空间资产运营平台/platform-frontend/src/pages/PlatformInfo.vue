<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const projects = ref([])
const persons = ref([])
const contracts = ref([])
const error = ref('')
const origin = window.location.origin
const user = (() => { try { return JSON.parse(localStorage.getItem('platformUser') || '{}') } catch { return {} } })()

onMounted(async () => {
  try {
    projects.value = await api.projects()
    persons.value = await api.persons()
    const p = projects.value[0]
    if (p) contracts.value = await api.contracts(p.id)
  } catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('platformInfo.title') }}</h2><p>{{ t('platformInfo.subtitle') }}</p></div><span class="badge blue">v0.1.0</span></div>
      <div class="grid cards">
        <div class="card"><div class="label">{{ t('platformInfo.currentUser') }}</div><div class="value" style="font-size:18px">{{ user.displayName || user.username || '-' }}</div><div class="hint">{{ user.username }}</div></div>
        <div class="card"><div class="label">{{ t('platformInfo.tenant') }}</div><div class="value" style="font-size:18px">{{ user.tenantId || '350600' }}</div><div class="hint">{{ t('platformInfo.tenantHint') }}</div></div>
        <div class="card"><div class="label">{{ t('platformInfo.projects') }}</div><div class="value">{{ projects.length }}</div><div class="hint">{{ t('platformInfo.allProjects') }}</div></div>
        <div class="card"><div class="label">{{ t('platformInfo.persons') }}</div><div class="value">{{ persons.length }}</div><div class="hint">{{ t('platformInfo.personHint') }}</div></div>
        <div class="card"><div class="label">{{ t('platformInfo.contracts') }}</div><div class="value">{{ contracts.length }}</div><div class="hint">{{ t('platformInfo.currentProject') }}</div></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('platformInfo.deployment') }}</h2></div>
        <div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="muted">{{ t('platformInfo.origin') }}</span><span class="mono">{{ origin }}</span></div>
        <div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="muted">{{ t('platformInfo.frontend') }}</span><span>Vue 3 + Vite</span></div>
        <div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="muted">{{ t('platformInfo.backend') }}</span><span>Spring Boot 3 / Java 17</span></div>
        <div class="row" style="padding:7px 0"><span class="muted">{{ t('platformInfo.database') }}</span><span>MySQL · bp_platform_v2</span></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>{{ t('platformInfo.entries') }}</h2></div>
        <div class="row">
          <RouterLink class="badge blue" to="/help">{{ t('platformInfo.help') }}</RouterLink>
          <RouterLink class="badge blue" to="/users">{{ t('platformInfo.users') }}</RouterLink>
          <RouterLink class="badge blue" to="/menus">{{ t('platformInfo.menus') }}</RouterLink>
          <RouterLink class="badge blue" to="/migration-exceptions">{{ t('platformInfo.migration') }}</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
