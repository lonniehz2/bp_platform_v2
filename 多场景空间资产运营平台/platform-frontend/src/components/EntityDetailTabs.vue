<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const props = defineProps({ type: { type: String, required: true }, entityId: { type: [String, Number], required: true } })
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
const statusLabels = { ACTIVE:'生效中', INACTIVE:'停用', ENABLED:'启用', DISABLED:'停用', DRAFT:'草稿', APPROVING:'审批中', TERMINATED:'已终止', DISCARDED:'已作废', WITHDRAWN:'已撤回', EXPIRED:'已到期', PAID:'已支付', UNPAID:'未支付', PARTIAL:'部分支付', WAIVED:'已减免', CLOSED:'已关闭', VACANT:'空置', RENTED:'已出租', OCCUPIED:'已入住', ALLOCATED:'已配租', IN_USE:'使用中', CONTRACTED:'已签约', INSTALLED:'已安装', PENDING_INSTALL:'待安装', PENDING:'待处理', PROCESSING:'处理中', DONE:'已完成', OPEN:'待处理', RESOLVED:'已解决', SUCCESS:'成功', FAILED:'失败', LOCKED:'无权限' }
const moneyKeys = new Set(['amount','payableAmount','paidAmount','refundedAmount','subsidyAmount'])
const dateKeys = new Set(['startDate','endDate','periodStart','periodEnd','validStart','validEnd','paidTime','createTime','effectiveDate'])
function statusLabel(v) { return statusLabels[String(v || '').toUpperCase()] || v || '-' }
function formatValue(item, col) {
  const v = item?.[col.key]
  if (v === null || v === undefined || v === '') return '-'
  if (col.key === 'status' || col.key.endsWith('Status')) return statusLabel(v)
  if (col.key === 'personType') return ({ GUARANTEE_TENANT:'保障对象', COHABITANT:'同住人', FAMILY:'家庭成员' }[String(v)] || v)
  if (moneyKeys.has(col.key)) return '¥' + Number(v).toFixed(2)
  if (dateKeys.has(col.key)) return String(v).replace('T', ' ').slice(0, 19)
  if (col.key === 'fileSize') return Number(v) >= 1024 ? (Number(v) / 1024).toFixed(1) + ' KB' : v + ' B'
  return v
}
const columns = computed(() => current.value?.columns?.length ? current.value.columns : [{ key: 'title', label: '名称' }, { key: 'subtitle', label: '说明' }, { key: 'status', label: '状态' }])
const overviewLabels = { title: '名称', subtitle: '编码', personName: '姓名', personCode: '人员编码', phone: '电话', personType: '人员类型', status: '状态', contractNo: '合同号', contractStatus: '合同状态', startDate: '开始日期', endDate: '结束日期', houseName: '房屋', houseCode: '房源编码', rentAmount: '租金', depositAmount: '押金' }
function overviewEntries(item) { return Object.entries(item || {}).filter(([k, v]) => v !== null && v !== '' && !['id','type','route'].includes(k)).map(([k, v]) => [overviewLabels[k] || k, v]) }

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
    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <template v-else>
      <div v-if="entity" class="entity-detail-head">
        <div><strong>{{ entity.title }}</strong><span v-if="entity.subtitle" class="small muted"> · {{ entity.subtitle }}</span></div>
        <span class="badge">{{ entity.type }}</span>
      </div>
      <div class="tab-strip">
        <button v-for="s in sections" :key="s.key" class="tab-btn" :class="{ active: s.key === active }" @click="selectTab(s.key)">
          {{ s.label }}<span v-if="s.items?.length" class="tab-count">{{ s.items.length }}</span>
        </button>
      </div>
      <div v-if="current" class="tab-panel">
        <div v-if="!current.accessible" class="empty">🔒 {{ current.reason || '无权限查看该关联信息' }}</div>
        <div v-else-if="!current.items?.length" class="empty">暂无关联记录</div>
        <div v-else-if="current.key === 'overview'" class="kv-grid">
          <div v-for="([label, value], i) in overviewEntries(current.items[0])" :key="i"><span>{{ label }}</span><strong>{{ formatValue({ value }, { key: 'value' }) === '-' ? value : value }}</strong></div>
        </div>
        <div v-else class="table-wrap">
          <table>
            <thead><tr><th v-for="col in columns" :key="col.key">{{ col.label }}</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="(item, i) in current.items" :key="i">
                <td v-for="col in columns" :key="col.key">{{ formatValue(item, col) }}</td>
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
