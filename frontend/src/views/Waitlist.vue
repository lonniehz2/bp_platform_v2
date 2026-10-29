<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">轮候管理</h3>
      <el-tag size="small" type="info">总分 = 优先附加分 + 轮候天数 × 0.1</el-tag>
      <div class="spacer" />
      <el-select v-model="orgId" placeholder="组织名称" clearable filterable
                 style="width:200px" data-testid="wait-org" @change="reload">
        <el-option v-for="o in orgs" :key="o.id" :label="o.orgName" :value="o.id" />
      </el-select>
      <el-input v-model="keyword" placeholder="姓名/手机号" clearable style="width:170px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openEnqueue">入队登记</el-button>
      <el-button @click="recalc">重算总分</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="摇号按总分降序、入队时间升序取前 N 名；优先附加分用于优抚对象加分"
              style="margin-bottom:12px" />

    <el-table empty-text="轮候库为空，审核通过后会自动入队" :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="personIdName" label="轮候人" width="200">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column label="组织" width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ row.orgIdName || '—' }}</template>
      </el-table-column>
      <el-table-column prop="priorityScore" label="优先分" width="100" />
      <el-table-column prop="liveWaitDays" label="已轮候天数" width="110" />
      <el-table-column prop="totalScore" label="总分" width="100">
        <template #default="{ row }">
          <strong>{{ row.totalScore }}</strong>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="row.queueStatus === 'WAITING' ? 'success'
            : (row.queueStatus === 'EXITED' ? 'info' : 'warning')">
            {{ row.queueStatusLabel || enumLabel('queueStatus', row.queueStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="enterTime" label="入队时间" width="170" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" @click="doExit(row)">候补退出</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />

    <el-dialog v-model="enqueueVisible" title="轮候入队" width="560px">
      <el-form :model="ef" label-width="130px">
        <el-form-item label="人员ID" required>
          <PersonPicker v-model="ef.personId" width="240px" testid="person-picker" /></el-form-item>
        <el-form-item label="申请单ID">
          <el-input v-model="ef.applicationId"
                    placeholder="已通过的申请单，可为空" /></el-form-item>
        <el-form-item label="组织ID" required>
          <OrgSelect v-model="ef.orgId" width="100%" /></el-form-item>
        <el-form-item label="保障类型" required>
          <el-select v-model="ef.securityType" style="width:100%">
            <el-option label="公租房" value="PUBLIC" />
            <el-option label="保租房" value="AFFORDABLE" />
            <el-option label="人才房" value="TALENT" />
            <el-option label="廉租房" value="LOW_RENT" />
          </el-select></el-form-item>
        <el-form-item label="优先附加分">
          <el-input-number v-model="ef.priorityScore" :min="0" :precision="1"
                           style="width:100%" />
        </el-form-item>
        <el-form-item label="优先原因">
          <el-input v-model="ef.priorityReason"
                    placeholder="如 退役军人 / 残疾人 / 计生特殊家庭" /></el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="入队后系统按「优先分 + 轮候天数×0.1」计算总分，摇号时实时排序" />
      <template #footer>
        <el-button @click="enqueueVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doEnqueue">确认入队</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="轮候详情" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import OrgSelect from '@/components/OrgSelect.vue'
import { enumLabel } from '@/constants/enums'
import DetailView from '@/components/DetailView.vue'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const keyword = ref('')
const orgId = ref(null)
const orgs = ref([])

async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    orgs.value = d.rows || d || []
  } catch (e) { orgs.value = [] }
}
const show = ref(false)
const detail = ref(null)
const enqueueVisible = ref(false)
const query = reactive({ pageNum: 1, pageSize: 20 })
const ef = reactive({ personId: null, applicationId: null, orgId: null,
  securityType: 'PUBLIC', priorityScore: 0, priorityReason: '' })

async function load() {
  loading.value = true
  try {
    const d = await req.get('/allocation/waiting', {
      // 轮候接口暂不支持关键字（需关联人员表），先不传，避免「输入了却不生效」
      params: { ...query, keyword: keyword.value || undefined,
        orgId: orgId.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { query.pageNum = 1; load() }

function openEnqueue() {
  Object.assign(ef, { personId: null, applicationId: null, orgId: null,
    securityType: 'PUBLIC', priorityScore: 0, priorityReason: '' })
  enqueueVisible.value = true
}

/** 选择人员后自动带出已通过的申请单与组织，避免手填 ID */
watch(() => ef.personId, async (v) => {
  if (!v) return
  try {
    const d = await req.get('/applications',
      { params: { personId: v, status: 'APPROVED', pageNum: 1, pageSize: 5 } })
    const app = (d.rows || [])[0]
    if (app) {
      ef.applicationId = app.id
      ef.orgId = app.orgId || ef.orgId
      ef.securityType = app.securityType || ef.securityType
      ElMessage.success('已带入申请单与组织')
    } else {
      ElMessage.warning('该人员暂无「已通过」的申请单，请先完成申请审核')
    }
  } catch (e) { /* 忽略，用户可手填 */ }
})

async function doEnqueue() {
  if (!ef.personId) { ElMessage.warning('请选择人员'); return }
  if (!ef.applicationId) { ElMessage.warning('请先带入已通过的申请单'); return }
  if (!ef.orgId) { ElMessage.warning('组织为必填'); return }
  saving.value = true
  try {
    await req.post('/allocation/waiting', { ...ef })
    ElMessage.success('已入队')
    enqueueVisible.value = false; reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || '入队失败')
  } finally { saving.value = false }
}

async function recalc() {
  const r = await req.post('/allocation/waiting/recalc', null,
    { params: { orgId: ef.orgId || undefined } })
  ElMessage.success('重算完成：更新 ' + (r?.count ?? r ?? '全部') + ' 条')
  load()
}

function resetQuery() {
  orgId.value = null
  keyword.value = ''
  reload()
}

onMounted(() => { load(); loadOrgs() })
/** 候补退出：放弃轮候资格，需填原因 */
async function doExit(row) {
  const { value } = await ElMessageBox.prompt('退出原因（如已购商品房/迁出本市）', '候补退出',
    { inputValidator: (v) => (v && v.trim() ? true : '请填写退出原因') })
  await ElMessageBox.confirm('确认该候补家庭退出轮候？退出后需重新申请。', '确认',
    { type: 'warning' })
  await req.post(`/allocation/waiting/${row.id}/exit`, { reason: value })
  ElMessage.success('已退出轮候'); load()
}
</script>
