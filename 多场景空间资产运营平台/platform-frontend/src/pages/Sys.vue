<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const projects = ref([])
const users = ref([])
const roles = ref([])
const auditLogs = ref([])
const error = ref('')

onMounted(async () => {
  try {
    projects.value = await api.projects()
    users.value = await api.users()
    roles.value = await api.roles('GUARANTEE')
    auditLogs.value = await api.auditLogs(20).catch(() => [])
  } catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>系统支撑</h2><p>平台基础配置、权限、开放和运维入口</p></div><span class="badge blue">SYSTEM</span></div>
      <div class="grid cards">
        <div class="card"><div class="label">项目</div><div class="value">{{ projects.length }}</div><div class="hint">组织/项目</div></div>
        <div class="card"><div class="label">用户</div><div class="value">{{ users.length }}</div><div class="hint">平台账号</div></div>
        <div class="card"><div class="label">角色</div><div class="value">{{ roles.length }}</div><div class="hint">场景角色</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>操作审计</h2><span class="small muted">最近 20 条写操作</span></div>
      <div v-if="!auditLogs.length" class="empty">暂无审计日志</div>
      <div class="table-wrap" v-else>
        <table><thead><tr><th>时间</th><th>用户</th><th>方法</th><th>路径</th><th>状态</th><th>IP</th></tr></thead>
          <tbody><tr v-for="l in auditLogs" :key="l.id">
            <td class="small">{{ l.createTime }}</td><td>{{ l.username }}</td><td class="mono">{{ l.method }}</td>
            <td class="mono small">{{ l.path }}</td><td>{{ l.statusCode }}</td><td class="small">{{ l.ip }}</td>
          </tr></tbody>
        </table>
      </div>
    </div>

    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">
      <div class="panel"><div class="panel-head"><h2>用户与权限</h2></div><div class="row"><RouterLink class="badge blue" to="/users">用户管理</RouterLink><RouterLink class="badge blue" to="/menus">菜单与角色</RouterLink></div></div>
      <div class="panel"><div class="panel-head"><h2>开放与数据</h2></div><div class="row"><RouterLink class="badge blue" to="/open-apps">开放平台</RouterLink><RouterLink class="badge blue" to="/migration-exceptions">迁移异常</RouterLink></div></div>
      <div class="panel"><div class="panel-head"><h2>运行信息</h2></div><div class="row"><RouterLink class="badge blue" to="/platform-info">平台信息</RouterLink><RouterLink class="badge blue" to="/help">使用帮助</RouterLink></div></div>
      <div class="panel"><div class="panel-head"><h2>业务数据</h2></div><div class="row"><RouterLink class="badge blue" to="/translations">业务数据翻译</RouterLink><RouterLink class="badge blue" to="/reports">报表导出</RouterLink></div></div>
    </div>
  </div>
</template>
