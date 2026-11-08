<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const persons = ref([])
const personId = ref('')
const entries = ref([])
const error = ref('')
const busy = ref(false)

async function load() {
  error.value = ''
  try {
    persons.value = await api.persons()
    if (!personId.value && persons.value.length) personId.value = persons.value[0].id
    await loadKeyring()
  } catch (e) { error.value = e.message }
}

async function loadKeyring() {
  if (!personId.value) { entries.value = []; return }
  try { entries.value = await api.keyring(personId.value) } catch { entries.value = [] }
}

async function revoke(g) {
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, '钥匙包撤销'); await loadKeyring() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>钥匙包</h2><p>按人员聚合的有效通行授权</p></div><span class="badge blue">{{ entries.length }} 项</span></div>
      <div class="field" style="max-width:320px"><label>人员</label><select v-model="personId" @change="loadKeyring"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}（{{ p.personCode }}）</option></select></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>钥匙列表</h2><span class="small muted">仅显示当前有效授权</span></div>
      <div v-if="!entries.length" class="empty">暂无有效授权</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>授权对象</th><th>类型</th><th>级别</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="g in entries" :key="g.id">
              <td>{{ g.targetName || g.targetId }}</td><td>{{ g.targetType }}</td><td>{{ g.grantLevel }}</td>
              <td class="small">{{ g.validStart }} ~ {{ g.validEnd || '长期' }}</td>
              <td><span class="badge green">{{ g.grantStatus }}</span></td>
              <td><button class="sm danger" :disabled="busy" @click="revoke(g)">撤销</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
