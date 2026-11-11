<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const users = ref([])
const roles = ref([])
const projects = ref([])
const scopeUser = ref(null)
const archiveTarget = ref(null)
const scopeMode = ref('inherit')
const scopeProjectIds = ref([])
const scopeNotice = ref('')
const error = ref('')
const busy = ref(false)
const search = ref('')
const page = ref(1)
const pageSize = ref(10)
const previewUser = ref(null)
const preview = ref(null)
const createOpen = ref(false)
const editing = ref(null)
const createForm = reactive({ username: '', password: '', displayName: '', roleIds: [] })
const editForm = reactive({ displayName: '', password: '', roleIds: [], userStatus: 'ENABLED' })
const hasOverride = (u) => Number(u.scopeOverrideEnabled) > 0
const projectSearch = ref('')
const filteredProjects = computed(() => {
  const q = projectSearch.value.trim().toLowerCase()
  return projects.value.filter(p => !q || (String(p.orgName) + ' ' + String(p.orgCode)).toLowerCase().includes(q))
})
const selectedProjectNames = computed(() => projects.value.filter(p => scopeProjectIds.value.includes(String(p.id))).map(p => p.orgName))
const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize.value)))
const pagedUsers = computed(() => filtered.value.slice((page.value - 1) * pageSize.value, page.value * pageSize.value))
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter(u => (String(u.username) + ' ' + String(u.displayName || '')).toLowerCase().includes(q))
})

async function load() {
  error.value = ''
  try {
    const [u, r, p] = await Promise.all([api.users(), api.userRoles(), api.projects()])
    users.value = u; roles.value = r; projects.value = p
  } catch (e) { error.value = e.message }
}

function roleIdsOf(u) {
  return roles.value.filter(r => (u.roleCodes || []).includes(r.roleCode)).map(r => r.id)
}

function openCreate() {
  createForm.username = ''; createForm.password = ''; createForm.displayName = ''; createForm.roleIds = []
  createOpen.value = true
}

async function createUser() {
  busy.value = true; error.value = ''
  try {
    if (!createForm.username.trim() || !createForm.displayName.trim() || createForm.password.length < 6) throw new Error(t('up.required'))
    await api.createUser({ username: createForm.username.trim(), password: createForm.password, displayName: createForm.displayName.trim(), roleIds: createForm.roleIds })
    createOpen.value = false
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openEdit(u) {
  editing.value = u
  editForm.displayName = u.displayName || ''
  editForm.password = ''
  editForm.userStatus = u.userStatus || 'ENABLED'
  editForm.roleIds = roleIdsOf(u)
}

async function saveEdit() {
  busy.value = true; error.value = ''
  try {
    const body = { displayName: editForm.displayName.trim(), roleIds: editForm.roleIds, userStatus: editForm.userStatus }
    if (editForm.password) body.password = editForm.password
    await api.updateUser(editing.value.id, body)
    editing.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function openScope(u) {
  scopeUser.value = u
  error.value = ''
  scopeNotice.value = ''
  try {
    const sc = await api.userScopes(u.id)
    scopeMode.value = sc.overrideEnabled ? 'limit' : 'inherit'
    scopeProjectIds.value = (sc.projectIds || []).map(String)
    projectSearch.value = ''
  } catch (e) { error.value = e.message }
}

function toggleProject(id) {
  const key = String(id)
  const i = scopeProjectIds.value.indexOf(key)
  if (i >= 0) scopeProjectIds.value.splice(i, 1)
  else scopeProjectIds.value.push(key)
}

function selectAllFiltered() {
  for (const p of filteredProjects.value) {
    const key = String(p.id)
    if (!scopeProjectIds.value.includes(key)) scopeProjectIds.value.push(key)
  }
}

function chooseScopeMode(mode) {
  scopeMode.value = mode
  scopeNotice.value = ''
  if (mode === 'inherit') scopeProjectIds.value = []
}

async function saveScope() {
  if (!scopeUser.value) return
  busy.value = true; error.value = ''
  scopeNotice.value = ''
  try {
    const limit = scopeMode.value === 'limit'
    const saved = await api.updateUserScopes(scopeUser.value.id, {
      projectIds: limit ? scopeProjectIds.value.map(Number) : [],
      orgIds: [],
      overrideEnabled: limit
    })
    scopeMode.value = saved.overrideEnabled ? 'limit' : 'inherit'
    scopeProjectIds.value = (saved.projectIds || []).map(String)
    scopeNotice.value = limit ? t('up.savedLimit', { n: scopeProjectIds.value.length }) : t('up.savedInherit')
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function askArchive(u) { archiveTarget.value = u; error.value = '' }

async function confirmArchive() {
  if (!archiveTarget.value) return
  busy.value = true; error.value = ''
  try {
    await api.archiveUser(archiveTarget.value.id)
    archiveTarget.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function toggle(u) {
  busy.value = true; error.value = ''
  try {
    await api.updateUser(u.id, { userStatus: u.userStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED' })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

watch(search, () => { page.value = 1 })

async function openPreview(u) {
  previewUser.value = u; preview.value = null; error.value = ''
  try {
    const [perms, scope] = await Promise.all([api.effectivePermissions(u.id), api.effectiveScope(u.id)])
    preview.value = { ...perms, ...scope }
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('up.title') }}</h2><p>{{ t('up.subtitle') }}</p></div><span class="badge blue">{{ users.length }} {{ t('up.count') }}</span></div>
      <div class="row">
        <input v-model="search" :placeholder="t('up.search')" style="max-width:260px" />
        <button class="primary" @click="openCreate">{{ t('up.createTitle') }}</button>
      </div>
    </div>

    <div class="panel">
      <div class="table-wrap">
        <table>
          <thead><tr><th>{{ t('up.username') }}</th><th>{{ t('up.name') }}</th><th>{{ t('up.roles') }}</th><th>{{ t('up.scope') }}</th><th>{{ t('up.status') }}</th><th>{{ t('up.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="u in pagedUsers" :key="u.id">
              <td class="mono">{{ u.username }}</td><td>{{ u.displayName }}</td>
              <td><span v-for="r in u.roleNames" :key="r" class="badge blue" style="margin-right:4px">{{ r }}</span><span v-if="!u.roleNames?.length" class="muted">{{ t('up.unassigned') }}</span></td>
              <td><span v-if="hasOverride(u)" class="badge orange">{{ t('up.override', { n: u.scopeProjectCount || 0 }) }}</span><span v-else class="badge">{{ t('up.follow') }}</span></td>
              <td><span class="badge" :class="u.userStatus === 'ENABLED' ? 'green' : 'orange'">{{ u.userStatus }}</span></td>
              <td><div class="row"><button class="sm" @click="openEdit(u)">{{ t('up.edit') }}</button><button class="sm" @click="openScope(u)">{{ t('up.scope') }}</button><button class="sm" @click="openPreview(u)">{{ t('up.previewBtn') }}</button><button class="sm danger" @click="askArchive(u)">{{ t('up.delete') }}</button><button class="sm" :class="u.userStatus === 'ENABLED' ? 'danger' : ''" :disabled="busy" @click="toggle(u)">{{ u.userStatus === 'ENABLED' ? t('up.disable') : t('up.enable') }}</button></div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="row" style="justify-content:flex-end;margin-top:8px"><button class="sm" :disabled="page <= 1" @click="page--">{{ t('up.prev') }}</button><span class="small muted">{{ page }} / {{ pageCount }} · {{ filtered.length }} {{ t('up.people') }}</span><button class="sm" :disabled="page >= pageCount" @click="page++">{{ t('up.next') }}</button></div>

    <div v-if="previewUser" class="modal-mask" @click.self="previewUser = null">
      <div class="modal" style="max-width:620px">
        <div class="panel-head"><div><h2>{{ t('up.previewTitle') }}</h2><p class="small muted">{{ previewUser.displayName }}（{{ previewUser.username }}）</p></div><button class="sm" @click="previewUser = null">{{ t('up.close') }}</button></div>
        <div v-if="!preview" class="empty">{{ t('up.loading') }}</div>
        <template v-else>
          <div class="alert"><strong>{{ t('up.roleLabel') }}:</strong>{{ preview.roles?.join(', ') || t('up.unassigned') }}</div>
          <div class="alert"><strong>{{ t('up.pagePerm')+': ' }}</strong>{{ preview.pageCodes?.length || 0 }} {{ t('up.itemUnit') }}</div>
          <div class="small muted" style="margin:6px 0 12px">{{ preview.pageCodes?.join(', ') || '-' }}</div>
          <div class="alert"><strong>{{ t('up.actionPerm')+': ' }}</strong>{{ preview.actionCodes?.length || 0 }} {{ t('up.itemUnit') }}</div>
          <div class="alert"><strong>{{ t('up.scopeLabel')+': ' }}</strong><span v-if="preview.allProjects">{{ t('up.allProjects') }}</span><span v-else>{{ t('up.projectsCount', { n: preview.effectiveProjectIds?.length || 0 }) }}</span><span v-if="preview.overrideEnabled" class="badge orange">{{ t('up.exception') }}</span></div>
        </template>
      </div>
    </div>

    <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
      <div class="modal" style="max-width:560px">
        <div class="panel-head"><h2>{{ t('up.createTitle') }}</h2><button class="sm" @click="createOpen = false">{{ t('up.close') }}</button></div>
        <div class="field"><label>{{ t('up.username') }}</label><input v-model="createForm.username" /></div>
        <div class="field"><label>{{ t('up.name') }}</label><input v-model="createForm.displayName" /></div>
        <div class="field"><label>{{ t('up.initialPassword') }}</label><input v-model="createForm.password" type="password" /></div>
        <div class="field"><label>{{ t('up.roles') }}</label><select v-model="createForm.roleIds" multiple size="5"><option v-for="r in roles" :key="r.id" :value="r.id">{{ r.roleName }}（{{ r.roleCode }}）</option></select></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="createUser">{{ t('up.create') }}</button></div>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal" style="max-width:560px">
        <div class="panel-head"><h2>{{ t('up.editTitle') }}</h2><button class="sm" @click="editing = null">{{ t('up.close') }}</button></div>
        <div class="field"><label>{{ t('up.username') }}</label><input :value="editing.username" disabled /></div>
        <div class="field"><label>{{ t('up.name') }}</label><input v-model="editForm.displayName" /></div>
        <div class="field"><label>{{ t('up.newPassword') }}</label><input v-model="editForm.password" type="password" /></div>
        <div class="field"><label>{{ t('up.roles') }}</label><select v-model="editForm.roleIds" multiple size="5"><option v-for="r in roles" :key="r.id" :value="r.id">{{ r.roleName }}（{{ r.roleCode }}）</option></select></div>
        <div class="field"><label>{{ t('up.status') }}</label><select v-model="editForm.userStatus"><option value="ENABLED">{{ t('up.enable') }}</option><option value="DISABLED">{{ t('up.disable') }}</option></select></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveEdit">{{ t('up.save') }}</button></div>
      </div>
    </div>

    <div v-if="archiveTarget" class="modal-mask" @click.self="archiveTarget = null">
      <div class="modal" style="max-width:460px">
        <div class="panel-head"><h2>{{ t('up.deleteTitle') }}</h2><button class="sm" @click="archiveTarget = null">{{ t('up.close') }}</button></div>
        <div class="alert">{{ t('up.deleteMessage', { name: archiveTarget.displayName, username: archiveTarget.username }) }}</div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="sm" @click="archiveTarget = null">{{ t('up.cancel') }}</button><button class="danger" :disabled="busy" @click="confirmArchive">{{ busy ? t('up.deleting') : t('up.confirmDelete') }}</button></div>
      </div>
    </div>

    <div v-if="scopeUser" class="modal-mask" @click.self="scopeUser = null">
      <div class="modal scope-modal" style="max-width:620px">
        <div class="panel-head"><div><h2>{{ t('up.scope') }}</h2><p class="small muted">{{ scopeUser.displayName }}（{{ scopeUser.username }}）</p></div><button class="sm" @click="scopeUser = null">{{ t('up.close') }}</button></div>
        <div v-if="scopeNotice" class="alert success">{{ scopeNotice }}</div>
        <div class="alert">
          <div><strong>{{ t('up.current')+': ' }}</strong><span v-if="hasOverride(scopeUser)">{{ t('up.singleLimit', { n: scopeUser.scopeProjectCount || 0 }) }}</span><span v-else>{{ t('up.follow') }}</span></div>
          <div class="small muted" style="margin-top:4px">{{ t('up.roleLabel') }}: {{ scopeUser.roleNames?.join(', ') || t('up.noRole') }}</div>
        </div>
        <div class="scope-choice">
          <button class="scope-card" :class="{ active: scopeMode === 'inherit' }" @click="chooseScopeMode('inherit')">
            <strong>{{ t('up.inherit') }}</strong>
            <span>{{ t('up.inheritHint') }}</span>
          </button>
          <button class="scope-card" :class="{ active: scopeMode === 'limit' }" @click="chooseScopeMode('limit')">
            <strong>{{ t('up.limit') }}</strong>
            <span>{{ t('up.limitHint') }}</span>
          </button>
        </div>
        <div v-if="scopeMode === 'limit'">
          <div class="scope-help">{{ t('up.scopeHelp') }}</div>
          <input v-model="projectSearch" :placeholder="t('up.searchProject')" style="margin:10px 0 8px" />
          <div class="project-picker">
            <label v-for="p in filteredProjects" :key="p.id" class="project-option" :class="{ selected: scopeProjectIds.includes(String(p.id)) }">
              <input type="checkbox" :checked="scopeProjectIds.includes(String(p.id))" @change="toggleProject(p.id)" />
              <span>{{ p.orgName }}</span><span class="mono small muted">{{ p.orgCode }}</span>
            </label>
            <div v-if="!filteredProjects.length" class="empty">{{ t('up.noMatch') }}</div>
          </div>
          <div class="row" style="justify-content:space-between;margin-top:8px">
            <span class="small">{{ t('up.selectedN', { n: scopeProjectIds.length }) }}</span>
            <div class="row"><button class="sm" @click="selectAllFiltered">{{ t('up.selectAll') }}</button><button class="sm" @click="scopeProjectIds = []">{{ t('up.clear') }}</button></div>
          </div>
          <div v-if="selectedProjectNames.length" class="small muted" style="margin-top:6px">{{ t('up.selected') }}: {{ selectedProjectNames.join(', ') }}</div>
        </div>
        <div v-else class="alert">{{ t('up.inheritHint2') }}</div>
        <div class="row" style="justify-content:flex-end;margin-top:16px"><button class="sm" @click="scopeUser = null">{{ t('up.cancel') }}</button><button class="primary" :disabled="busy" @click="saveScope">{{ busy ? t('up.saving') : t('up.save') }}</button></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scope-choice { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; }
.scope-card { text-align:left; padding:12px; border:1px solid var(--line); border-radius:8px; background:var(--bg); cursor:pointer; display:flex; flex-direction:column; gap:4px; }
.scope-card strong { font-size:14px; }
.scope-card span { font-size:12px; color:var(--muted); line-height:1.5; }
.scope-card.active { border-color:var(--brand); background:var(--brand-soft); }
.alert.success { background:#ecfdf5; color:#047857; border-color:#a7f3d0; }
.scope-help { margin-top:12px; padding:10px 12px; background:#eff6ff; border:1px solid #bfdbfe; color:#1d4ed8; border-radius:6px; font-size:12px; line-height:1.7; }
.project-picker { width:100%; max-height:260px; overflow:auto; border:1px solid var(--line); border-radius:6px; padding:4px; box-sizing:border-box; }
.project-option { display:flex; align-items:center; gap:8px; padding:8px; border-radius:4px; cursor:pointer; }
.project-option:hover, .project-option.selected { background:var(--brand-soft); }
.project-option input { width:auto; }
.project-option .mono { margin-left:auto; }
</style>
