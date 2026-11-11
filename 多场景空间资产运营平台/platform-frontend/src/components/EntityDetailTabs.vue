<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { enumLabel } from '../enumLabels'
import { api } from '../api'

const props = defineProps({ type: { type: String, required: true }, entityId: { type: [String, Number], required: true } })
const { t, te } = useI18n()
const route = useRoute()
const router = useRouter()
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
    const wanted = String(route.query.tab || '')
    active.value = sections.value.some(s => s.key === wanted) ? wanted : (sections.value[0]?.key || '')
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

const current = computed(() => sections.value.find(s => s.key === active.value) || sections.value[0] || null)
const statusLabels = {}
const moneyKeys = new Set(['amount','payableAmount','paidAmount','refundedAmount','subsidyAmount'])
const dateKeys = new Set(['startDate','endDate','periodStart','periodEnd','validStart','validEnd','paidTime','createTime','effectiveDate'])
function statusLabel(v) { const code = String(v || '').toUpperCase(); return te(`status.${code}`) ? t(`status.${code}`) : (statusLabels[code] || v || '-') }
function formatValue(item, col) {
  const v = item?.[col.key]
  if (v === null || v === undefined || v === '') return '-'
  if (col.key === 'status' || col.key.endsWith('Status')) return statusLabel(v)
  if (col.key === 'personType') return te(`personType.${v}`) ? t(`personType.${v}`) : v
  if (moneyKeys.has(col.key)) return '¥' + Number(v).toFixed(2)
  if (dateKeys.has(col.key)) return String(v).replace('T', ' ').slice(0, 19)
  if (col.key === 'fileSize') return Number(v) >= 1024 ? (Number(v) / 1024).toFixed(1) + ' KB' : v + ' B'
  return v
}
const columns = computed(() => current.value?.columns?.length ? current.value.columns : [{ key: 'title', label: 'Title' }, { key: 'subtitle', label: 'Detail' }, { key: 'status', label: 'Status' }])
const overviewLabels = {}
function formatOverviewValue(key, value) { if (value === null || value === undefined || value === '') return '-'; const code = String(value); if (te(`enum.${code}`)) return t(`enum.${code}`); if (['area','innerArea'].includes(key)) return Number(value).toFixed(2) + ' ' + t('units.sqm'); if (key === 'floorNo' || key === 'totalFloors') return value + ' ' + t('units.floor'); if (key.toLowerCase().includes('status')) return statusLabel(value); if (moneyKeys.has(key)) return '¥' + Number(value).toFixed(2); if (dateKeys.has(key) || key.toLowerCase().includes('time')) return String(value).replace('T', ' ').slice(0, 19); return value }
function overviewEntries(item) {
  const entries = Object.entries(item || {}).filter(([k, v]) => v !== null && v !== '' && !['id','type','route','title','subtitle'].includes(k))
  const hasSpecificStatus = entries.some(([k]) => k !== 'status' && k.toLowerCase().endsWith('status'))
  return entries.filter(([k]) => !(k === 'status' && hasSpecificStatus)).map(([k, v]) => ({ label: overviewLabels[k] || k, key: k, value: v }))
}

function selectTab(key) {
  active.value = key
  router.replace({ query: { ...route.query, tab: key } })
}

watch(() => route.query.tab, key => {
  if (key && sections.value.some(s => s.key === key)) active.value = String(key)
})
watch(() => [props.type, props.entityId], load, { immediate: true })
</script>

<template>
  <div class="entity-detail-tabs">
    <div v-if="loading" class="empty">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-if="entity" class="entity-detail-head">
        <div><strong>{{ entity.title }}</strong><span v-if="entity.subtitle" class="small muted"> · {{ entity.subtitle }}</span></div>
        <span class="badge">{{ enumLabel(entity.type) }}</span>
      </div>
      <div class="tab-strip">
        <button v-for="s in sections" :key="s.key" class="tab-btn" :class="{ active: s.key === active }" @click="selectTab(s.key)">
          {{ te(`section.${s.key}`) ? t(`section.${s.key}`) : s.label }}<span v-if="s.items?.length" class="tab-count">{{ s.items.length }}</span>
        </button>
      </div>
      <div v-if="current" class="tab-panel">
        <div v-if="!current.accessible" class="empty">🔒 {{ current.reason || t('common.noPermission') }}</div>
        <div v-else-if="!current.items?.length" class="empty">{{ t('common.noRelation') }}</div>
        <div v-else-if="current.key === 'overview'" class="kv-grid">
          <div v-for="(entry, i) in overviewEntries(current.items[0])" :key="i"><span>{{ te(`field.${entry.key}`) ? t(`field.${entry.key}`) : entry.label }}</span><strong>{{ formatOverviewValue(entry.key, entry.value) }}</strong></div>
        </div>
        <div v-else class="table-wrap">
          <table>
            <thead><tr><th v-for="col in columns" :key="col.key">{{ te(`field.${col.key}`) ? t(`field.${col.key}`) : col.label }}</th><th>{{ t('common.action') }}</th></tr></thead>
            <tbody>
              <tr v-for="(item, i) in current.items" :key="i">
                <td v-for="col in columns" :key="col.key">{{ formatValue(item, col) }}</td>
                <td><RouterLink v-if="item.route && item.status !== 'LOCKED'" :to="item.route">{{ t('common.open') }}</RouterLink><span v-else class="small muted">-</span></td>
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
.kv-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 14px;margin-top:8px}
.kv-grid>div{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;padding:10px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel-soft);min-width:0}
.kv-grid>div>span{color:var(--muted);font-size:12px;white-space:nowrap}
.kv-grid>div>strong{text-align:right;font-size:13px;font-weight:600;overflow-wrap:anywhere}
@media (max-width:700px){.kv-grid{grid-template-columns:1fr}}
</style>
