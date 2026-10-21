<template>
  <div class="h5-root">
    <router-view />
    <nav v-if="showTab" class="tabbar">
      <div v-for="t in tabs" :key="t.path" :class="['tab', { active: isActive(t.path) }]"
           @click="$router.push(t.path)">
        <el-icon :size="20"><component :is="t.icon" /></el-icon>
        <span>{{ t.label }}</span>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const tabs = [
  { path: '/h5/home', label: '首页', icon: 'HomeFilled' },
  { path: '/h5/bills', label: '账单', icon: 'Money' },
  { path: '/h5/applications', label: '申请', icon: 'Document' },
  { path: '/h5/profile', label: '我的', icon: 'User' }
]
const showTab = computed(() => !route.meta.hideTab)
function isActive(p) { return route.path.startsWith(p) }
</script>
