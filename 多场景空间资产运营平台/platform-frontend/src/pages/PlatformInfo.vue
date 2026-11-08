<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const projects = ref([])
const persons = ref([])
const contracts = ref([])
const error = ref('')
const origin = window.location.origin
const user = (() => { try { return JSON.parse(localStorage.getItem('platformUser') || '{}') } catch { return {} } })()

onMounted(async () => {
  try {
    projects.value = await api.projects()
    persons.value = await api.persons()
    const p = projects.value[0]
    if (p) contracts.value = await api.contracts(p.id)
  } catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>平台信息</h2><p>当前登录、租户、部署和业务规模</p></div><span class="badge blue">v0.1.0</span></div>
      <div class="grid cards">
        <div class="card"><div class="label">当前用户</div><div class="value" style="font-size:18px">{{ user.displayName || user.username || '-' }}</div><div class="hint">{{ user.username }}</div></div>
        <div class="card"><div class="label">租户</div><div class="value" style="font-size:18px">{{ user.tenantId || '350600' }}</div><div class="hint">平台租户编码</div></div>
        <div class="card"><div class="label">项目</div><div class="value">{{ projects.length }}</div><div class="hint">全部项目</div></div>
        <div class="card"><div class="label">人员</div><div class="value">{{ persons.length }}</div><div class="hint">人员档案</div></div>
        <div class="card"><div class="label">合同</div><div class="value">{{ contracts.length }}</div><div class="hint">当前项目</div></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="panel">
        <div class="panel-head"><h2>部署</h2></div>
        <div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="muted">访问地址</span><span class="mono">{{ origin }}</span></div>
        <div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="muted">前端</span><span>Vue 3 + Vite</span></div>
        <div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="muted">后端</span><span>Spring Boot 3 / Java 17</span></div>
        <div class="row" style="padding:7px 0"><span class="muted">数据库</span><span>MySQL · bp_platform_v2</span></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>相关入口</h2></div>
        <div class="row">
          <RouterLink class="badge blue" to="/help">使用帮助</RouterLink>
          <RouterLink class="badge blue" to="/users">用户管理</RouterLink>
          <RouterLink class="badge blue" to="/menus">菜单与角色</RouterLink>
          <RouterLink class="badge blue" to="/migration-exceptions">迁移异常</RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
