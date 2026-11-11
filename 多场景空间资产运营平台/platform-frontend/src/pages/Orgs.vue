<script setup>
import { computed, onMounted, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const orgs = ref([])
const keyword = ref('')
const error = ref('')
const filtered = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  return q ? orgs.value.filter(o => String(o.orgCode || '').toLowerCase().includes(q) || String(o.orgName || '').toLowerCase().includes(q)) : orgs.value
})

onMounted(async () => {
  try { orgs.value = await api.projects() } catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('orgs.title') }}</h2><p>{{ t('orgs.subtitle') }}</p></div><span class="badge blue">{{ orgs.length }} {{ t('orgs.count') }}</span></div>
      <div class="field" style="max-width:360px"><label>{{ t('orgs.search') }}</label><input v-model="keyword" :placeholder="t('orgs.searchPlaceholder')" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('orgs.list') }}</h2><RouterLink :to="'/projects'">{{ t('orgs.manage') }}</RouterLink></div>
      <div v-if="!filtered.length" class="empty">{{ t('orgs.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('orgs.code') }}</th><th>{{ t('orgs.name') }}</th><th>{{ t('orgs.scene') }}</th><th>{{ t('orgs.mode') }}</th><th>{{ t('orgs.status') }}</th></tr></thead>
          <tbody>
            <tr v-for="o in filtered" :key="o.id">
              <td class="mono">{{ o.orgCode }}</td><td>{{ o.orgName }}</td><td>{{ enumLabel(o.sceneCode) }}</td>
              <td>{{ enumLabel(o.businessMode) }}</td><td><span class="badge green">{{ enumLabel(o.status) }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
