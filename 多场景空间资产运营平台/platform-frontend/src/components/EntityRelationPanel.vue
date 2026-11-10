<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const props = defineProps({ type: { type: String, required: true }, entityId: { type: [String, Number], default: '' } })
const router = useRouter()
const links = ref([])
const loading = ref(false)
const error = ref('')

async function load() {
  if (!props.entityId) { links.value = []; return }
  loading.value = true; error.value = ''
  try {
    const data = await api.entityRelations(props.type, props.entityId)
    links.value = data.links || []
  } catch (e) { error.value = e.message; links.value = [] } finally { loading.value = false }
}

function open(link) {
  if (!link.accessible || !link.route) return
  router.push(link.route)
}
onMounted(load)
watch(() => [props.type, props.entityId], load)
</script>

<template>
  <div class="panel">
    <div class="panel-head"><div><h2>关联信息</h2><p>人员、房源、账单、押金</p></div></div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-else-if="loading" class="empty">加载中…</div>
    <div v-else-if="!links.length" class="empty">暂无关联信息</div>
    <div v-else class="relation-grid">
      <button v-for="l in links" :key="l.type + '-' + (l.id || '')" class="relation-card" :class="{ locked: !l.accessible }" :disabled="!l.accessible" @click="open(l)">
        <div class="relation-kind">{{ l.label }}</div>
        <div class="relation-title">{{ l.title }}</div>
        <div v-if="l.reason" class="relation-reason">{{ l.reason }}</div>
        <div v-else class="relation-go">查看 →</div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.relation-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }
.relation-card { text-align:left; padding:12px; border:1px solid var(--line); border-radius:8px; background:var(--bg); cursor:pointer; display:flex; flex-direction:column; gap:6px; }
.relation-card:hover:not(:disabled) { border-color:var(--brand); background:var(--brand-soft); }
.relation-card.locked { opacity:.65; cursor:not-allowed; }
.relation-kind { font-size:11px; color:var(--muted); }
.relation-title { font-weight:600; font-size:14px; }
.relation-reason { font-size:11px; color:var(--muted); }
.relation-go { font-size:11px; color:var(--brand); }
</style>
