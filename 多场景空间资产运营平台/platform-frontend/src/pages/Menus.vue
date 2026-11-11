<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'
import { currentScene, scenePath } from '../scene'

const { t } = useI18n()
const props = defineProps({ embedded: Boolean })
const menus = ref([])
const roles = ref([])
const roleMenus = ref([])
const selectedRole = ref(null)
const selectedCodes = ref([])
const error = ref('')
const busy = ref(false)
const newRole = reactive({ roleCode: '', roleName: '' })

const flatMenus = computed(() => {
  const out = []
  const walk = (list, prefix = '') => {
    for (const m of list) {
      if (m.menuType !== 'GROUP') out.push({ code: m.menuCode, name: prefix + m.menuName })
      if (m.children?.length) walk(m.children, prefix + m.menuName + ' / ')
    }
  }
  walk(menus.value)
  return out
})

async function load() {
  try {
    const [m, r] = await Promise.all([api.menus(currentScene()), api.roles(currentScene())])
    menus.value = m
    roles.value = r
    if (r.length) await selectRole(r[0])
  } catch (e) { error.value = e.message }
}

async function selectRole(role) {
  selectedRole.value = role
  roleMenus.value = await api.roleMenus(role.id)
  selectedCodes.value = roleMenus.value.map(m => m.menuCode)
}

function toggleCode(code) {
  const i = selectedCodes.value.indexOf(code)
  if (i >= 0) selectedCodes.value.splice(i, 1)
  else selectedCodes.value.push(code)
}

async function saveMenus() {
  busy.value = true; error.value = ''
  try {
    await api.saveRoleMenus(selectedRole.value.id, selectedCodes.value)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function createRole() {
  busy.value = true; error.value = ''
  try {
    if (!newRole.roleCode.trim() || !newRole.roleName.trim()) throw new Error(t('menus.required'))
    await api.createRole({ sceneCode: currentScene(), roleCode: newRole.roleCode.trim(), roleName: newRole.roleName.trim(), menuCodes: [] })
    newRole.roleCode = ''; newRole.roleName = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div v-if="!props.embedded" class="panel-head"><div><h2>{{ t('menus.title') }}</h2><p>{{ currentScene() }} · {{ t('menus.subtitle') }}</p></div><span class="badge blue">{{ roles.length }} {{ t('menus.count') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('menus.roleCode') }}</label><input v-model="newRole.roleCode" :placeholder="t('menus.roleCodePlaceholder')" /></div>
        <div class="field"><label>{{ t('menus.roleName') }}</label><input v-model="newRole.roleName" :placeholder="t('menus.roleNamePlaceholder')" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="createRole">{{ t('menus.add') }}</button></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns: 1.1fr .9fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('menus.permissions') }}</h2><span class="small muted">{{ flatMenus.length }} {{ t('menus.menuCount') }}</span></div>
        <div v-if="!menus.length" class="empty">{{ t('menus.emptyMenus') }}</div>
        <div v-for="m in menus" :key="m.menuCode" style="padding:9px 0;border-bottom:1px solid var(--line)">
          <div class="row"><strong>{{ m.menuName }}</strong><span class="mono">{{ m.route ? scenePath(m.route) : '' }}</span></div>
          <div v-if="m.children?.length" class="row" style="margin:6px 0 0 18px">
            <span v-for="c in m.children" :key="c.menuCode" class="badge blue">{{ c.menuName }}</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('menus.templates') }}</h2><span class="small muted">{{ t('menus.assignHint') }}</span></div>
        <div v-if="!roles.length" class="empty">{{ t('menus.emptyRoles') }}</div>
        <div v-for="r in roles" :key="r.id" class="row" style="padding:9px 0;border-bottom:1px solid var(--line);cursor:pointer" @click="selectRole(r)">
          <div style="flex:1"><div>{{ r.roleName }}</div><div class="mono">{{ r.roleCode }}</div></div>
          <span class="badge">{{ r.menuCount }} {{ t('menus.menuUnit') }}</span>
        </div>
      </div>
    </div>

    <div v-if="selectedRole" class="panel">
      <div class="panel-head"><div><h2>{{ selectedRole.roleName }} · {{ t('menus.auth') }}</h2><p>{{ selectedRole.roleCode }}</p></div><button class="primary" :disabled="busy" @click="saveMenus">{{ t('menus.save') }}</button></div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(180px,1fr))">
        <label v-for="m in flatMenus" :key="m.code" class="row" style="gap:6px;align-items:center;padding:5px 0">
          <input type="checkbox" :checked="selectedCodes.includes(m.code)" @change="toggleCode(m.code)" style="width:auto" />
          <span class="small">{{ m.name }}</span>
        </label>
      </div>
      <div v-if="!flatMenus.length" class="empty">{{ t('menus.emptyMenus') }}</div>
    </div>
  </div>
</template>
