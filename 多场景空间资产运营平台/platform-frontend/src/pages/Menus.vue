<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const menus = ref([])
const roles = ref([])
const roleMenus = ref([])
const selectedRole = ref(null)
const error = ref('')

async function load() {
  try {
    const [m, r] = await Promise.all([api.menus('GUARANTEE'), api.roles('GUARANTEE')])
    menus.value = m
    roles.value = r
    if (r.length) await selectRole(r[0])
  } catch (e) { error.value = e.message }
}

async function selectRole(role) {
  selectedRole.value = role
  roleMenus.value = await api.roleMenus(role.id)
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid" style="grid-template-columns: 1.2fr .8fr">
      <div class="panel">
        <div class="panel-head"><div><h2>场景菜单</h2><p>GUARANTEE · 平台按场景组合菜单</p></div><span class="pill">{{ menus.length }} 个一级</span></div>
        <div v-if="!menus.length" class="empty">暂无菜单</div>
        <div v-for="m in menus" :key="m.menuCode" style="padding:9px 0;border-bottom:1px solid var(--line)">
          <div class="row">
            <strong>{{ m.menuName }}</strong>
            <span class="mono">{{ m.route }}</span>
          </div>
          <div v-if="m.children?.length" class="row" style="margin:6px 0 0 18px">
            <span v-for="c in m.children" :key="c.menuCode" class="badge blue">{{ c.menuName }}</span>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>角色模板</h2><span class="small muted">点击查看菜单</span></div>
        <div v-if="!roles.length" class="empty">暂无角色</div>
        <div v-for="r in roles" :key="r.id" class="row" style="padding:9px 0;border-bottom:1px solid var(--line);cursor:pointer" @click="selectRole(r)">
          <div style="flex:1">
            <div>{{ r.roleName }}</div>
            <div class="mono">{{ r.roleCode }}</div>
          </div>
          <span class="badge">{{ r.menuCount }} 菜单</span>
        </div>
        <div v-if="selectedRole" style="margin-top:14px">
          <div class="small muted">{{ selectedRole.roleName }} 菜单</div>
          <div class="row" style="margin-top:8px">
            <span v-for="m in roleMenus" :key="m.menuCode" class="badge blue">{{ m.menuName }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
