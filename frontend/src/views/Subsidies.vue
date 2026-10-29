<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">补贴管理</h3>
      <el-tag size="small" type="info">4 种方式 · 月度封顶 · 抵扣租金</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="batchVisible = true">批量发放</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="补贴：FIXED 定额 / BY_AREA 按面积 / BY_PERSON 按人 / RATIO 按租金比例；封顶与抵扣规则由标准配置"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small" empty-text="暂无数据，可调整筛选条件或点击右上角新建">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="recordNo" label="补贴单号" width="170" />
      <el-table-column prop="personId" label="人员" width="110">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="payMode" label="发放方式" width="110">
        <template #default="{ row }">{{ row.payModeLabel || enumLabel('payMode', row.payMode) }}</template>
      </el-table-column>
      <el-table-column prop="subsidyPeriod" label="周期" width="100" />
      <el-table-column label="补贴标准" width="170" show-overflow-tooltip>
        <template #default="{ row }">{{ row.standardIdName || row.standardId || '—' }}</template>
      </el-table-column>
      <el-table-column label="合同" width="160" show-overflow-tooltip>
        <template #default="{ row }">{{ row.contractIdName || row.contractId || '—' }}</template>
      </el-table-column>
      <el-table-column label="金额" width="100" >
          <template #default="{ row }">{{ $money(row.subsidyAmount) }}</template>
        </el-table-column>
      <el-table-column prop="recordStatus" label="状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.recordStatus === 'PAID' ? 'success'
            : (row.recordStatus === 'FAILED' ? 'danger' : 'warning')">
            {{ row.recordStatusLabel || enumLabel('recordStatus', row.recordStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" :disabled="row.recordStatus !== 'PENDING'"
                     @click="confirm(row)">确认发放</el-button>
          <el-button link type="danger" :disabled="row.recordStatus !== 'PENDING'"
                     @click="doFail(row)">发放失败</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />


    <!-- ==================== 补贴标准 ==================== -->
    <div class="page-card">
      <div class="toolbar">
        <h4 style="margin:0">补贴标准</h4>
        <el-tag size="small" type="info">按保障类型 + 补贴方式配置，停用后不再参与发放</el-tag>
        <div class="spacer" />
        <el-select v-model="stQuery.securityType" placeholder="保障类型" clearable
                   style="width:130px" @change="loadStandards">
          <el-option label="公租房" value="PUBLIC" />
          <el-option label="保障性租赁住房" value="AFFORDABLE" />
          <el-option label="人才公寓" value="TALENT" />
          <el-option label="廉租房" value="LOW_RENT" />
        </el-select>
        <el-select v-model="stQuery.subsidyMode" placeholder="补贴方式" clearable
                   style="width:140px" @change="loadStandards">
          <el-option label="定额" value="FIXED" />
          <el-option label="按面积" value="BY_AREA" />
          <el-option label="按人" value="BY_PERSON" />
          <el-option label="按租金比例" value="RATIO" />
        </el-select>
        <el-input v-model="stQuery.keyword" placeholder="编码/名称" clearable
                  style="width:160px" @keyup.enter="loadStandards" />
        <el-button type="primary" @click="loadStandards">查询</el-button>
        <el-button type="success" @click="openStandard">新建标准</el-button>
        <span class="muted">共 {{ stTotal }} 条</span>
      </div>

      <el-table :data="standards" v-loading="stLoading" border size="small">
        <el-table-column prop="standardCode" label="标准编码" width="150" />
        <el-table-column prop="standardName" label="名称" min-width="160" />
        <el-table-column prop="securityType" label="保障类型" width="150">
          <template #default="{ row }">{{ enumLabel('securityType', row.securityType) }}</template>
        </el-table-column>
        <el-table-column prop="subsidyMode" label="补贴方式" width="130">
          <template #default="{ row }">
            {{ row.subsidyModeLabel || enumLabel('subsidyMode', row.subsidyMode) }}
          </template>
        </el-table-column>
        <el-table-column prop="subsidyValue" label="补贴值" width="110" />
        <el-table-column prop="maxAmount" label="封顶金额" width="110" />
        <el-table-column label="有效期" min-width="200">
          <template #default="{ row }">
            {{ row.effectiveStart || '—' }} ~ {{ row.effectiveEnd || '长期' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
              {{ row.status === 'ENABLED' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="{ row }">
            <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                       @click="toggleStandard(row)">
              {{ row.status === 'ENABLED' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="+stTotal || 0" :page-size="stQuery.pageSize"
                     :current-page="stQuery.pageNum"
                     @current-change="(p) => { stQuery.pageNum = p; loadStandards() }" />
    </div>

    <!-- 新建补贴标准 -->
    <el-dialog v-model="standardVisible" title="新建补贴标准" width="580px">
      <el-form :model="sf" label-width="120px">
        <el-form-item label="标准编码" required>
          <el-input v-model="sf.standardCode" placeholder="如 SUB-PUBLIC-2026" />
        </el-form-item>
        <el-form-item label="标准名称" required>
          <el-input v-model="sf.standardName" />
        </el-form-item>
        <el-form-item label="保障类型" required>
          <el-select v-model="sf.securityType" style="width:100%">
            <el-option label="公租房" value="PUBLIC" />
            <el-option label="保障性租赁住房" value="AFFORDABLE" />
            <el-option label="人才公寓" value="TALENT" />
            <el-option label="廉租房" value="LOW_RENT" />
          </el-select>
        </el-form-item>
        <el-form-item label="补贴方式" required>
          <el-select v-model="sf.subsidyMode" style="width:100%">
            <el-option label="定额（元/月）" value="FIXED" />
            <el-option label="按面积（元/㎡·月）" value="BY_AREA" />
            <el-option label="按人（元/人·月）" value="BY_PERSON" />
            <el-option label="按租金比例（0~1）" value="RATIO" />
          </el-select>
        </el-form-item>
        <el-form-item label="补贴值" required>
          <el-input v-model.number="sf.subsidyValue" />
        </el-form-item>
        <el-form-item label="封顶金额">
          <el-input v-model.number="sf.maxAmount" />
        </el-form-item>
        <el-form-item label="生效起">
          <el-date-picker v-model="sf.effectiveStart" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="生效止">
          <el-date-picker v-model="sf.effectiveEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="补贴值含义随方式变化：定额=元/月；按面积=元/㎡·月；按人=元/人·月；比例=0~1" />
      <template #footer>
        <el-button @click="standardVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateStandard">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="batchVisible" title="批量发放补贴" width="480px">
      <el-form :model="bf" label-width="110px">
        <el-form-item label="补贴周期">
          <el-input v-model="bf.subsidyPeriod" placeholder="2026-10" /></el-form-item>
        <el-form-item label="组织"><OrgSelect v-model="bf.orgId" width="100%" /></el-form-item>
        <el-form-item label="发放方式">
          <el-select v-model="bf.payMode" style="width:100%">
            <el-option label="银行代发" value="BANK" />
            <el-option label="抵扣租金" value="OFFSET" />
          </el-select></el-form-item>
        <el-form-item label="试算（不落库）">
          <el-switch v-model="bf.dryRun" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doBatch">确认发放</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { subsidyApi } from '@/api/modules'
import req from '@/api/request'
import OrgSelect from '@/components/OrgSelect.vue'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const batchVisible = ref(false)
const bf = reactive({ subsidyPeriod: '', orgId: 1, payMode: 'BANK', dryRun: false })

async function load() {
  loading.value = true
  try {
    const d = await subsidyApi.records({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doBatch() {
  if (!bf.subsidyPeriod) { ElMessage.warning('请填写补贴周期'); return }
  await ElMessageBox.confirm('将按所选标准批量发放补贴，涉及资金，是否继续？',
    '确认批量发放', { type: 'warning' })
  saving.value = true
  try {
    const r = await subsidyApi.batchGrant({ ...bf })
    ElMessage.success('发放完成：' + (r?.count ?? r ?? '已执行'))
    batchVisible.value = false; load()
  } finally { saving.value = false }
}

async function confirm(row) {
  await subsidyApi.confirm(row.id)
  ElMessage.success('已确认发放'); load()
}

function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}

onMounted(load)
/** 发放失败：银行退回/账户异常等，记录原因便于补发 */
async function doFail(row) {
  const { value } = await ElMessageBox.prompt('失败原因（如账户异常/银行退回）', '标记发放失败',
    { inputValidator: (v) => (v && v.trim() ? true : '请填写失败原因') })
  await req.post(`/fin/subsidies/records/${row.id}/fail`, { reason: value })
  ElMessage.success('已标记失败')
  load()
}
// ---------------- 补贴标准 ----------------
const standards = ref([])
const stTotal = ref(0)
const stLoading = ref(false)
const standardVisible = ref(false)
const stQuery = reactive({ pageNum: 1, pageSize: 20, securityType: undefined,
  subsidyMode: undefined, keyword: '' })
const sf = reactive({ standardCode: '', standardName: '', securityType: 'PUBLIC',
  subsidyMode: 'FIXED', subsidyValue: null, maxAmount: null,
  effectiveStart: '', effectiveEnd: '' })

async function loadStandards() {
  stLoading.value = true
  try {
    const d = await req.get('/fin/subsidies/standards', {
      params: { pageNum: stQuery.pageNum, pageSize: stQuery.pageSize,
        securityType: stQuery.securityType || undefined,
        subsidyMode: stQuery.subsidyMode || undefined,
        keyword: stQuery.keyword || undefined }
    })
    standards.value = d.rows || []
    stTotal.value = Number(d.total || 0)
  } catch (e) {
    standards.value = []; stTotal.value = 0
  } finally { stLoading.value = false }
}

function openStandard() {
  Object.assign(sf, { standardCode: '', standardName: '', securityType: 'PUBLIC',
    subsidyMode: 'FIXED', subsidyValue: null, maxAmount: null,
    effectiveStart: '', effectiveEnd: '' })
  standardVisible.value = true
}

async function doCreateStandard() {
  if (!sf.standardCode || !sf.standardName || sf.subsidyValue === null) {
    ElMessage.warning('编码、名称、补贴值为必填'); return
  }
  saving.value = true
  try {
    await req.post('/fin/subsidies/standards', { ...sf })
    ElMessage.success('标准已创建')
    standardVisible.value = false
    loadStandards()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally { saving.value = false }
}

async function toggleStandard(row) {
  const enabled = row.status !== 'ENABLED'
  await ElMessageBox.confirm(
    `确认${enabled ? '启用' : '停用'}标准「${row.standardName}」？`, '提示',
    { type: 'warning' })
  await req.post(`/fin/subsidies/standards/${row.id}/status`, { enabled })
  ElMessage.success('已更新')
  loadStandards()
}
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
