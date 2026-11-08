<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const devices = ref([])
const spaces = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ deviceId: '', spaceId: '' })
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
    if (!form.deviceId && unbound.value.length) form.deviceId = unbound.value[0].id
    if (!form.spaceId && s.length) form.spaceId = s[0].id
  } catch (e) { error.value = e.message }
}

async function bind() {
  busy.value = true; error.value = ''
  try {
    if (!form.deviceId || !form.spaceId) throw new Error('请选择设备和空间')
    await api.bindDevice(form.deviceId, form.spaceId)
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
  document.getElementById('space-' + d.sourceSpaceId)?.scrollIntoView({ block: 'center', behavior: 'smooth' })
}

async function unbind(d) {
  busy.value = true; error.value = ''
  try { await api.bindDevice(d.id, null); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>设备绑定</h2><p>{{ project?.orgName || '未选择项目' }} · 设备绑定到空间，子空间自动继承</p></div>
        <div class="row"><span class="badge blue">{{ unbound.length }} 台未绑定</span><button class="sm" @click="openImport">设备导入</button></div>
      </div>
      <div class="row">
        <div class="field"><label>未绑定设备</label><select v-model="form.deviceId"><option value="">请选择</option><option v-for="d in unbound" :key="d.id" :value="d.id">{{ d.deviceCode }} · {{ d.deviceName }}</option></select></div>
        <div class="field"><label>绑定空间</label><select v-model="form.spaceId"><option value="">请选择</option><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}（{{ s.spaceType }}）</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('device')" class="primary" :disabled="busy" @click="bind">绑定</button></div>
      </div>
      <div class="alert" style="margin-top:10px">设备绑定到楼栋/单元/楼层后，下级空间自动显示继承设备；绑定到房屋后只作用于该房屋。</div>
    </div>

    <div class="grid" style="grid-template-columns:1.25fr .75fr">
      <div class="panel">
        <div class="panel-head"><h2>空间层级与设备</h2><span class="small muted">{{ spaces.length }} 个空间 · {{ devices.length }} 台设备</span></div>
        <div v-if="!spaceTree.length" class="empty">暂无空间</div>
        <div v-for="s in spaceTree" :id="'space-' + s.id" :key="s.id" class="space-node" :class="{ active: String(s.id) === activeSpaceId }" :style="{ paddingLeft: (s.depth * 18 + 6) + 'px' }">
          <div class="row" style="border-bottom:1px solid var(--line);padding:7px 0">
            <span class="badge" :class="s.spaceType === 'ROOM' || s.spaceType === 'BED' ? 'blue' : ''">{{ s.spaceType }}</span>
            <strong>{{ s.spaceName }}</strong>
            <span class="mono small">{{ s.spaceCode }}</span>
            <span v-if="s.direct.length" class="badge green">直绑 {{ s.direct.length }}</span>
            <span v-if="s.inherited.length" class="badge orange">继承 {{ s.inherited.length }}</span>
          </div>
          <div v-for="d in [...s.inherited, ...s.direct]" :key="d.id" class="row" style="padding:4px 0 4px 18px;font-size:12px">
            <span class="mono">{{ d.deviceCode }}</span>
            <span>{{ d.deviceName }}</span>
            <span class="badge" :class="s.direct.includes(d) ? 'green' : 'orange'">{{ s.direct.includes(d) ? '直绑' : '继承' }}</span>
            <template v-if="!s.direct.includes(d)">
              <span class="small muted">来自 {{ d.sourceSpaceName }} · {{ d.sourcePath }}</span>
              <button class="sm" @click="jumpSource(d)">跳转来源</button>
            </template>
            <button v-if="can('device') && s.direct.includes(d)" class="sm danger" :disabled="busy" @click="unbind(d)">解绑</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>未绑定设备</h2><span class="small muted">{{ unbound.length }} 台</span></div>
        <div v-if="!unbound.length" class="empty">全部设备已绑定</div>
        <div v-for="d in unbound" :key="d.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div class="mono">{{ d.deviceCode }}</div><div class="small muted">{{ d.deviceName }} · {{ d.deviceType }}</div></div>
          <span class="badge orange">UNBOUND</span>
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
