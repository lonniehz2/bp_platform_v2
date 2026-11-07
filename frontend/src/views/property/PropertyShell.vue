<template>
  <div class="property-shell">
    <aside class="property-side">
      <div class="brand">
        <div class="brand-mark">{{ t('property.brandMark') }}</div>
        <div>
          <div class="brand-name">{{ t('property.title') }}</div>
          <div class="brand-sub">{{ t('property.subtitle') }}</div>
        </div>
      </div>

      <el-menu :default-active="route.path" router class="property-menu">
        <el-menu-item index="/property/dashboard">
          <el-icon><DataBoard /></el-icon>
          <span>{{ t('property.dashboard') }}</span>
        </el-menu-item>
        <el-menu-item index="/property/projects">
          <el-icon><OfficeBuilding /></el-icon>
          <span>{{ t('property.projects') }}</span>
        </el-menu-item>
        <el-menu-item index="/property/categories">
          <el-icon><Collection /></el-icon>
          <span>{{ t('property.categories') }}</span>
        </el-menu-item>
      </el-menu>

      <div class="side-foot">{{ t('property.phaseHint') }}</div>
    </aside>

    <section class="property-main">
      <header class="property-head">
        <div>
          <div class="head-title">{{ pageTitle }}</div>
          <div class="head-sub">
            {{ t('property.currentProject') }}：
            <el-select v-model="selectedProject" size="small" style="width:210px"
                       :placeholder="t('property.selectProject')" @change="onProjectChange">
              <el-option v-for="p in store.projects" :key="p.orgId"
                         :label="p.projectName" :value="String(p.orgId)" />
            </el-select>
          </div>
        </div>
        <div class="head-actions">
          <el-tag size="small" type="warning">{{ t('property.phaseTag') }}</el-tag>
          <span class="user">{{ auth.user?.realName || auth.user?.username || '-' }}</span>
          <el-button link type="primary" @click="goHousing">{{ t('property.backHousing') }}</el-button>
        </div>
      </header>
      <main class="property-body">
        <router-view />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { DataBoard, Collection, OfficeBuilding } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { usePropertyStore } from '@/store/property'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = usePropertyStore()
const { t } = useI18n()
const selectedProject = computed({
  get: () => store.projectId,
  set: (v) => store.selectProject(v)
})

const pageTitle = computed(() => {
  if (route.path.includes('categories')) return t('property.categories')
  if (route.path.includes('projects')) return t('property.projects')
  return t('property.dashboard')
})

onMounted(async () => {
  await store.loadProjects()
})

function onProjectChange() {}

function goHousing() {
  router.push('/dashboard')
}
</script>

<style scoped>
.property-shell { min-height: 100vh; display: flex; background: #f3f6fb; }
.property-side { width: 232px; flex: 0 0 232px; background: #0f2747; color: #dbe9ff; display: flex; flex-direction: column; }
.brand { display: flex; gap: 10px; align-items: center; padding: 18px 16px; border-bottom: 1px solid rgba(255,255,255,.08); }
.brand-mark { width: 34px; height: 34px; border-radius: 8px; display: grid; place-items: center; background: linear-gradient(135deg,#2f7cf6,#55b0ff); font-weight: 700; }
.brand-name { font-size: 16px; font-weight: 600; }
.brand-sub { font-size: 11px; color: #8fb8e8; margin-top: 2px; }
.property-menu { border-right: 0; background: transparent; padding: 10px 8px; }
.property-menu :deep(.el-menu-item) { color: #cfe2ff; border-radius: 6px; margin-bottom: 4px; }
.property-menu :deep(.el-menu-item:hover) { background: rgba(64,158,255,.14); }
.property-menu :deep(.el-menu-item.is-active) { background: #1d4f8f; color: #fff; }
.side-foot { margin-top: auto; padding: 14px 16px; font-size: 11px; color: #7aa2d6; }
.property-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.property-head { height: 68px; background: #fff; border-bottom: 1px solid #e6edf7; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; }
.head-title { font-size: 17px; font-weight: 600; color: #1f2d3d; }
.head-sub { font-size: 12px; color: #8492a6; margin-top: 3px; }
.head-actions { display: flex; align-items: center; gap: 12px; }
.user { font-size: 13px; color: #475569; }
.property-body { padding: 18px; flex: 1; }
</style>
