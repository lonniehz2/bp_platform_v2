<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Users from './Users.vue'
import Menus from './Menus.vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const tab = ref(route.params.tab || 'user')
const menus = ref([])
const error = ref('')
const tabList = [
  { key: 'user', label: '用户管理' },
  { key: 'role', label: '角色管理' },
  { key: 'perm', label: '权限清单' }
]
const flatMenus = computed(() => {
  const out = []
  const walk = (list, prefix = '') => {
    for (const m of list) {
      out.push({ code: m.menuCode, name: prefix + m.menuName, route: m.route })
      if (m.children?.length) walk(m.children, prefix + m.menuName + ' / ')
    }
  }
  walk(menus.value)
  return out
})

function switchTab(key) {
  tab.value = key
  router.replace(`/rbac/${key}`)
}

watch(() => route.params.tab, v => { tab.value = v || 'user' })
onMounted(async () => {
  try { menus.value = await api.menus('GUARANTEE') } catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>用户与权限</h2><p>用户、角色和权限清单</p></div></div>
      <div class="row">
        <button v-for="t in tabList" :key="t.key" class="sm" :class="{ primary: tab === t.key }" @click="switchTab(t.key)">{{ t.label }}</button>
      </div>
    </div>
    <div v-if="error" class="error">{{ error }}</div>
    <Users v-if="tab === 'user'" />
    <Menus v-else-if="tab === 'role'" />
    <div v-else class="panel">
      <div class="panel-head"><h2>权限清单</h2><span class="small muted">{{ flatMenus.length }} 项</span></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>权限编码</th><th>名称</th><th>路由</th></tr></thead>
          <tbody>
            <tr v-for="m in flatMenus" :key="m.code">
              <td class="mono">{{ m.code }}</td><td>{{ m.name }}</td><td class="mono">{{ m.route }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
