<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const users = ref([])
const roles = ref([])
const projects = ref([])
const scopeUser = ref(null)
const scopeMode = ref('inherit')
const scopeProjectIds = ref([])
const scopeNotice = ref('')
const error = ref('')
const busy = ref(false)
const search = ref('')
const createOpen = ref(false)
const editing = ref(null)
const createForm = reactive({ username: '', password: '', displayName: '', roleIds: [] })
const editForm = reactive({ displayName: '', password: '', roleIds: [], userStatus: 'ENABLED' })
const hasOverride = (u) => Number(u.scopeOverrideEnabled) > 0
const selectedProjectNames = computed(() => projects.value.filter(p => scopeProjectIds.value.includes(String(p.id))).map(p => p.orgName))
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
    if (!createForm.username.trim() || !createForm.displayName.trim() || createForm.password.length < 6) throw new Error('用户名、姓名必填，密码至少 6 位')
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
  } catch (e) { error.value = e.message }
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
    scopeNotice.value = limit ? `已保存：单独限制 ${scopeProjectIds.value.length} 个项目` : '已保存：跟随角色范围'
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

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>用户管理</h2><p>账号、角色、启用/停用</p></div><span class="badge blue">{{ users.length }} 个用户</span></div>
      <div class="row">
        <input v-model="search" placeholder="搜索用户名/姓名" style="max-width:260px" />
        <button class="primary" @click="openCreate">新增用户</button>
      </div>
    </div>

    <div class="panel">
      <div class="table-wrap">
        <table>
          <thead><tr><th>用户名</th><th>姓名</th><th>角色</th><th>数据范围</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="u in filtered" :key="u.id">
              <td class="mono">{{ u.username }}</td><td>{{ u.displayName }}</td>
              <td><span v-for="r in u.roleNames" :key="r" class="badge blue" style="margin-right:4px">{{ r }}</span><span v-if="!u.roleNames?.length" class="muted">未分配</span></td>
              <td><span v-if="hasOverride(u)" class="badge orange">单独限制 · {{ u.scopeProjectCount || 0 }} 个项目</span><span v-else class="badge">跟随角色</span></td>
              <td><span class="badge" :class="u.userStatus === 'ENABLED' ? 'green' : 'orange'">{{ u.userStatus }}</span></td>
              <td><div class="row"><button class="sm" @click="openEdit(u)">编辑</button><button class="sm" @click="openScope(u)">数据范围</button><button class="sm" :class="u.userStatus === 'ENABLED' ? 'danger' : ''" :disabled="busy" @click="toggle(u)">{{ u.userStatus === 'ENABLED' ? '停用' : '启用' }}</button></div></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
      <div class="modal" style="max-width:560px">
        <div class="panel-head"><h2>新增用户</h2><button class="sm" @click="createOpen = false">关闭</button></div>
        <div class="field"><label>用户名</label><input v-model="createForm.username" /></div>
        <div class="field"><label>姓名</label><input v-model="createForm.displayName" /></div>
        <div class="field"><label>初始密码</label><input v-model="createForm.password" type="password" /></div>
        <div class="field"><label>角色</label><select v-model="createForm.roleIds" multiple size="5"><option v-for="r in roles" :key="r.id" :value="r.id">{{ r.roleName }}（{{ r.roleCode }}）</option></select></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="createUser">创建</button></div>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal" style="max-width:560px">
        <div class="panel-head"><h2>编辑用户</h2><button class="sm" @click="editing = null">关闭</button></div>
        <div class="field"><label>用户名</label><input :value="editing.username" disabled /></div>
        <div class="field"><label>姓名</label><input v-model="editForm.displayName" /></div>
        <div class="field"><label>新密码（留空不改）</label><input v-model="editForm.password" type="password" /></div>
        <div class="field"><label>角色</label><select v-model="editForm.roleIds" multiple size="5"><option v-for="r in roles" :key="r.id" :value="r.id">{{ r.roleName }}（{{ r.roleCode }}）</option></select></div>
        <div class="field"><label>状态</label><select v-model="editForm.userStatus"><option value="ENABLED">启用</option><option value="DISABLED">停用</option></select></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveEdit">保存</button></div>
      </div>
    </div>

    <div v-if="scopeUser" class="modal-mask" @click.self="scopeUser = null">
      <div class="modal scope-modal" style="max-width:620px">
        <div class="panel-head"><div><h2>数据范围</h2><p class="small muted">{{ scopeUser.displayName }}（{{ scopeUser.username }}）</p></div><button class="sm" @click="scopeUser = null">关闭</button></div>
        <div v-if="scopeNotice" class="alert success">{{ scopeNotice }}</div>
        <div class="alert">
          <div><strong>当前：</strong><span v-if="hasOverride(scopeUser)">单独限制 · {{ scopeUser.scopeProjectCount || 0 }} 个项目</span><span v-else>跟随角色</span></div>
          <div class="small muted" style="margin-top:4px">角色：{{ scopeUser.roleNames?.join('、') || '未分配角色' }}</div>
        </div>
        <div class="scope-choice">
          <button class="scope-card" :class="{ active: scopeMode === 'inherit' }" @click="chooseScopeMode('inherit')">
            <strong>跟随角色范围</strong>
            <span>用户可见范围由角色决定，不单独限制。</span>
          </button>
          <button class="scope-card" :class="{ active: scopeMode === 'limit' }" @click="chooseScopeMode('limit')">
            <strong>单独限制</strong>
            <span>只允许缩小角色范围，不能扩大。</span>
          </button>
        </div>
        <div v-if="scopeMode === 'limit'">
          <div class="row" style="justify-content:space-between;margin:12px 0 6px">
            <span class="small">已选 {{ scopeProjectIds.length }} 个项目</span>
            <button class="sm" @click="scopeProjectIds = []">清空</button>
          </div>
          <div v-if="selectedProjectNames.length" class="small" style="margin-bottom:6px">{{ selectedProjectNames.join('、') }}</div>
          <select v-model="scopeProjectIds" multiple size="7">
            <option v-for="p in projects" :key="p.id" :value="String(p.id)">{{ p.orgName }}（{{ p.orgCode }}）</option>
          </select>
          <div class="small muted" style="margin-top:6px">不选项目表示该用户没有项目数据。</div>
        </div>
        <div v-else class="alert">保存后清除该用户的单独范围，恢复为角色默认范围。</div>
        <div class="row" style="justify-content:flex-end;margin-top:16px"><button class="sm" @click="scopeUser = null">取消</button><button class="primary" :disabled="busy" @click="saveScope">{{ busy ? '保存中…' : '保存' }}</button></div>
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
</style>
