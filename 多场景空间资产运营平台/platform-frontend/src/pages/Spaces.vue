<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import TreeSelect from '../components/TreeSelect.vue'
import { can } from '../permissions'
import { confirmAction } from '../confirm'

const project = ref(null)
const spaces = ref([])
const assetTypes = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ parentId: '', spaceCode: '', spaceName: '', spaceType: 'BUILDING', assetTypeCode: 'PUBLIC_RENTAL' })
const types = ['AREA', 'BUILDING', 'UNIT', 'FLOOR', 'ROOM', 'INNER_ROOM', 'BED']
const editingSpace = ref(null)
const spaceEditForm = reactive({ spaceName: '', spaceType: 'ROOM', assetTypeCode: '', area: 0, innerArea: 0, rentable: false })

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


function openSpaceEdit(s) {
  editingSpace.value = s
  Object.assign(spaceEditForm, {
    spaceName: s.spaceName || '', spaceType: s.spaceType || 'ROOM', assetTypeCode: s.assetTypeCode || '',
    area: s.area || 0, innerArea: s.innerArea || 0, rentable: !!s.rentable
  })
}


async function archiveSpace(s) {
  if (!await confirmAction({ title: '归档空间', message: `确认归档空间 ${s.spaceName}？存在子空间或房屋时会被拒绝。`, confirmText: '归档', danger: true })) return
  busy.value = true; error.value = ''
  try { await api.archiveSpace(project.value.id, s.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function saveSpaceEdit() {
  busy.value = true; error.value = ''
  try {
    if (!spaceEditForm.spaceName.trim()) throw new Error('空间名称不能为空')
    await api.updateSpace(project.value.id, editingSpace.value.id, { ...spaceEditForm })
    editingSpace.value = null
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
        <div class="field"><label>上级空间</label><TreeSelect v-model="form.parentId" :nodes="spaces" label-key="spaceName" value-key="id" parent-key="parentId" placeholder="选择上级空间（空为根）" clearable /></div>
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
          <thead><tr><th>编码</th><th>名称</th><th>类型</th><th>层级</th><th>资产类型</th><th>路径</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="s in spaces" :key="s.id">
              <td class="mono">{{ s.spaceCode }}</td><td>{{ s.spaceName }}</td><td>{{ s.spaceType }}</td>
              <td>{{ s.levelNo }}</td><td>{{ s.assetTypeCode || '-' }}</td><td class="small">{{ s.spacePath }}</td>
              <td><button class="sm" @click="openSpaceEdit(s)">编辑</button> <button class="sm danger" :disabled="busy" @click="archiveSpace(s)">归档</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="editingSpace" class="modal-mask" @click.self="editingSpace = null">
      <div class="modal">
        <div class="panel-head"><h2>编辑空间</h2><button class="sm" @click="editingSpace = null">关闭</button></div>
        <div class="field"><label>空间编码</label><input :value="editingSpace.spaceCode" disabled /></div>
        <div class="field"><label>空间名称</label><input v-model="spaceEditForm.spaceName" /></div>
        <div class="field"><label>空间类型</label><select v-model="spaceEditForm.spaceType"><option v-for="t in types" :key="t" :value="t">{{ t }}</option></select></div>
        <div class="field"><label>资产类型</label><input v-model="spaceEditForm.assetTypeCode" /></div>
        <div class="field"><label>建筑面积</label><input v-model.number="spaceEditForm.area" type="number" /></div>
        <div class="field"><label>套内面积</label><input v-model.number="spaceEditForm.innerArea" type="number" /></div>
        <div class="field"><label><input type="checkbox" v-model="spaceEditForm.rentable" /> 可出租</label></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveSpaceEdit">保存</button></div>
      </div>
    </div>
  </div>
</template>
