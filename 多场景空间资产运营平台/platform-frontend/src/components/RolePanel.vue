<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const roles = ref([])
const projects = ref([])
const menus = ref([])
const selected = ref(null)
const selectedCodes = ref([])
const selectedActions = ref([])
const scopeMode = ref('NONE')
const scopeProjectIds = ref([])
const error = ref('')
const notice = ref('')
const busy = ref(false)
const search = ref('')
const pageSearch = ref('')
const projectSearch = ref('')
const createOpen = ref(false)
const deleteTarget = ref(null)
const members = ref([])
const editOpen = ref(false)
const editForm = reactive({ roleName: '', roleStatus: 'ENABLED' })
const form = reactive({ roleCode: '', roleName: '' })
const actionOptions = [
  { code: 'view', label: '查看' },
  { code: 'create', label: '新增' },
  { code: 'edit', label: '编辑' },
  { code: 'delete', label: '删除' },
  { code: 'approve', label: '审批' }
]

const filteredRoles = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return roles.value
  return roles.value.filter(r => (String(r.roleName) + ' ' + String(r.roleCode)).toLowerCase().includes(q))
})

const groups = computed(() => menus.value.filter(m => m.menuType === 'GROUP').map(g => ({
  ...g,
  pages: (g.children || []).filter(m => m.menuType !== 'GROUP')
})))

const filteredGroups = computed(() => {
  const q = pageSearch.value.trim().toLowerCase()
  if (!q) return groups.value
  return groups.value.map(g => ({
    ...g,
    pages: g.pages.filter(p => (String(p.menuName) + ' ' + String(p.menuCode)).toLowerCase().includes(q))
  })).filter(g => g.pages.length)
})

const pageCount = computed(() => groups.value.reduce((n, g) => n + g.pages.length, 0))
const selectedPageCount = computed(() => selectedCodes.value.length)
const selectedProjectNames = computed(() => projects.value.filter(p => scopeProjectIds.value.includes(String(p.id))).map(p => p.orgName))
const filteredProjects = computed(() => {
  const q = projectSearch.value.trim().toLowerCase()
  return projects.value.filter(p => !q || (String(p.orgName) + ' ' + String(p.orgCode)).toLowerCase().includes(q))
})

async function load() {
  error.value = ''
  try {
    const [m, r, p] = await Promise.all([api.menus('GUARANTEE'), api.roles('GUARANTEE'), api.projects()])
    menus.value = m; roles.value = r; projects.value = p
    const keep = selected.value && r.find(x => String(x.id) === String(selected.value.id))
    await selectRole(keep || r[0] || null)
  } catch (e) { error.value = e.message }
}

async function selectRole(r) {
  selected.value = r || null
  notice.value = ''
  pageSearch.value = ''
  projectSearch.value = ''
  if (!r) { selectedCodes.value = []; selectedActions.value = []; return }
  try {
    const [list, scope, actions, memberList] = await Promise.all([api.roleMenus(r.id), api.roleScope(r.id), api.roleActions(r.id), api.roleMembers(r.id).catch(() => [])])
    selectedCodes.value = list.map(x => x.menuCode)
    scopeMode.value = scope.scopeType || 'NONE'
    scopeProjectIds.value = (scope.projectIds || []).map(String)
    selectedActions.value = actions.actions || []
    members.value = memberList || []
  } catch (e) { error.value = e.message; selectedCodes.value = [] }
}

function pageCodes(g) { return g.pages.map(p => p.menuCode) }
function groupAll(g) { const codes = pageCodes(g); return codes.length > 0 && codes.every(c => selectedCodes.value.includes(c)) }
function groupSome(g) { return pageCodes(g).some(c => selectedCodes.value.includes(c)) }
function toggleGroup(g) {
  const codes = pageCodes(g)
  if (groupAll(g)) {
    selectedCodes.value = selectedCodes.value.filter(c => !codes.includes(c))
    selectedActions.value = selectedActions.value.filter(k => !codes.some(c => k.startsWith(c + ':')))
  } else {
    for (const c of codes) {
      if (!selectedCodes.value.includes(c)) selectedCodes.value.push(c)
      if (!selectedActions.value.includes(c + ':view')) selectedActions.value.push(c + ':view')
    }
  }
}
function toggleCode(code) {
  const i = selectedCodes.value.indexOf(code)
  if (i >= 0) {
    selectedCodes.value.splice(i, 1)
    selectedActions.value = selectedActions.value.filter(k => !k.startsWith(code + ':'))
  } else {
    selectedCodes.value.push(code)
    if (!selectedActions.value.includes(code + ':view')) selectedActions.value.push(code + ':view')
  }
}
function pageHas(code, action) { return selectedActions.value.includes(code + ':' + action) }
function togglePageAction(code, action) {
  if (action === 'view') return
  if (!selectedCodes.value.includes(code)) return
  const key = code + ':' + action
  const i = selectedActions.value.indexOf(key)
  if (i >= 0) selectedActions.value.splice(i, 1)
  else selectedActions.value.push(key)
}
function groupActionAll(g, action) {
  const pages = g.pages.filter(p => selectedCodes.value.includes(p.menuCode))
  return pages.length > 0 && pages.every(p => pageHas(p.menuCode, action))
}
function toggleGroupAction(g, action) {
  if (action === 'view') return
  const pages = g.pages.filter(p => selectedCodes.value.includes(p.menuCode))
  if (!pages.length) return
  const all = pages.every(p => pageHas(p.menuCode, action))
  for (const p of pages) {
    const key = p.menuCode + ':' + action
    const i = selectedActions.value.indexOf(key)
    if (all && i >= 0) selectedActions.value.splice(i, 1)
    if (!all && i < 0) selectedActions.value.push(key)
  }
}

async function savePages() {
  if (!selected.value) return
  busy.value = true; error.value = ''
  try {
    await api.saveRoleMenus(selected.value.id, selectedCodes.value)
    await api.saveRoleActions(selected.value.id, selectedActions.value)
    notice.value = '页面权限和操作权限已保存'
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
async function saveActions() {
  if (!selected.value) return
  busy.value = true; error.value = ''
  try {
    await api.saveRoleActions(selected.value.id, selectedActions.value)
    notice.value = '功能权限已保存'
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
async function saveScope() {
  if (!selected.value) return
  busy.value = true; error.value = ''
  try {
    const projectIds = scopeMode.value === 'PROJECTS' ? scopeProjectIds.value.map(Number) : []
    const saved = await api.saveRoleScope(selected.value.id, { scopeType: scopeMode.value, projectIds })
    scopeMode.value = saved.scopeType || 'NONE'
    scopeProjectIds.value = (saved.projectIds || []).map(String)
    notice.value = '默认数据范围已保存；页面/功能权限的未保存修改不会丢失' 
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
function chooseScope(mode) { scopeMode.value = mode; if (mode !== 'PROJECTS') scopeProjectIds.value = [] }
function toggleProject(id) {
  const key = String(id)
  const i = scopeProjectIds.value.indexOf(key)
  if (i >= 0) scopeProjectIds.value.splice(i, 1)
  else scopeProjectIds.value.push(key)
}
function selectAllProjects() {
  for (const p of filteredProjects.value) {
    const key = String(p.id)
    if (!scopeProjectIds.value.includes(key)) scopeProjectIds.value.push(key)
  }
}


function openRoleEdit() {
  editForm.roleName = selected.value?.roleName || ''
  editForm.roleStatus = selected.value?.roleStatus || 'ENABLED'
  editOpen.value = true
}

async function saveRoleEdit() {
  if (!selected.value) return
  busy.value = true; error.value = ''
  try {
    await api.updateRole(selected.value.id, { roleName: editForm.roleName.trim(), roleStatus: editForm.roleStatus })
    editOpen.value = false
    notice.value = '角色信息已更新'
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function askDelete() { deleteTarget.value = selected.value; error.value = '' }

async function confirmDelete() {
  if (!deleteTarget.value) return
  busy.value = true; error.value = ''
  try {
    await api.deleteRole(deleteTarget.value.id)
    deleteTarget.value = null
    selected.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function createRole() {
  busy.value = true; error.value = ''
  try {
    if (!form.roleCode.trim() || !form.roleName.trim()) throw new Error('请填写角色编码和名称')
    await api.createRole({ sceneCode: 'GUARANTEE', roleCode: form.roleCode.trim(), roleName: form.roleName.trim(), menuCodes: [] })
    form.roleCode = ''; form.roleName = ''
    createOpen.value = false
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid" style="grid-template-columns:280px minmax(0,1fr)">
      <div class="panel role-list">
        <div class="panel-head"><div><h2>角色</h2><p>{{ roles.length }} 个角色</p></div><button class="sm" @click="createOpen = true">新增</button></div>
        <input v-model="search" placeholder="搜索角色" style="margin-bottom:8px" />
        <div v-for="r in filteredRoles" :key="r.id" class="role-row" :class="{ active: selected && String(selected.id) === String(r.id) }" @click="selectRole(r)">
          <div style="flex:1;min-width:0"><div class="ellipsis">{{ r.roleName }}</div><div class="mono small muted ellipsis">{{ r.roleCode }}</div></div>
          <span class="badge">{{ r.menuCount }} 项</span>
        </div>
      </div>

      <div v-if="selected" class="role-detail">
        <div class="panel">
          <div class="panel-head"><div><h2>{{ selected.roleName }}</h2><p class="mono small muted">{{ selected.roleCode }} · {{ selectedPageCount }}/{{ pageCount }} 个页面 · {{ selectedActions.length }} 个功能点</p></div><div class="row"><button class="sm" @click="openRoleEdit">编辑角色</button><button class="sm danger" @click="askDelete">删除角色</button></div></div>
          <div v-if="notice" class="alert success">{{ notice }}</div>
        </div>

        <div class="panel">
          <div class="panel-head"><div><h2>页面权限</h2><p>分组行用于批量设置，页面行配置该页面的操作权限</p></div><button class="primary" :disabled="busy" @click="savePages">保存权限</button></div>
          <input v-model="pageSearch" placeholder="搜索页面名称或编码" style="margin-bottom:10px" />
          <div class="perm-table">
            <div class="perm-head">
              <span>页面 / 菜单</span>
              <span v-for="a in actionOptions" :key="a.code" class="center">{{ a.label }}</span>
            </div>
            <div v-for="g in filteredGroups" :key="g.menuCode" class="perm-group">
              <div class="group-row">
                <label class="group-name">
                  <input type="checkbox" :checked="groupAll(g)" @change="toggleGroup(g)" />
                  <strong>{{ g.menuName }}</strong>
                  <span class="badge" :class="groupAll(g) ? 'green' : (groupSome(g) ? 'orange' : '')">{{ pageCodes(g).filter(c => selectedCodes.includes(c)).length }}/{{ g.pages.length }}</span>
                  <span class="mono small muted">{{ g.menuCode }}</span>
                </label>
                <template v-for="a in actionOptions" :key="a.code">
                  <span v-if="a.code === 'view'" class="center muted">—</span>
                  <input v-else type="checkbox" class="cell-check" :checked="groupActionAll(g, a.code)" :disabled="!pageCodes(g).some(c => selectedCodes.includes(c))" @change="toggleGroupAction(g, a.code)" />
                </template>
              </div>
              <div v-for="p in g.pages" :key="p.menuCode" class="page-row">
                <label class="page-name">
                  <input type="checkbox" :checked="selectedCodes.includes(p.menuCode)" @change="toggleCode(p.menuCode)" />
                  <span>{{ p.menuName }}</span>
                  <span class="mono small muted">{{ p.menuCode }}</span>
                </label>
                <input v-for="a in actionOptions" :key="a.code" type="checkbox" class="cell-check"
                  :checked="pageHas(p.menuCode, a.code)"
                  :disabled="a.code === 'view' || !selectedCodes.includes(p.menuCode)"
                  @change="togglePageAction(p.menuCode, a.code)" />
              </div>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><div><h2>角色成员</h2><p>当前使用该角色的用户</p></div><span class="badge">{{ members.length }} 人</span></div>
          <div v-if="!members.length" class="empty">暂无成员</div>
          <div v-for="m in members" :key="m.id" class="entity-row"><div><strong>{{ m.displayName }}</strong><span class="small muted"> · {{ m.username }}</span></div><span class="badge" :class="m.userStatus === 'ENABLED' ? 'green' : 'orange'">{{ m.userStatus }}</span></div>
        </div>

        <div class="panel">
          <div class="panel-head"><div><h2>默认数据范围</h2><p>用户默认继承此范围，可在用户页面进一步收窄</p></div><button class="primary" :disabled="busy" @click="saveScope">保存数据范围</button></div>
          <div class="scope-choice">
            <button class="scope-card" :class="{ active: scopeMode === 'NONE' }" @click="chooseScope('NONE')"><strong>无数据</strong><span>默认不可见任何项目。</span></button>
            <button class="scope-card" :class="{ active: scopeMode === 'ALL' }" @click="chooseScope('ALL')"><strong>全部项目</strong><span>可见全部项目数据。</span></button>
            <button class="scope-card" :class="{ active: scopeMode === 'PROJECTS' }" @click="chooseScope('PROJECTS')"><strong>指定项目</strong><span>只允许指定项目。</span></button>
            <button class="scope-card" :class="{ active: scopeMode === 'SELF' }" @click="chooseScope('SELF')"><strong>仅本人</strong><span>仅本人创建或负责的数据。</span></button>
          </div>
          <div v-if="scopeMode === 'PROJECTS'" style="margin-top:12px">
            <div class="scope-help">勾选项目即可多选，不需要按 Ctrl；可以搜索后全选当前结果。</div>
            <input v-model="projectSearch" placeholder="搜索项目名称或编码" style="margin:10px 0 8px" />
            <div class="scope-project-picker">
              <label v-for="p in filteredProjects" :key="p.id" class="project-option" :class="{ selected: scopeProjectIds.includes(String(p.id)) }">
                <input type="checkbox" :checked="scopeProjectIds.includes(String(p.id))" @change="toggleProject(p.id)" />
                <span>{{ p.orgName }}</span><span class="mono small muted">{{ p.orgCode }}</span>
              </label>
              <div v-if="!filteredProjects.length" class="empty">没有匹配的项目</div>
            </div>
            <div class="row" style="justify-content:space-between;margin-top:8px"><span class="small">已选 {{ scopeProjectIds.length }} 个项目</span><div class="row"><button class="sm" @click="selectAllProjects">全选当前</button><button class="sm" @click="scopeProjectIds = []">清空</button></div></div>
            <div v-if="selectedProjectNames.length" class="small muted" style="margin-top:6px">已选：{{ selectedProjectNames.join('、') }}</div>
          </div>
        </div>
      </div>
      <div v-else class="panel"><div class="empty">请选择角色</div></div>
    </div>

    <div v-if="editOpen" class="modal-mask" @click.self="editOpen = false">
      <div class="modal" style="max-width:480px">
        <div class="panel-head"><h2>编辑角色</h2><button class="sm" @click="editOpen = false">关闭</button></div>
        <div class="field"><label>角色编码</label><input :value="selected?.roleCode" disabled /></div>
        <div class="field"><label>角色名称</label><input v-model="editForm.roleName" /></div>
        <div class="field"><label>状态</label><select v-model="editForm.roleStatus"><option value="ENABLED">启用</option><option value="DISABLED">停用</option></select></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveRoleEdit">保存</button></div>
      </div>
    </div>

    <div v-if="deleteTarget" class="modal-mask" @click.self="deleteTarget = null">
      <div class="modal" style="max-width:480px">
        <div class="panel-head"><h2>删除角色</h2><button class="sm" @click="deleteTarget = null">关闭</button></div>
        <div class="alert">确认删除角色“{{ deleteTarget.roleName }}（{{ deleteTarget.roleCode }}）”？页面权限、操作权限和数据范围将一并删除。有用户使用该角色时不能删除。</div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="sm" @click="deleteTarget = null">取消</button><button class="danger" :disabled="busy" @click="confirmDelete">{{ busy ? '删除中…' : '确认删除' }}</button></div>
      </div>
    </div>

    <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
      <div class="modal" style="max-width:480px">
        <div class="panel-head"><h2>新增角色</h2><button class="sm" @click="createOpen = false">关闭</button></div>
        <div class="field"><label>角色编码</label><input v-model="form.roleCode" placeholder="如 GUARANTEE_AUDITOR" /></div>
        <div class="field"><label>角色名称</label><input v-model="form.roleName" placeholder="稽核员" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="createRole">创建</button></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.role-list { align-self:start; }
.role-row { display:flex; align-items:center; gap:8px; padding:10px 8px; border-bottom:1px solid var(--line); cursor:pointer; border-radius:6px; }
.role-row:hover, .role-row.active { background:var(--brand-soft); color:var(--brand); }
.ellipsis { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.role-detail { display:flex; flex-direction:column; gap:12px; min-width:0; }
.perm-table { border:1px solid var(--line); border-radius:8px; overflow:auto; max-height:500px; }
.perm-head, .group-row, .page-row { display:grid; grid-template-columns:minmax(250px,1fr) repeat(5,56px); align-items:center; }
.perm-head { position:sticky; top:0; z-index:1; background:var(--bg); border-bottom:1px solid var(--line); padding:9px 12px; font-size:12px; color:var(--muted); }
.perm-head span { text-align:center; }
.perm-head span:first-child { text-align:left; }
.perm-group { border-bottom:1px solid var(--line); }
.group-row { background:var(--bg); padding:9px 12px; }
.group-name, .page-name { display:flex; align-items:center; gap:8px; cursor:pointer; min-width:0; }
.group-name input, .page-name input, .cell-check { width:auto; }
.group-name strong { font-size:13px; }
.page-row { padding:7px 12px 7px 30px; }
.page-row:hover { background:var(--brand-soft); }
.page-name { font-size:13px; }
.page-name .mono { margin-left:auto; }
.cell-check { justify-self:center; }
.center { text-align:center; }
.muted { color:var(--muted); }
.scope-choice { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
.scope-card { text-align:left; padding:10px; border:1px solid var(--line); border-radius:8px; background:var(--bg); cursor:pointer; display:flex; flex-direction:column; gap:4px; }
.scope-card strong { font-size:13px; }
.scope-card span { font-size:11px; color:var(--muted); line-height:1.5; }
.scope-card.active { border-color:var(--brand); background:var(--brand-soft); }
.scope-help { padding:9px 11px; background:#eff6ff; border:1px solid #bfdbfe; color:#1d4ed8; border-radius:6px; font-size:12px; line-height:1.6; }
.scope-project-picker { width:100%; box-sizing:border-box; max-height:230px; overflow:auto; border:1px solid var(--line); border-radius:6px; padding:4px; }
.project-option { display:flex; align-items:center; gap:8px; padding:7px 8px; border-radius:4px; cursor:pointer; }
.project-option:hover, .project-option.selected { background:var(--brand-soft); }
.project-option input { width:auto; }
.project-option .mono { margin-left:auto; }
.alert.success { background:#ecfdf5; color:#047857; border-color:#a7f3d0; }
@media (max-width:1100px) { .scope-choice { grid-template-columns:repeat(2,1fr); } }
</style>
