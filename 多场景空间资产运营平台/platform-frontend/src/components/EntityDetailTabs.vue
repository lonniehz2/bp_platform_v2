<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({ type: { type: String, required: true }, entityId: { type: [String, Number], required: true } })
const loading = ref(false)
const error = ref('')
const entity = ref(null)
const sections = ref([])
const active = ref('')

async function load() {
  loading.value = true; error.value = ''; sections.value = []; entity.value = null; active.value = ''
  try {
    const data = await api.entitySections(props.type, props.entityId)
    entity.value = data.entity || null
    sections.value = data.sections || []
    active.value = sections.value[0]?.key || ''
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

const current = computed(() => sections.value.find(s => s.key === active.value) || sections.value[0] || null)
watch(() => [props.type, props.entityId], load, { immediate: true })
</script>

<template>
  <div class="entity-detail-tabs">
    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-if="entity" class="entity-detail-head">
        <div><strong>{{ entity.title }}</strong><span v-if="entity.subtitle" class="small muted"> · {{ entity.subtitle }}</span></div>
        <span class="badge">{{ entity.type }}</span>
      </div>
      <div class="tab-strip">
        <button v-for="s in sections" :key="s.key" class="tab-btn" :class="{ active: s.key === active }" @click="active = s.key">
          {{ s.label }}<span v-if="s.items?.length" class="tab-count">{{ s.items.length }}</span>
        </button>
      </div>
      <div v-if="current" class="tab-panel">
        <div v-if="!current.accessible" class="empty">🔒 {{ current.reason || '无权限查看该关联信息' }}</div>
        <div v-else-if="!current.items?.length" class="empty">暂无关联记录</div>
        <div v-else class="table-wrap">
          <table>
            <thead><tr><th>名称</th><th>类型</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="(item, i) in current.items" :key="i">
                <td><strong>{{ item.title || '-' }}</strong><div v-if="item.subtitle" class="small muted">{{ item.subtitle }}</div></td>
                <td>{{ item.subtitle || '-' }}</td>
                <td><span class="badge" :class="item.status === 'LOCKED' ? 'orange' : 'green'">{{ item.status === 'LOCKED' ? '无权限' : '可查看' }}</span></td>
                <td><RouterLink v-if="item.route && item.status !== 'LOCKED'" :to="item.route">打开</RouterLink><span v-else class="small muted">-</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.entity-detail-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.tab-strip{display:flex;gap:6px;border-bottom:1px solid var(--line);margin-bottom:10px;overflow-x:auto}
.tab-btn{border:0;background:transparent;padding:9px 12px;border-bottom:2px solid transparent;cursor:pointer;color:var(--muted);white-space:nowrap}
.tab-btn.active{color:var(--brand);border-bottom-color:var(--brand);font-weight:600}
.tab-count{margin-left:5px;font-size:11px;background:var(--brand-soft);border-radius:8px;padding:1px 5px}
.tab-panel{min-height:80px}
</style>
