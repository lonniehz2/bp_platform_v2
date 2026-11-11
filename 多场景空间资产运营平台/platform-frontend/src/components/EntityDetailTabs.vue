<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
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
const statusLabels = { ACTIVE:'生效中', INACTIVE:'停用', ENABLED:'启用', DISABLED:'停用', DRAFT:'草稿', APPROVING:'审批中', TERMINATED:'已终止', DISCARDED:'已作废', WITHDRAWN:'已撤回', EXPIRED:'已到期', PAID:'已支付', UNPAID:'未支付', PARTIAL:'部分支付', WAIVED:'已减免', CLOSED:'已关闭', VACANT:'空置', RENTED:'已出租', OCCUPIED:'已入住', ALLOCATED:'已配租', IN_USE:'使用中', CONTRACTED:'已签约', INSTALLED:'已安装', PENDING_INSTALL:'待安装', PENDING:'待处理', PROCESSING:'处理中', DONE:'已完成', OPEN:'待处理', RESOLVED:'已解决', SUCCESS:'成功', FAILED:'失败', LOCKED:'无权限' }
const moneyKeys = new Set(['amount','payableAmount','paidAmount','refundedAmount','subsidyAmount'])
const dateKeys = new Set(['startDate','endDate','periodStart','periodEnd','validStart','validEnd','paidTime','createTime','effectiveDate'])
function statusLabel(v) { const code = String(v || '').toUpperCase(); return te(`status.${code}`) ? t(`status.${code}`) : (statusLabels[code] || v || '-') }
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
const overviewLabels = { title: '名称', subtitle: '编码', personName: '姓名', personCode: '人员编码', phone: '电话', personType: '人员类型', status: '状态', contractNo: '合同号', contractStatus: '合同状态', startDate: '开始日期', endDate: '结束日期', houseName: '房屋', houseCode: '房源编码', rentAmount: '租金', depositAmount: '押金', houseStatus: '房态', area: '建筑面积', innerArea: '套内面积', layoutType: '户型', orientation: '朝向', floorNo: '楼层', totalFloors: '总楼层', billNo: '账单号', periodStart: '账期起', periodEnd: '账期止', amount: '金额', discountAmount: '减免', payableAmount: '应付', paidAmount: '已收', billStatus: '账单状态', dueDate: '到期日', deviceCode: '设备编码', deviceName: '设备名称', deviceType: '设备类型', deviceModel: '型号', assetStatus: '资产状态', businessStatus: '业务状态', installTime: '安装时间', warrantyEnd: '保修截止', deviceMac: 'MAC', orderNo: '工单号', orderType: '工单类型', priority: '优先级', orderStatus: '工单状态', assigneeName: '处理人', createTime: '创建时间', finishTime: '完成时间', applicationNo: '申请编号', applicationType: '申请类型', familySize: '家庭人数', incomeLevel: '收入水平', housingStatus: '住房情况', guaranteeType: '保障类型', applicationStatus: '申请状态', submitTime: '提交时间', archiveNo: '档案编号', applicantName: '申请人' }
function formatOverviewValue(key, value) { if (value === null || value === undefined || value === '') return '-'; const codeLabels = { TWO_BED:'两室', ONE_BED:'一室', THREE_BED:'三室', SOUTH:'南', NORTH:'北', EAST:'东', WEST:'西', SOUTHEAST:'东南', SOUTHWEST:'西南', GUARANTEE_TENANT:'保障对象', COHABITANT:'同住人', PUBLIC_RENTAL:'公租房', AFFORDABLE_RENTAL:'保障性租赁住房', TALENT_APARTMENT:'人才公寓', DORMITORY:'宿舍', RENTAL:'出租房', HOTEL:'酒店民宿' }; if (codeLabels[String(value)]) return codeLabels[String(value)]; if (['area','innerArea'].includes(key)) return Number(value).toFixed(2) + ' ㎡'; if (key === 'floorNo') return value + ' 层'; if (key === 'totalFloors') return value + ' 层'; if (key.toLowerCase().includes('status')) return statusLabel(value); if (moneyKeys.has(key)) return '¥' + Number(value).toFixed(2); if (dateKeys.has(key) || key.toLowerCase().includes('time')) return String(value).replace('T', ' ').slice(0, 19); return value }
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
        <span class="badge">{{ entity.type }}</span>
      </div>
      <div class="tab-strip">
        <button v-for="s in sections" :key="s.key" class="tab-btn" :class="{ active: s.key === active }" @click="selectTab(s.key)">
          {{ s.label }}<span v-if="s.items?.length" class="tab-count">{{ s.items.length }}</span>
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
