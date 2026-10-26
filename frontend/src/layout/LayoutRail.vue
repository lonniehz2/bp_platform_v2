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
        <el-menu-item v-for="m in activeItems" :key="m.path" :index="m.path">
          <span>{{ m.meta.title }}</span>
          <el-badge v-if="m.path === '/todos' && todo.total > 0" :value="todo.total"
                    :max="99" style="margin-left:8px" />
        </el-menu-item>
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
        <el-tag size="small" type="info">租户 {{ auth.user?.tenantId || '—' }}</el-tag>
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
import { QuestionFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { groups, titleOf } = useMenu()
const todo = useTodoStore()

const activeGroup = ref(groups.value[0]?.name || '')
const activeItems = computed(() =>
  groups.value.find((g) => g.name === activeGroup.value)?.items
  || groups.value[0]?.items || [])

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
  router.push('/help')
}

async function logout() {
  await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100%; }
.rail {
  width: 76px; flex: 0 0 76px; background: #fff;
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
.rail-item:hover { background: #f5f5f5; }
.rail-item.active { background: #e6f7ff; color: #1890ff; }
.rail-bottom { margin-top: auto; }

.panel {
  width: 168px; flex: 0 0 168px; background: #fff;
  border-right: 1px solid #f0f0f0; padding: 8px 0; overflow: hidden;
}
.panel-title { padding: 6px 16px 10px; font-size: 13px; color: rgba(0, 0, 0, 0.45); }
.panel-menu { border-right: none; }
.panel-menu :deep(.el-menu-item) {
  height: 38px; line-height: 38px; font-size: 14px;
  margin: 0 8px; border-radius: 6px;
}
.panel-menu :deep(.el-menu-item.is-active) {
  background: #e6f7ff; color: #1890ff; font-weight: 500;
}

.right { min-width: 0; }
.header {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border-bottom: 1px solid #f0f0f0;
  height: 56px; padding: 0 16px;
}
.greet { font-size: 15px; color: rgba(0, 0, 0, 0.85); font-weight: 500; }
.crumb { font-size: 13px; }
.header .spacer { flex: 1; }
.main { background: #f0f2f5; padding: 16px; overflow-y: auto; }
</style>
