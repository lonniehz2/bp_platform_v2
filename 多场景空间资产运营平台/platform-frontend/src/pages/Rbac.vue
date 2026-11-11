<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UserPanel from '../components/UserPanel.vue'
import RolePanel from '../components/RolePanel.vue'
import PermissionPanel from '../components/PermissionPanel.vue'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()
const router = useRouter()
const tab = ref(route.params.tab || 'user')
const tabs = [
  { key: 'user', label: t('rbac.user') },
  { key: 'role', label: t('rbac.role') },
  { key: 'perm', label: t('rbac.perm') }
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
      <div class="panel-head"><div><h2>{{ t('rbac.title') }}</h2><p>{{ t('rbac.subtitle') }}</p></div></div>
      <div class="row">
        <button v-for="t in tabs" :key="t.key" class="sm" :class="{ primary: tab === t.key }" @click="switchTab(t.key)">{{ t.label }}</button>
      </div>
    </div>
    <UserPanel v-if="tab === 'user'" />
    <RolePanel v-else-if="tab === 'role'" />
    <PermissionPanel v-else />
  </div>
</template>
