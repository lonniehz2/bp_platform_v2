<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { useI18n } from 'vue-i18n'
import { currentScene } from '../scene'

const { t, te } = useI18n()
const groupLabel = (g) => te(`group.${String(g.menuCode).replace('group_', '')}`) ? t(`group.${String(g.menuCode).replace('group_', '')}`) : g.menuName
const pageLabel = (p) => te(`nav.${p.menuCode}`) ? t(`nav.${p.menuCode}`) : p.menuName
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
  { code: 'view', label: t('rp.view') },
  { code: 'create', label: t('rp.createAction') },
  { code: 'edit', label: t('rp.editAction') },
  { code: 'delete', label: t('rp.deleteAction') },
  { code: 'approve', label: t('rp.approve') }
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
    const [m, r, p] = await Promise.all([api.menus(currentScene()), api.roles(currentScene()), api.projects()])
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
    notice.value = t('rp.savedPages')
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
async function saveActions() {
  if (!selected.value) return
  busy.value = true; error.value = ''
  try {
    await api.saveRoleActions(selected.value.id, selectedActions.value)
    notice.value = t('rp.savedActions')
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
    notice.value = t('rp.savedScope') 
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
    notice.value = t('rp.roleUpdated')
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
    if (!form.roleCode.trim() || !form.roleName.trim()) throw new Error(t('rp.required'))
    await api.createRole({ sceneCode: currentScene(), roleCode: form.roleCode.trim(), roleName: form.roleName.trim(), menuCodes: [] })
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
        <div class="panel-head"><div><h2>{{ t('rp.role') }}</h2><p>{{ roles.length }} {{ t('rp.roleCount') }}</p></div><button class="sm" @click="createOpen = true">{{ t('rp.add') }}</button></div>
        <input v-model="search" :placeholder="t('rp.searchRole')" style="margin-bottom:8px" />
        <div v-for="r in filteredRoles" :key="r.id" class="role-row" :class="{ active: selected && String(selected.id) === String(r.id) }" @click="selectRole(r)">
          <div style="flex:1;min-width:0"><div class="ellipsis">{{ r.roleName }}</div><div class="mono small muted ellipsis">{{ r.roleCode }}</div></div>
          <span class="badge">{{ r.menuCount }} {{ t('rp.itemUnit') }}</span>
        </div>
      </div>

      <div v-if="selected" class="role-detail">
        <div class="panel">
          <div class="panel-head"><div><h2>{{ selected.roleName }}</h2><p class="mono small muted">{{ selected.roleCode }} · {{ selectedPageCount }}/{{ pageCount }} {{ t('rp.pageCount') }} · {{ selectedActions.length }} {{ t('rp.funcCount') }}</p></div><div class="row"><button class="sm" @click="openRoleEdit">{{ t('rp.editTitle') }}</button><button class="sm danger" @click="askDelete">{{ t('rp.deleteTitle') }}</button></div></div>
          <div v-if="notice" class="alert success">{{ notice }}</div>
        </div>

        <div class="panel">
          <div class="panel-head"><div><h2>{{ t('rp.pagePerm') }}</h2><p>{{ t('rp.pagePermHint') }}</p></div><button class="primary" :disabled="busy" @click="savePages">{{ t('rp.savePerm') }}</button></div>
          <input v-model="pageSearch" :placeholder="t('rp.searchPage')" style="margin-bottom:10px" />
          <div class="perm-table">
            <div class="perm-head">
              <span>{{ t('rp.pageMenu') }}</span>
              <span v-for="a in actionOptions" :key="a.code" class="center">{{ a.label }}</span>
            </div>
            <div v-for="g in filteredGroups" :key="g.menuCode" class="perm-group">
              <div class="group-row">
                <label class="group-name">
                  <input type="checkbox" :checked="groupAll(g)" @change="toggleGroup(g)" />
                  <strong>{{ groupLabel(g) }}</strong>
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
                  <span>{{ pageLabel(p) }}</span>
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
          <div class="panel-head"><div><h2>{{ t('rp.members') }}</h2><p>{{ t('rp.membersHint') }}</p></div><span class="badge">{{ members.length }} {{ t('rp.memberUnit') }}</span></div>
          <div v-if="!members.length" class="empty">{{ t('rp.noMembers') }}</div>
          <div v-for="m in members" :key="m.id" class="entity-row"><div><strong>{{ m.displayName }}</strong><span class="small muted"> · {{ m.username }}</span></div><span class="badge" :class="m.userStatus === 'ENABLED' ? 'green' : 'orange'">{{ enumLabel(m.userStatus) }}</span></div>
        </div>

        <div class="panel">
          <div class="panel-head"><div><h2>{{ t('rp.scopeTitle') }}</h2><p>{{ t('rp.scopeHint') }}</p></div><button class="primary" :disabled="busy" @click="saveScope">{{ t('rp.saveScope') }}</button></div>
          <div class="scope-choice">
            <button class="scope-card" :class="{ active: scopeMode === 'NONE' }" @click="chooseScope('NONE')"><strong>{{ t('rp.none') }}</strong><span>{{ t('rp.noneHint') }}</span></button>
            <button class="scope-card" :class="{ active: scopeMode === 'ALL' }" @click="chooseScope('ALL')"><strong>{{ t('rp.all') }}</strong><span>{{ t('rp.allHint') }}</span></button>
            <button class="scope-card" :class="{ active: scopeMode === 'PROJECTS' }" @click="chooseScope('PROJECTS')"><strong>{{ t('rp.projects') }}</strong><span>{{ t('rp.projectsHint') }}</span></button>
            <button class="scope-card" :class="{ active: scopeMode === 'SELF' }" @click="chooseScope('SELF')"><strong>{{ t('rp.self') }}</strong><span>{{ t('rp.selfHint') }}</span></button>
          </div>
          <div v-if="scopeMode === 'PROJECTS'" style="margin-top:12px">
            <div class="scope-help">{{ t('rp.scopeHelp') }}</div>
            <input v-model="projectSearch" :placeholder="t('rp.searchProject')" style="margin:10px 0 8px" />
            <div class="scope-project-picker">
              <label v-for="p in filteredProjects" :key="p.id" class="project-option" :class="{ selected: scopeProjectIds.includes(String(p.id)) }">
                <input type="checkbox" :checked="scopeProjectIds.includes(String(p.id))" @change="toggleProject(p.id)" />
                <span>{{ p.orgName }}</span><span class="mono small muted">{{ p.orgCode }}</span>
              </label>
              <div v-if="!filteredProjects.length" class="empty">{{ t('rp.noMatchProject') }}</div>
            </div>
            <div class="row" style="justify-content:space-between;margin-top:8px"><span class="small">{{ t('rp.selectedCount', { n: scopeProjectIds.length }) }}</span><div class="row"><button class="sm" @click="selectAllProjects">{{ t('rp.selectAll') }}</button><button class="sm" @click="scopeProjectIds = []">{{ t('rp.clear') }}</button></div></div>
            <div v-if="selectedProjectNames.length" class="small muted" style="margin-top:6px">{{ t('rp.selected') }}: {{ selectedProjectNames.join(', ') }}</div>
          </div>
        </div>
      </div>
      <div v-else class="panel"><div class="empty">{{ t('rp.selectRole') }}</div></div>
    </div>

    <div v-if="editOpen" class="modal-mask" @click.self="editOpen = false">
      <div class="modal" style="max-width:480px">
        <div class="panel-head"><h2>{{ t('rp.editTitle') }}</h2><button class="sm" @click="editOpen = false">{{ t('rp.close') }}</button></div>
        <div class="field"><label>{{ t('rp.roleCode') }}</label><input :value="selected?.roleCode" disabled /></div>
        <div class="field"><label>{{ t('rp.roleName') }}</label><input v-model="editForm.roleName" /></div>
        <div class="field"><label>{{ t('rp.status') }}</label><select v-model="editForm.roleStatus"><option value="ENABLED">{{ t('rp.enable') }}</option><option value="DISABLED">{{ t('rp.disable') }}</option></select></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveRoleEdit">{{ t('rp.save') }}</button></div>
      </div>
    </div>

    <div v-if="deleteTarget" class="modal-mask" @click.self="deleteTarget = null">
      <div class="modal" style="max-width:480px">
        <div class="panel-head"><h2>{{ t('rp.deleteTitle') }}</h2><button class="sm" @click="deleteTarget = null">{{ t('rp.close') }}</button></div>
        <div class="alert">{{ t('rp.deleteMessage', { name: deleteTarget.roleName, code: deleteTarget.roleCode }) }}</div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="sm" @click="deleteTarget = null">{{ t('rp.cancel') }}</button><button class="danger" :disabled="busy" @click="confirmDelete">{{ busy ? t('rp.deleting') : t('rp.confirmDelete') }}</button></div>
      </div>
    </div>

    <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
      <div class="modal" style="max-width:480px">
        <div class="panel-head"><h2>{{ t('rp.createTitle') }}</h2><button class="sm" @click="createOpen = false">{{ t('rp.close') }}</button></div>
        <div class="field"><label>{{ t('rp.roleCode') }}</label><input v-model="form.roleCode" :placeholder="t('rp.codePlaceholder')" /></div>
        <div class="field"><label>{{ t('rp.roleName') }}</label><input v-model="form.roleName" :placeholder="t('rp.namePlaceholder')" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="createRole">{{ t('rp.create') }}</button></div>
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
