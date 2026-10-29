<template>
  <el-container class="layout">
    <div class="rail">
      <div class="rail-logo">保</div>
      <div v-for="g in groups" :key="g.name"
           :class="['rail-item', { active: activeGroup === g.name }]"
           @click="pickGroup(g.name)">
        <el-icon :size="20"><component :is="g.icon" /></el-icon>
        <span>{{ g.name }}</span>
      </div>
      <div class="rail-bottom">
        <el-tooltip content="全屏大屏" placement="right">
          <div class="rail-item" @click="openScreen">
            <el-icon :size="18"><Monitor /></el-icon>
          </div>
        </el-tooltip>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">{{ activeGroup }}</div>
      <el-menu :default-active="$route.path" router class="panel-menu">
        <template v-for="sec in activeSections" :key="sec.title || 'all'">
          <div v-if="sec.title" class="sub-group">{{ sec.title }}</div>
          <el-menu-item v-for="m in sec.items" :key="m.path" :index="m.path"
                        :disabled="m.disabled">
            <el-tooltip :content="m.disabled ? '未授权：请联系管理员' : (m.desc || m.meta.title)"
                        placement="right" :show-after="400">
              <span class="mi-label">
                {{ m.meta.title }}
                <el-icon v-if="m.disabled" class="lock"><Lock /></el-icon>
              </span>
            </el-tooltip>
            <el-badge v-if="badgeOf(m) > 0" :value="badgeOf(m)" :max="99"
                      class="mi-badge" />
          </el-menu-item>
        </template>
      </el-menu>
    </div>

    <el-container class="right">
      <el-header class="header">
        <span class="greet">Hi {{ auth.displayName || '管理员' }}，你好~</span>
        <el-breadcrumb separator="/" class="crumb">
          <el-breadcrumb-item>{{ activeGroup }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ titleOf($route.path) }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="spacer" />
        <el-tooltip placement="bottom"
                    :content="'平台编码：' + (auth.user?.tenantId || '—') + ' ｜ 组织：' + (auth.user?.orgName || '平台')">
          <el-tag size="small" type="info">
            {{ auth.user?.tenantName || '平台' }} · {{ auth.user?.orgName || '平台' }}
          </el-tag>
        </el-tooltip>
        <el-tooltip content="使用帮助" placement="bottom">
          <el-button text @click="toHelp">
            <el-icon><QuestionFilled /></el-icon>
          </el-button>
        </el-tooltip>
        <StyleSwitch />
        <el-button text @click="logout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { useMenu } from './useMenu'
import { useTodoStore } from '@/store/todo'
import StyleSwitch from './StyleSwitch.vue'
import { sectionForRoute } from '@/content/help'
import { QuestionFilled, Lock } from '@element-plus/icons-vue'
import { useMenuBadges } from './useMenuBadges'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { groups, titleOf } = useMenu()
const todo = useTodoStore()

const activeGroup = ref(groups.value[0]?.name || '')
const activeSections = computed(() => {
  const g = groups.value.find((x) => x.name === activeGroup.value) || groups.value[0]
  return g?.sections || []
})

// 角标：待办/逾期账单/待执行催缴/待处理告警/待派单
const { countOf: badgeCount } = useMenuBadges()
function badgeOf(m) {
  const key = m.badgeKey
  if (!key) return 0
  return badgeCount(key)
}

function pickGroup(name) {
  activeGroup.value = name
  const g = groups.value.find((x) => x.name === name)
  if (g && !g.items.some((m) => m.path === route.path)) {
    router.push(g.items[0].path)
  }
}

watch(() => route.path, () => {
  const hit = groups.value.find((g) => g.items.some((m) => m.path === route.path))
  if (hit) {
    activeGroup.value = hit.name
  } else if (!groups.value.some((g) => g.name === activeGroup.value)) {
    // 渲染时权限可能尚未就绪：回退到第一个分组，避免左侧面板空白
    activeGroup.value = groups.value[0]?.name || ''
  }
}, { immediate: true })

// 权限加载完成后菜单可能从空变有，这里补一次校正
watch(() => groups.value.length, () => {
  if (!groups.value.some((g) => g.name === activeGroup.value)) {
    activeGroup.value = groups.value[0]?.name || ''
  }
})

function openScreen() {
  window.open('./view-screen.html', 'bp-screen', 'width=1600,height=900')
}

function toHelp() {
  // 带当前页对应的帮助章节，省去用户在大纲里找
  router.push({ path: '/help', query: { sec: sectionForRoute(route.path) } })
}

async function logout() {
  await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.sub-group {
  margin: 10px 0 4px;
  padding: 0 18px;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  letter-spacing: 0.5px;
}
.mi-label { display: inline-flex; align-items: center; gap: 4px; }
.mi-label .lock { font-size: 12px; color: var(--el-text-color-secondary); }
.mi-badge { margin-left: auto; }

.layout { height: 100%; }
.rail {
  width: 76px; flex: 0 0 76px; background: var(--bp-sider-bg);
  border-right: 1px solid #f0f0f0;
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 0; gap: 2px;
}
.rail-logo {
  width: 36px; height: 36px; border-radius: 8px; background: #1890ff;
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-weight: 600; margin-bottom: 10px;
}
.rail-item {
  width: 64px; padding: 8px 0 6px; border-radius: 8px;
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  cursor: pointer; color: rgba(0, 0, 0, 0.65); font-size: 12px;
  transition: background 0.15s, color 0.15s;
}
.rail-item:hover { background: var(--bp-hover-bg); }
.rail-item.active { background: var(--bp-sider-active-bg); color: var(--el-color-primary); }
.rail-bottom { margin-top: auto; }

.panel {
  width: 168px; flex: 0 0 168px; background: var(--bp-sider-bg);
  border-right: 1px solid #f0f0f0; padding: 8px 0; overflow: hidden;
}
.panel-title { padding: 6px 16px 10px; font-size: 13px; color: rgba(0, 0, 0, 0.45); }
.panel-menu { border-right: none; }
.panel-menu :deep(.el-menu-item) {
  height: 38px; line-height: 38px; font-size: 14px;
  margin: 0 8px; border-radius: 6px;
}
.panel-menu :deep(.el-menu-item.is-active) {
  background: var(--bp-sider-active-bg); color: var(--el-color-primary); font-weight: 500;
}

.right { min-width: 0; }
.header {
  display: flex; align-items: center; gap: 12px;
  background: var(--bp-sider-bg); border-bottom: 1px solid var(--el-border-color-light);
  height: 56px; padding: 0 16px;
}
.greet { font-size: 15px; color: rgba(0, 0, 0, 0.85); font-weight: 500; }
.crumb { font-size: 13px; }
.header .spacer { flex: 1; }
.main { background: var(--bp-page-bg); padding: 16px; overflow-y: auto; }
</style>
