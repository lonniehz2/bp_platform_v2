<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const spaces = ref([])
const assetTypes = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ parentId: '', spaceCode: '', spaceName: '', spaceType: 'BUILDING', assetTypeCode: 'PUBLIC_RENTAL' })
const types = ['AREA', 'BUILDING', 'UNIT', 'FLOOR', 'ROOM', 'INNER_ROOM', 'BED']

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
    const [s, t] = await Promise.all([api.spaces(project.value.id), api.assetTypes('GUARANTEE')])
    spaces.value = s; assetTypes.value = t
    if (!form.assetTypeCode && t.length) form.assetTypeCode = t[0].typeCode
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.spaceCode.trim() || !form.spaceName.trim()) throw new Error('请填写空间编码和名称')
    await api.createSpace(project.value.id, {
      parentId: form.parentId || null, spaceCode: form.spaceCode.trim(), spaceName: form.spaceName.trim(),
      spaceType: form.spaceType, assetTypeCode: form.assetTypeCode,
      rentable: ['ROOM', 'INNER_ROOM', 'BED'].includes(form.spaceType), area: 0, subUnitMode: null
    })
    form.spaceCode = ''; form.spaceName = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>空间层级</h2><p>{{ project?.orgName || '未选择项目' }} · 小区/楼栋/单元/楼层/房屋</p></div><span class="badge blue">{{ spaces.length }} 个空间</span></div>
      <div class="row">
        <div class="field"><label>上级空间</label><select v-model="form.parentId"><option value="">根节点</option><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}（{{ s.spaceType }}）</option></select></div>
        <div class="field"><label>空间编码</label><input v-model="form.spaceCode" /></div>
        <div class="field"><label>空间名称</label><input v-model="form.spaceName" /></div>
        <div class="field"><label>类型</label><select v-model="form.spaceType"><option v-for="t in types" :key="t" :value="t">{{ t }}</option></select></div>
        <div class="field"><label>资产类型</label><select v-model="form.assetTypeCode"><option v-for="t in assetTypes" :key="t.typeCode" :value="t.typeCode">{{ t.typeName }}</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">新增空间</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>空间列表</h2><span class="small muted">按层级路径排序</span></div>
      <div v-if="!spaces.length" class="empty">暂无空间</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>编码</th><th>名称</th><th>类型</th><th>层级</th><th>资产类型</th><th>路径</th></tr></thead>
          <tbody>
            <tr v-for="s in spaces" :key="s.id">
              <td class="mono">{{ s.spaceCode }}</td><td>{{ s.spaceName }}</td><td>{{ s.spaceType }}</td>
              <td>{{ s.levelNo }}</td><td>{{ s.assetTypeCode || '-' }}</td><td class="small">{{ s.spacePath }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
