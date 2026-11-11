<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const tasks = ref([])
const status = ref('')
const error = ref('')
const filtered = computed(() => status.value ? tasks.value.filter(t => t.taskStatus === status.value) : tasks.value)

async function load() {
  error.value = ''
  try { tasks.value = await api.workflowTasks(status.value) } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('todos.title') }}</h2><p>{{ t('todos.subtitle') }}</p></div><span class="badge blue">{{ filtered.length }} {{ t('todos.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('todos.status') }}</label><select v-model="status" @change="load"><option value="">{{ t('todos.all') }}</option><option value="APPROVING">{{ t('todos.approving') }}</option><option value="APPROVED">{{ t('todos.approved') }}</option><option value="REJECTED">{{ t('todos.rejected') }}</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><RouterLink to="/audit">{{ t('todos.audit') }}</RouterLink></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('todos.list') }}</h2><span class="small muted">{{ t('todos.hint') }}</span></div>
      <div v-if="!filtered.length" class="empty">{{ t('todos.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('todos.bizType') }}</th><th>{{ t('todos.summary') }}</th><th>{{ t('todos.submitter') }}</th><th>{{ t('todos.currentNode') }}</th><th>{{ t('todos.status') }}</th><th>{{ t('todos.submitTime') }}</th></tr></thead>
          <tbody>
            <tr v-for="t in filtered" :key="t.id">
              <td>{{ t.bizType }}</td><td>{{ t.summary }}</td><td>{{ t.submitterName }}</td>
              <td>{{ t.currentNode || '-' }}</td>
              <td><span class="badge" :class="t.taskStatus === 'APPROVED' ? 'green' : t.taskStatus === 'REJECTED' ? 'red' : 'orange'">{{ t.taskStatus }}</span></td>
              <td class="small">{{ t.submitTime }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
