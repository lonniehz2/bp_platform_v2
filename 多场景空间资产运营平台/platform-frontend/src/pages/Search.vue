<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const keyword = ref('')
const projects = ref([])
const persons = ref([])
const contracts = ref([])
const project = ref(null)
const error = ref('')

const q = computed(() => keyword.value.trim().toLowerCase())
const match = (...values) => values.some(v => String(v || '').toLowerCase().includes(q.value))
const projectHits = computed(() => q.value ? projects.value.filter(p => match(p.orgCode, p.orgName)).slice(0, 20) : [])
const personHits = computed(() => q.value ? persons.value.filter(p => match(p.personCode, p.personName, p.phone)).slice(0, 20) : [])
const contractHits = computed(() => q.value ? contracts.value.filter(c => match(c.contractNo, c.personName, c.houseName)).slice(0, 20) : [])
const hasResult = computed(() => projectHits.value.length || personHits.value.length || contractHits.value.length)

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    projects.value = await api.projects()
    persons.value = await api.persons()
    project.value = await currentProject()
    if (project.value) contracts.value = await api.contracts(project.value.id)
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('search.title') }}</h2><p>{{ t('search.subtitle') }}</p></div><span class="badge blue">{{ projects.length }} {{ t('search.projects') }} · {{ persons.length }} {{ t('search.persons') }}</span></div>
      <div class="row">
        <div class="field" style="flex:2"><label>{{ t('search.keyword') }}</label><input v-model="keyword" :placeholder="t('search.placeholder')" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" @click="load">{{ t('search.refresh') }}</button></div>
      </div>
    </div>

    <div v-if="!q" class="empty">{{ t('search.start') }}</div>
    <div v-else-if="!hasResult" class="empty">{{ t('search.noResult') }}</div>
    <template v-else>
      <div v-if="projectHits.length" class="panel">
        <div class="panel-head"><h2>{{ t('search.project') }}</h2><span class="small muted">{{ projectHits.length }} {{ t('search.records') }}</span></div>
        <div v-for="p in projectHits" :key="p.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ p.orgName }}</div><div class="mono">{{ p.orgCode }}</div></div>
          <RouterLink to="/projects">{{ t('search.view') }}</RouterLink>
        </div>
      </div>

      <div v-if="personHits.length" class="panel">
        <div class="panel-head"><h2>{{ t('search.person') }}</h2><span class="small muted">{{ personHits.length }} {{ t('search.records') }}</span></div>
        <div v-for="p in personHits" :key="p.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ p.personName }}</div><div class="mono">{{ p.personCode }} · {{ p.phone }}</div></div>
          <RouterLink to="/persons">{{ t('search.view') }}</RouterLink>
        </div>
      </div>

      <div v-if="contractHits.length" class="panel">
        <div class="panel-head"><h2>{{ t('search.contract') }} · {{ project?.orgName }}</h2><span class="small muted">{{ contractHits.length }} {{ t('search.records') }}</span></div>
        <div v-for="c in contractHits" :key="c.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div class="mono">{{ c.contractNo }}</div><div class="small muted">{{ c.personName }} · {{ c.houseName }}</div></div>
          <RouterLink to="/contracts">{{ t('search.view') }}</RouterLink>
        </div>
      </div>
    </template>
  </div>
</template>
