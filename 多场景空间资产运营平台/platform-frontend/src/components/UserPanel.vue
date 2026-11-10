<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const users = ref([])
const roles = ref([])
const projects = ref([])
const scopeUser = ref(null)
const scopeForm = reactive({ overrideEnabled: false, projectIds: [] })
const error = ref('')
const busy = ref(false)
const search = ref('')
const createOpen = ref(false)
const editing = ref(null)
const createForm = reactive({ username: '', password: '', displayName: '', roleIds: [] })
const editForm = reactive({ displayName: '', password: '', roleIds: [], userStatus: 'ENABLED' })
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
  try {
    const sc = await api.userScopes(u.id)
    scopeForm.overrideEnabled = !!sc.overrideEnabled
    scopeForm.projectIds = (sc.projectIds || []).map(String)
  } catch (e) { error.value = e.message }
}

async function saveScope() {
  if (!scopeUser.value) return
  busy.value = true; error.value = ''
  try {
    await api.updateUserScopes(scopeUser.value.id, { projectIds: scopeForm.projectIds.map(Number), orgIds: [], overrideEnabled: scopeForm.overrideEnabled })
    scopeUser.value = null
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
          <thead><tr><th>用户名</th><th>姓名</th><th>角色</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="u in filtered" :key="u.id">
              <td class="mono">{{ u.username }}</td><td>{{ u.displayName }}</td>
              <td><span v-for="r in u.roleNames" :key="r" class="badge blue" style="margin-right:4px">{{ r }}</span><span v-if="!u.roleNames?.length" class="muted">未分配</span></td>
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
      <div class="modal" style="max-width:560px">
        <div class="panel-head"><h2>数据范围</h2><button class="sm" @click="scopeUser = null">关闭</button></div>
        <div class="alert">默认继承角色范围。开启单独限制后只能缩小，不能扩大。</div>
        <div class="field"><label><input type="checkbox" v-model="scopeForm.overrideEnabled" /> 单独限制该用户的数据范围</label></div>
        <div v-if="scopeForm.overrideEnabled" class="field"><label>项目范围</label><select v-model="scopeForm.projectIds" multiple size="6"><option v-for="p in projects" :key="p.id" :value="String(p.id)">{{ p.orgName }}（{{ p.orgCode }}）</option></select></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveScope">保存</button></div>
      </div>
    </div>
  </div>
</template>
