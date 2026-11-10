<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserPanel from '../components/UserPanel.vue'
import RolePanel from '../components/RolePanel.vue'
import PermissionPanel from '../components/PermissionPanel.vue'

const route = useRoute()
const router = useRouter()
const tab = ref(route.params.tab || 'user')
const tabs = [
  { key: 'user', label: '用户管理' },
  { key: 'role', label: '角色管理' },
  { key: 'perm', label: '权限清单' }
]

function switchTab(key) {
  tab.value = key
  router.replace(`/rbac/${key}`)
}
watch(() => route.params.tab, v => { tab.value = v || 'user' })
onMounted(() => { if (!route.params.tab) tab.value = 'user' })
</script>

<template>
  <div>
    <div class="panel">
      <div class="panel-head"><div><h2>用户与权限</h2><p>用户、角色和数据范围</p></div></div>
      <div class="row">
        <button v-for="t in tabs" :key="t.key" class="sm" :class="{ primary: tab === t.key }" @click="switchTab(t.key)">{{ t.label }}</button>
      </div>
    </div>
    <UserPanel v-if="tab === 'user'" />
    <RolePanel v-else-if="tab === 'role'" />
    <PermissionPanel v-else />
  </div>
</template>
