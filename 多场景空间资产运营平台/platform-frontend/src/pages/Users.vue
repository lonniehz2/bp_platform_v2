<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const props = defineProps({ embedded: Boolean })

const users = ref([])
const roles = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ username: '', displayName: '', password: '', roleIds: [] })
const edit = reactive({ id: '', password: '', displayName: '', roleIds: [] })
const scopeUser = ref(null)
const scopeProjectIds = ref([])
const scopeOrgIds = ref([])
const scopeOptions = ref([])

async function load() {
  error.value = ''
  try {
    const [u, r] = await Promise.all([api.users(), api.userRoles()])
    users.value = u; roles.value = r
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.username.trim() || !form.displayName.trim() || form.password.length < 6) {
      throw new Error('请填写用户名、姓名，密码至少 6 位')
    }
    await api.createUser({
      username: form.username.trim(), displayName: form.displayName.trim(),
      password: form.password, roleIds: form.roleIds.map(Number)
    })
    form.username = ''; form.displayName = ''; form.password = ''; form.roleIds = []
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

function openEdit(u) {
  edit.id = u.id; edit.displayName = u.displayName || ''; edit.password = ''
  edit.roleIds = roles.value.filter(r => (u.roleCodes || []).includes(r.roleCode)).map(r => r.id)
}

async function saveEdit() {
  busy.value = true; error.value = ''
  try {
    await api.updateUser(edit.id, { displayName: edit.displayName, password: edit.password, roleIds: edit.roleIds.map(Number) })
    edit.id = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function openScopes(u) {
  error.value = ''
  try {
    const [sc, projects] = await Promise.all([api.userScopes(u.id), api.projects()])
    scopeUser.value = u
    scopeProjectIds.value = (sc.projectIds || []).map(String)
    scopeOrgIds.value = (sc.orgIds || []).map(String)
    scopeOptions.value = projects || []
  } catch (e) { error.value = e.message }
}

async function saveScopes() {
  busy.value = true; error.value = ''
  try {
    await api.updateUserScopes(scopeUser.value.id, {
      projectIds: scopeProjectIds.value.map(Number),
      orgIds: scopeOrgIds.value.map(Number)
    })
    scopeUser.value = null
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div v-if="!props.embedded" class="panel-head"><div><h2>用户管理</h2><p>平台账号、角色绑定、启用/停用</p></div><span class="badge blue">{{ users.length }} 个用户</span></div>
      <div class="row">
        <div class="field"><label>用户名</label><input v-model="form.username" /></div>
        <div class="field"><label>姓名</label><input v-model="form.displayName" /></div>
        <div class="field"><label>初始密码</label><input v-model="form.password" type="password" /></div>
        <div class="field" style="flex:2"><label>角色</label>
          <select v-model="form.roleIds" multiple size="3"><option v-for="r in roles" :key="r.id" :value="r.id">{{ r.roleName }}（{{ r.roleCode }}）</option></select>
        </div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('config')" class="primary" :disabled="busy" @click="create">新增用户</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>用户列表</h2><span class="small muted">启用/停用、重置密码</span></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>用户名</th><th>姓名</th><th>角色</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="mono">{{ u.username }}</td><td>{{ u.displayName }}</td>
              <td><span v-for="r in u.roleNames" :key="r" class="badge blue" style="margin-right:4px">{{ r }}</span></td>
              <td><span class="badge" :class="u.userStatus === 'ENABLED' ? 'green' : 'orange'">{{ u.userStatus }}</span></td>
              <td class="small">{{ u.createTime }}</td>
              <td class="row">
                <button v-if="can('config')" class="sm" @click="openScopes(u)">数据范围</button>
                <button v-if="can('config')" class="sm" @click="openEdit(u)">改密</button>
                <button v-if="can('config')" class="sm" @click="toggle(u)">{{ u.userStatus === 'ENABLED' ? '停用' : '启用' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="scopeUser" class="panel">
      <div class="panel-head"><h2>数据范围</h2><span class="small muted">{{ scopeUser.username }}</span><button class="sm" @click="scopeUser = null">关闭</button></div>
      <div class="alert">项目范围用于人员查询；组织范围用于财务收费数据。管理员不受范围限制。</div>
      <div class="row">
        <div class="field" style="flex:1"><label>项目范围</label>
          <select v-model="scopeProjectIds" multiple size="6">
            <option v-for="p in scopeOptions" :key="p.id" :value="String(p.id)">{{ p.orgName }}（{{ p.orgCode }}）</option>
          </select>
        </div>
        <div class="field" style="flex:1"><label>组织范围</label>
          <select v-model="scopeOrgIds" multiple size="6">
            <option v-for="p in scopeOptions" :key="p.id" :value="String(p.id)">{{ p.orgName }}（{{ p.orgCode }}）</option>
          </select>
        </div>
      </div>
      <div class="row" style="justify-content:flex-end;margin-top:10px"><button class="primary" :disabled="busy" @click="saveScopes">保存范围</button></div>
    </div>

    <div v-if="edit.id" class="panel">
      <div class="panel-head"><h2>编辑用户</h2><button class="sm" @click="edit.id = ''">关闭</button></div>
      <div class="row">
        <div class="field"><label>姓名</label><input v-model="edit.displayName" /></div>
        <div class="field"><label>新密码（留空不改）</label><input v-model="edit.password" type="password" /></div>
        <div class="field" style="flex:2"><label>角色</label><select v-model="edit.roleIds" multiple size="3"><option v-for="r in roles" :key="r.id" :value="r.id">{{ r.roleName }}（{{ r.roleCode }}）</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="saveEdit">保存</button></div>
      </div>
    </div>
  </div>
</template>
