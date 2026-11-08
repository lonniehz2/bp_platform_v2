<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import Pager from '../components/Pager.vue'

const project = ref(null)
const houses = ref([])
const status = ref('')
const page = ref(1)
const error = ref('')
const filtered = computed(() => status.value ? houses.value.filter(h => h.houseStatus === status.value) : houses.value)
const paged = computed(() => filtered.value.slice((page.value - 1) * 10, page.value * 10))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) houses.value = await api.houses(project.value.id)
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>房源台账</h2><p>{{ project?.orgName || '未选择项目' }} · 可出租房源和房态</p></div>
        <div class="row"><span class="badge blue">{{ houses.length }} 套</span><RouterLink to="/spaces">空间层级</RouterLink></div>
      </div>
      <div class="row">
        <div class="field"><label>房态</label><select v-model="status" @change="page = 1"><option value="">全部</option><option value="VACANT">空置</option><option value="ALLOCATED">已配租</option><option value="OCCUPIED">已入住</option></select></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>房源列表</h2><span class="small muted">房源由可出租空间生成</span></div>
      <div v-if="!filtered.length" class="empty">暂无房源</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>房源编码</th><th>名称</th><th>资产类型</th><th>面积</th><th>房态</th></tr></thead>
          <tbody>
            <tr v-for="h in paged" :key="h.id">
              <td class="mono">{{ h.houseCode }}</td><td>{{ h.houseName }}</td>
              <td>{{ h.assetTypeCode || '-' }}</td><td>{{ h.area || '-' }}</td>
              <td><span class="badge" :class="h.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ h.houseStatus }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pager :total="filtered.length" :page="page" @update:page="page = $event" />
    </div>
  </div>
</template>
