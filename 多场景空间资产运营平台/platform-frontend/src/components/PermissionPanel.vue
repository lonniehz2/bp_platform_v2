<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const menus = ref([])
const error = ref('')
const search = ref('')
const rows = computed(() => {
  const out = []
  const q = search.value.trim().toLowerCase()
  const walk = (list, depth = 0) => {
    for (const m of list) {
      if (m.menuType !== 'GROUP') out.push({ ...m, depth })
      if (m.children?.length) walk(m.children, depth + 1)
    }
  }
  walk(menus.value)
  if (!q) return out
  return out.filter(m => (String(m.menuName) + ' ' + String(m.menuCode) + ' ' + String(m.route || '')).toLowerCase().includes(q))
})

onMounted(async () => {
  try { menus.value = await api.menus('GUARANTEE') } catch (e) { error.value = e.message }
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>权限清单</h2><p>页面级权限，只读</p></div><span class="badge blue">{{ rows.length }} 项</span></div>
      <input v-model="search" placeholder="搜索权限名称/编码/路由" style="max-width:360px" />
    </div>
    <div class="panel">
      <div class="table-wrap">
        <table>
          <thead><tr><th>权限名称</th><th>编码</th><th>路由</th></tr></thead>
          <tbody>
            <tr v-for="m in rows" :key="m.menuCode">
              <td :style="{ paddingLeft: (12 + m.depth * 18) + 'px' }">{{ m.menuName }}</td>
              <td class="mono">{{ m.menuCode }}</td>
              <td class="mono small">{{ m.route || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
