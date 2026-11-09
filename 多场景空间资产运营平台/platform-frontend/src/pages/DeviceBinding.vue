<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'
import TreeSelect from '../components/TreeSelect.vue'
import { confirmAction } from '../confirm'

const project = ref(null)
const devices = ref([])
const spaces = ref([])
const error = ref('')
const busy = ref(false)
const expanded = ref(new Set())
const unboundQuery = ref('')
const selectedUnbound = ref([])
const activeSpaceId = ref('')
const importOpen = ref(false)
const importFile = ref(null)
const importBusy = ref(false)
const importResult = ref(null)
const importError = ref('')
const bySpace = computed(() => {
  const map = new Map()
  for (const d of devices.value) {
    if (d.spaceId) map.set(String(d.spaceId), [...(map.get(String(d.spaceId)) || []), d])
  }
  return map
})
const unbound = computed(() => devices.value.filter(d => !d.spaceId))
const spaceTree = computed(() => {
  const map = new Map()
  for (const s of spaces.value) map.set(String(s.id), { ...s, children: [], direct: bySpace.value.get(String(s.id)) || [], inherited: [] })
  const roots = []
  for (const node of map.values()) {
    const p = node.parentId ? map.get(String(node.parentId)) : null
    if (p) p.children.push(node)
    else roots.push(node)
  }
  const walk = (nodes, ancestors, depth) => {
    nodes.sort((a, b) => String(a.spacePath || '').localeCompare(String(b.spacePath || '')))
    const out = []
    for (const node of nodes) {
      node.depth = depth
      node.ancestorIds = ancestors.map(a => String(a.id))
      node.fullPath = [...ancestors.map(a => a.spaceName), node.spaceName].join(' / ')
      node.inherited = ancestors.flatMap(a => a.direct.map(d => ({
        ...d,
        sourceSpaceId: a.id,
        sourceSpaceName: a.spaceName,
        sourcePath: ancestors.slice(0, ancestors.indexOf(a) + 1).map(x => x.spaceName).join(' / '),
        inheritLevel: depth - a.depth
      })))
      out.push(node)
      out.push(...walk(node.children, [...ancestors, node], depth + 1))
    }
    return out
  }
  return walk(roots, [], 0)
})

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
    const [d, s] = await Promise.all([api.devices(project.value.id), api.spaces(project.value.id)])
    devices.value = d; spaces.value = s
    const roots = s.filter(x => !x.parentId || !s.some(y => String(y.id) === String(x.parentId)))
    if (!activeSpaceId.value && roots.length) activeSpaceId.value = String(roots[0].id)
    if (!expanded.value.size) expanded.value = new Set(roots.map(x => String(x.id)))
  } catch (e) { error.value = e.message }
}

const visibleSpaces = computed(() => spaceTree.value.filter(s => (s.ancestorIds || []).every(id => expanded.value.has(String(id)))))
const selectedSpace = computed(() => spaceTree.value.find(s => String(s.id) === String(activeSpaceId.value)) || null)
const filteredUnbound = computed(() => {
  const q = unboundQuery.value.trim().toLowerCase()
  if (!q) return unbound.value
  return unbound.value.filter(d => (String(d.deviceCode) + ' ' + String(d.deviceName || '') + ' ' + String(d.deviceType || '')).toLowerCase().includes(q))
})

function selectSpace(s) {
  activeSpaceId.value = String(s.id)
  selectedUnbound.value = []
}

function toggleExpand(s) {
  const id = String(s.id)
  const next = new Set(expanded.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expanded.value = next
}

function toggleUnbound(id) {
  const key = String(id)
  selectedUnbound.value = selectedUnbound.value.includes(key) ? selectedUnbound.value.filter(x => x !== key) : [...selectedUnbound.value, key]
}

async function bindOne(d) {
  if (!selectedSpace.value) { error.value = '请先选择空间'; return }
  busy.value = true; error.value = ''
  try {
    await api.bindDevice(d.id, selectedSpace.value.id)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function bindSelected() {
  if (!selectedSpace.value || !selectedUnbound.value.length) return
  busy.value = true; error.value = ''
  try {
    for (const id of selectedUnbound.value) await api.bindDevice(id, selectedSpace.value.id)
    selectedUnbound.value = []
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function downloadTemplate() {
  const orgCode = project.value?.orgCode || '350600'
  const csv = '\ufeff组织编码,楼栋,单元,楼层,房间,床位内房,房源编号,房源名称,房源类型,建筑面积,设备编号,设备类型,设备名称,物理MAC\n'
    + orgCode + ',A栋,1单元,1层,101室,,,101室,公租房,60,,门锁,101门锁,\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备绑定导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

function openImport() {
  importOpen.value = true
  importFile.value = null
  importResult.value = null
  importError.value = ''
}

function pickImportFile(e) {
  importFile.value = e.target.files?.[0] || null
  importResult.value = null
  importError.value = ''
}

async function runImport() {
  if (!importFile.value) { importError.value = '请选择 CSV 文件'; return }
  importBusy.value = true; importError.value = ''
  try {
    importResult.value = await api.importDevices(importFile.value)
    await load()
  } catch (e) { importError.value = e.message } finally { importBusy.value = false }
}

function jumpSource(d) {
  if (!d.sourceSpaceId) return
  activeSpaceId.value = String(d.sourceSpaceId)
  const source = spaceTree.value.find(s => String(s.id) === String(d.sourceSpaceId))
  if (source) {
    const next = new Set(expanded.value)
    for (const id of source.ancestorIds || []) next.add(String(id))
    next.add(String(source.id))
    expanded.value = next
  }
}

async function unbind(d) {
  if (!await confirmAction({ title: '解绑设备', message: `确认解绑设备 ${d.deviceName || d.deviceCode}？`, confirmText: '解绑', danger: true })) return
  busy.value = true; error.value = ''
  try { await api.bindDevice(d.id, null); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>

    <div class="panel">
      <div class="panel-head">
        <div><h2>设备绑定</h2><p>{{ project?.orgName || '未选择项目' }} · 按空间查看、绑定和解绑设备</p></div>
        <div class="row"><span class="badge blue">{{ unbound.length }} 台未绑定</span><button class="sm" @click="openImport">设备导入</button></div>
      </div>
      <div class="alert">左侧选择空间；右侧查看该空间直绑设备和继承设备。设备绑定到楼栋/单元/楼层后会向下继承显示，但设备只属于实际绑定空间。</div>
    </div>

    <div class="binding-grid">
      <div class="panel binding-tree">
        <div class="panel-head"><h2>空间树</h2><span class="small muted">{{ spaces.length }} 个空间</span></div>
        <div class="tree-scroll">
          <div v-for="s in visibleSpaces" :key="s.id" class="tree-row" :class="{ active: String(s.id) === String(activeSpaceId) }" :style="{ paddingLeft: (12 + s.depth * 18) + 'px' }" @click="selectSpace(s)">
            <button v-if="s.children.length" class="tree-toggle" type="button" @click.stop="toggleExpand(s)">{{ expanded.has(String(s.id)) ? '⌄' : '›' }}</button>
            <span v-else class="tree-toggle-placeholder"></span>
            <span class="tree-name">{{ s.spaceName }}</span>
            <span class="tree-counts"><span v-if="s.direct.length" class="badge green">{{ s.direct.length }}</span><span v-if="s.inherited.length" class="badge orange">{{ s.inherited.length }}</span></span>
          </div>
          <div v-if="!visibleSpaces.length" class="empty">暂无空间</div>
        </div>
      </div>

      <div class="binding-main">
        <div class="panel">
          <div class="panel-head">
            <div>
              <h2>{{ selectedSpace?.spaceName || '未选择空间' }}</h2>
              <p class="small muted">{{ selectedSpace?.fullPath || '请选择左侧空间' }}</p>
            </div>
            <span v-if="selectedSpace" class="badge blue">{{ selectedSpace.spaceType }}</span>
          </div>

          <div v-if="!selectedSpace" class="empty">请选择空间</div>
          <template v-else>
            <h3 class="section-title">直绑设备 <span class="small muted">{{ selectedSpace.direct.length }} 台</span></h3>
            <div v-if="!selectedSpace.direct.length" class="empty small">该空间暂无直绑设备</div>
            <div v-else class="table-wrap">
              <table>
                <thead><tr><th>设备编码</th><th>名称</th><th>类型</th><th>操作</th></tr></thead>
                <tbody>
                  <tr v-for="d in selectedSpace.direct" :key="d.id">
                    <td class="mono">{{ d.deviceCode }}</td><td>{{ d.deviceName }}</td><td>{{ d.deviceType }}</td>
                    <td><button v-if="can('device')" class="sm danger" :disabled="busy" @click="unbind(d)">解绑</button></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 class="section-title">继承设备 <span class="small muted">{{ selectedSpace.inherited.length }} 台</span></h3>
            <div v-if="!selectedSpace.inherited.length" class="empty small">暂无继承设备</div>
            <div v-else class="table-wrap">
              <table>
                <thead><tr><th>设备编码</th><th>名称</th><th>来源空间</th><th>操作</th></tr></thead>
                <tbody>
                  <tr v-for="d in selectedSpace.inherited" :key="d.id + '-' + d.sourceSpaceId">
                    <td class="mono">{{ d.deviceCode }}</td><td>{{ d.deviceName }}</td>
                    <td class="small">{{ d.sourceSpaceName }} · {{ d.sourcePath }}</td>
                    <td><button class="sm" @click="jumpSource(d)">跳转来源</button></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>

        <div class="panel">
          <div class="panel-head">
            <div><h2>未绑定设备</h2><p class="small muted">选择设备后批量绑定到当前空间</p></div>
            <span class="badge orange">{{ filteredUnbound.length }} 台</span>
          </div>
          <div class="row" style="margin-bottom:8px">
            <input v-model="unboundQuery" placeholder="搜索设备编码/名称/类型" style="max-width:300px" />
            <button v-if="can('device')" class="primary" :disabled="busy || !selectedSpace || !selectedUnbound.length" @click="bindSelected">批量绑定 {{ selectedUnbound.length ? '(' + selectedUnbound.length + ')' : '' }}</button>
          </div>
          <div v-if="!filteredUnbound.length" class="empty">暂无未绑定设备</div>
          <div v-for="d in filteredUnbound" :key="d.id" class="unbound-row">
            <input type="checkbox" :checked="selectedUnbound.includes(String(d.id))" @change="toggleUnbound(d.id)" />
            <div style="flex:1"><div class="mono">{{ d.deviceCode }}</div><div class="small muted">{{ d.deviceName }} · {{ d.deviceType }}</div></div>
            <button v-if="can('device')" class="sm" :disabled="busy || !selectedSpace" @click="bindOne(d)">绑定到当前空间</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="importOpen" class="modal-mask" @click.self="importOpen = false">
      <div class="modal" style="max-width:760px">
        <div class="panel-head"><h2>设备绑定批量导入</h2><button class="sm" @click="importOpen = false">关闭</button></div>
        <div class="alert">
          CSV 表头：组织编码, 楼栋, 单元, 楼层, 房间, 床位内房, 房源编号, 房源名称, 房源类型, 建筑面积, 设备编号, 设备类型, 设备名称, 物理MAC。
          一行一台设备；同一空间多行自动归并；房源编号为空自动生成；设备编号为空生成 DV 编号；设备编号重复同空间跳过、跨空间报错；物理 MAC 不允许重复。
        </div>
        <div class="row" style="margin:12px 0">
          <button class="sm" @click="downloadTemplate">下载模板</button>
          <input type="file" accept=".csv" @change="pickImportFile" />
          <span class="small muted">{{ importFile?.name || '未选择文件' }}</span>
        </div>
        <div v-if="importError" class="error">{{ importError }}</div>
        <div v-if="importResult">
          <div class="alert" :class="importResult.failed ? 'warn' : 'ok'">
            共 {{ importResult.total }} 行，空间新增 {{ importResult.spacesCreated }}，房源新增 {{ importResult.housesCreated }}，
            设备新增 {{ importResult.devicesCreated }}，设备处理 {{ importResult.devicesBound }}，失败 {{ importResult.failed }}。
          </div>
          <div v-if="importResult.errors?.length" class="table-wrap" style="margin-top:10px">
            <table>
              <thead><tr><th>行号</th><th>原因</th></tr></thead>
              <tbody><tr v-for="e in importResult.errors" :key="e.line"><td>{{ e.line }}</td><td>{{ e.message }}</td></tr></tbody>
            </table>
          </div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px">
          <button class="primary" :disabled="importBusy || !importFile" @click="runImport">{{ importBusy ? '导入中…' : '开始导入' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.binding-grid { display:grid; grid-template-columns: 300px minmax(0,1fr); gap:14px; align-items:start; }
.binding-tree { position:sticky; top:12px; }
.tree-scroll { max-height:calc(100vh - 210px); overflow:auto; padding:4px 0; }
.tree-row { display:flex; align-items:center; gap:4px; min-height:34px; padding:4px 8px 4px 0; border-radius:5px; cursor:pointer; color:var(--regular); }
.tree-row:hover, .tree-row.active { background:var(--brand-soft); color:var(--brand); }
.tree-toggle { width:18px; border:0; background:transparent; color:var(--muted); cursor:pointer; padding:0; }
.tree-toggle-placeholder { width:18px; }
.tree-name { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tree-counts { display:flex; gap:3px; }
.binding-main { min-width:0; }
.section-title { font-size:13px; margin:14px 0 6px; color:var(--regular); }
.unbound-row { display:flex; align-items:center; gap:8px; padding:8px 0; border-bottom:1px solid var(--line); }
@media (max-width:900px) { .binding-grid { grid-template-columns:1fr; } .binding-tree { position:static; } }
</style>
