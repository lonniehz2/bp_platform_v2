<script setup>
import { onMounted, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const rows = ref([])
const error = ref('')
const busy = ref(false)

const statusClass = (s) => s === 'RESOLVED' ? 'green' : 'orange'

async function load() {
  error.value = ''
  try { rows.value = await api.migrationExceptions('') } catch (e) { error.value = e.message }
}

async function resolve(row) {
  busy.value = true; error.value = ''
  try {
    await api.resolveMigrationException(row.id, { resolution: 'ACCEPT_SKIP' })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('migration.title') }}</h2><p>{{ t('migration.subtitle') }}</p></div><span class="pill">{{ rows.length }} {{ t('migration.count') }}</span></div>
      <div v-if="!rows.length" class="empty">{{ t('migration.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('migration.sourceTable') }}</th><th>{{ t('migration.sourceId') }}</th><th>{{ t('migration.reason') }}</th><th>{{ t('migration.payload') }}</th><th>{{ t('migration.status') }}</th><th>{{ t('migration.resolution') }}</th><th>{{ t('migration.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id">
              <td>{{ r.sourceTable }}</td><td class="mono">{{ r.sourceId }}</td>
              <td>{{ r.reason }}</td><td class="small">{{ r.payload }}</td>
              <td><span class="badge" :class="statusClass(r.resolveStatus)">{{ enumLabel(r.resolveStatus) }}</span></td>
              <td>{{ r.resolution || '-' }}</td>
              <td><button v-if="can('system') && r.resolveStatus === 'PENDING'" class="sm" :disabled="busy" @click="resolve(r)">{{ t('migration.resolve') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
