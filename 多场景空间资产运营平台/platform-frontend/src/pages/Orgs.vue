<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

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
      <div class="panel-head"><div><h2>组织机构</h2><p>保障房项目组织、编码和经营模式</p></div><span class="badge blue">{{ orgs.length }} 个组织</span></div>
      <div class="field" style="max-width:360px"><label>查询</label><input v-model="keyword" placeholder="组织编码/名称" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>组织列表</h2><RouterLink to="/projects">项目管理</RouterLink></div>
      <div v-if="!filtered.length" class="empty">暂无组织</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>组织编码</th><th>组织名称</th><th>场景</th><th>经营模式</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="o in filtered" :key="o.id">
              <td class="mono">{{ o.orgCode }}</td><td>{{ o.orgName }}</td><td>{{ o.sceneCode }}</td>
              <td>{{ o.businessMode }}</td><td><span class="badge green">{{ o.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
