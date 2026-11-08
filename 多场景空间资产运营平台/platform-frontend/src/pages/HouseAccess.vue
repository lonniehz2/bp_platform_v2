<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const houses = ref([])
const persons = ref([])
const houseId = ref('')
const personId = ref('')
const grants = ref([])
const error = ref('')
const busy = ref(false)
const house = computed(() => houses.value.find(h => String(h.id) === String(houseId.value)) || null)
const houseGrants = computed(() => grants.value.filter(g => g.targetType === 'SPACE' && String(g.targetId) === String(house.value?.spaceId)))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const [h, p] = await Promise.all([api.houses(project.value.id), api.persons()])
    houses.value = h; persons.value = p
    if (!houseId.value && h.length) houseId.value = h[0].id
    if (!personId.value && p.length) personId.value = p[0].id
    await loadGrants()
  } catch (e) { error.value = e.message }
}

async function loadGrants() {
  if (!personId.value) { grants.value = []; return }
  try { grants.value = await api.grants(personId.value) } catch { grants.value = [] }
}

async function grant() {
  busy.value = true; error.value = ''
  try {
    if (!house.value?.spaceId) throw new Error('该房源没有空间记录')
    await api.createGrant({
      projectId: project.value.id, personId: personId.value, targetType: 'SPACE', targetId: house.value.spaceId,
      grantLevel: 'OPEN', validStart: '2026-11-08', validEnd: '2027-11-07', sourceType: 'MANUAL'
    })
    await loadGrants()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revoke(g) {
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, '房源权限撤销'); await loadGrants() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>房源权限</h2><p>{{ project?.orgName || '未选择项目' }} · 按房源授权人员通行</p></div><span class="badge blue">{{ houseGrants.length }} 项</span></div>
      <div class="row">
        <div class="field" style="flex:2"><label>房源</label><select v-model="houseId"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>
        <div class="field" style="flex:2"><label>人员</label><select v-model="personId" @change="loadGrants"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="grant">授权通行</button></div>
      </div>
      <div class="alert" style="margin-top:10px">房源权限基于房源对应空间授权；子空间/床位按空间继承规则生效。</div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>当前房源授权</h2><span class="small muted">{{ house?.houseName || '未选择房源' }}</span></div>
      <div v-if="!houseGrants.length" class="empty">该房源暂无授权</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>人员</th><th>授权对象</th><th>级别</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="g in houseGrants" :key="g.id">
              <td>{{ persons.find(p => String(p.id) === String(g.personId))?.personName || g.personId }}</td>
              <td class="mono">{{ g.targetId }}</td><td>{{ g.grantLevel }}</td>
              <td class="small">{{ g.validStart }} ~ {{ g.validEnd || '长期' }}</td>
              <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ g.grantStatus }}</span></td>
              <td><button v-if="g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revoke(g)">撤销</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
