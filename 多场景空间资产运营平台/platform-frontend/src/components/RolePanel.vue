<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const roles = ref([])
const menus = ref([])
const selected = ref(null)
const selectedCodes = ref([])
const error = ref('')
const busy = ref(false)
const search = ref('')
const createOpen = ref(false)
const form = reactive({ roleCode: '', roleName: '' })
const filteredRoles = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return roles.value
  return roles.value.filter(r => (String(r.roleName) + ' ' + String(r.roleCode)).toLowerCase().includes(q))
})
const permissionRows = computed(() => {
  const rows = []
  const walk = (list, depth = 0) => {
    for (const m of list) {
      rows.push({ ...m, depth, group: m.menuType === 'GROUP' })
      if (m.children?.length) walk(m.children, depth + 1)
    }
  }
  walk(menus.value)
  return rows
})
const pageCount = computed(() => permissionRows.value.filter(r => !r.group).length)

async function load() {
  error.value = ''
  try {
    const [m, r] = await Promise.all([api.menus('GUARANTEE'), api.roles('GUARANTEE')])
    menus.value = m; roles.value = r
    const keep = selected.value && r.find(x => String(x.id) === String(selected.value.id))
    await selectRole(keep || r[0] || null)
  } catch (e) { error.value = e.message }
}

async function selectRole(r) {
  selected.value = r || null
  if (!r) { selectedCodes.value = []; return }
  try {
    const list = await api.roleMenus(r.id)
    selectedCodes.value = list.map(x => x.menuCode)
  } catch (e) { error.value = e.message; selectedCodes.value = [] }
}

function toggle(code) {
  const i = selectedCodes.value.indexOf(code)
  if (i >= 0) selectedCodes.value.splice(i, 1)
  else selectedCodes.value.push(code)
}

async function save() {
  if (!selected.value) return
  busy.value = true; error.value = ''
  try {
    await api.saveRoleMenus(selected.value.id, selectedCodes.value)
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
    <div class="grid" style="grid-template-columns:300px minmax(0,1fr)">
      <div class="panel">
        <div class="panel-head"><div><h2>角色</h2><p>{{ roles.length }} 个角色</p></div><button class="sm" @click="createOpen = true">新增</button></div>
        <input v-model="search" placeholder="搜索角色" style="margin-bottom:8px" />
        <div v-for="r in filteredRoles" :key="r.id" class="role-row" :class="{ active: selected && String(selected.id) === String(r.id) }" @click="selectRole(r)">
          <div style="flex:1"><div>{{ r.roleName }}</div><div class="mono small muted">{{ r.roleCode }}</div></div>
          <span class="badge">{{ r.menuCount }} 项</span>
        </div>
      </div>

      <div v-if="selected" class="panel">
        <div class="panel-head"><div><h2>{{ selected.roleName }}</h2><p class="mono small muted">{{ selected.roleCode }} · {{ pageCount }} 个可授权页面</p></div><button class="primary" :disabled="busy" @click="save">保存权限</button></div>
        <div class="alert">勾选页面权限。分组只做展示，不可授权。</div>
        <div class="perm-list">
          <div v-for="m in permissionRows" :key="m.menuCode" class="perm-row" :class="{ group: m.group }" :style="{ paddingLeft: (10 + m.depth * 18) + 'px' }">
            <template v-if="m.group"><strong>{{ m.menuName }}</strong></template>
            <label v-else class="row" style="gap:6px;cursor:pointer"><input type="checkbox" :checked="selectedCodes.includes(m.menuCode)" @change="toggle(m.menuCode)" /><span>{{ m.menuName }}</span><span class="mono small muted">{{ m.menuCode }}</span></label>
          </div>
        </div>
      </div>
      <div v-else class="panel"><div class="empty">请选择角色</div></div>
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
.role-row { display:flex; align-items:center; gap:8px; padding:10px 8px; border-bottom:1px solid var(--line); cursor:pointer; border-radius:5px; }
.role-row:hover, .role-row.active { background:var(--brand-soft); color:var(--brand); }
.perm-list { max-height:520px; overflow:auto; border:1px solid var(--line); border-radius:6px; padding:6px; }
.perm-row { min-height:32px; display:flex; align-items:center; border-radius:4px; }
.perm-row.group { margin-top:6px; color:var(--muted); font-size:12px; }
.perm-row:not(.group):hover { background:var(--bg); }
</style>
