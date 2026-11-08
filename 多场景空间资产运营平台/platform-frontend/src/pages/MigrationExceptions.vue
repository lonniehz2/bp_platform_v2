<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

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
      <div class="panel-head"><div><h2>迁移异常</h2><p>老数据迁移中无法直接迁入的记录，需人工确认</p></div><span class="pill">{{ rows.length }} 条</span></div>
      <div v-if="!rows.length" class="empty">暂无异常</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>来源表</th><th>来源 ID</th><th>原因</th><th>内容</th><th>状态</th><th>处理结论</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="r in rows" :key="r.id">
              <td>{{ r.sourceTable }}</td><td class="mono">{{ r.sourceId }}</td>
              <td>{{ r.reason }}</td><td class="small">{{ r.payload }}</td>
              <td><span class="badge" :class="statusClass(r.resolveStatus)">{{ r.resolveStatus }}</span></td>
              <td>{{ r.resolution || '-' }}</td>
              <td><button class="sm" v-if="r.resolveStatus === 'PENDING'" :disabled="busy" @click="resolve(r)">确认跳过</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
