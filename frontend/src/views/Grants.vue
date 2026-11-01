<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">{{ t('grant.title') }}</h3>
        <el-tag size="small" :type="stats.riskLevel === 'HIGH' ? 'danger'
          : (stats.riskLevel === 'MEDIUM' ? 'warning' : 'success')">
          {{ t('misc4.risk', { level: stats.riskLevel || '-' }) }}
        </el-tag>
        <span class="muted">{{ t('misc.grantPending', { n: stats.pending ?? 0 }) }}</span>
      </div>

      <el-tabs v-model="tab" @tab-change="onTabChange">
        <!-- ============ 授权管理 ============ -->
        <el-tab-pane :label="t('grant.grantTab')" name="grant">
          <div class="toolbar" style="margin-bottom:10px">
            <PersonPicker v-model="gq.personId" width="240px" testid="picker" />
            <SpaceSelect v-model="gq.spaceId" width="240px" testid="spaceselect" />
            <el-select v-model="gq.grantStatus" :placeholder="t('grant.status')" clearable
                       style="width:140px">
              <el-option v-for="s in GRANT_STATUS" :key="s" :label="enumLabel('grantStatus', s)"
                         :value="s" />
            </el-select>
            <el-button type="primary" @click="loadGrants">{{ t('grant.search') }}</el-button>
            <el-button @click="resetGrantQuery">{{ t('grant.reset') }}</el-button>
            <el-button type="success" @click="openCreate">{{ t('grant.create') }}</el-button>
            <span class="muted">{{ t('misc4.total', { n: grantTotal }) }}</span>
          </div>

          <el-table :empty-text="t('misc.grantEmpty')" :data="grants" v-loading="grantLoading" border size="small">
            <el-table-column prop="grantNo" :label="t('grant.grantNo')" width="180" />
            <el-table-column prop="personIdName" :label="t('grant.person')" width="130">
              <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
            </el-table-column>
            <el-table-column prop="spaceId" :label="t('grant.space')" width="120" />
            <el-table-column prop="grantLevel" :label="t('grant.level')" width="110">
              <template #default="{ row }">{{ enumLabel('grantLevel', row.grantLevel) }}</template>
            </el-table-column>
            <el-table-column :label="t('grant.validity')" min-width="230">
              <template #default="{ row }">
                {{ row.validStart || '—' }} ~ {{ row.validEnd || t('misc4.longTerm') }}
              </template>
            </el-table-column>
            <el-table-column prop="visitLimitTimes" :label="t('grant.visitorTimes')" width="110">
              <template #default="{ row }">
                <span v-if="row.visitLimitTimes">
                  {{ row.visitUsedTimes || 0 }}/{{ row.visitLimitTimes }}
                </span>
                <span v-else class="muted">{{ t('misc.unlimited') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="grantStatus" :label="t('grant.statusCol')" width="110">
              <template #default="{ row }">
                <el-tag size="small" :type="statusTagType(row.grantStatus)">
                  {{ row.grantStatusLabel || enumLabel('grantStatus', row.grantStatus) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="t('grant.actions')" width="170" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDetail(row)">{{ t('grant.detail') }}</el-button>
                <el-button link type="danger" :disabled="row.grantStatus === 'REVOKED'"
                           @click="revoke(row)">{{ t('grant.revoke') }}</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                         :total="+grantTotal || 0" :page-size="gq.pageSize"
                         :current-page="gq.pageNum"
                         @current-change="(p) => { gq.pageNum = p; loadGrants() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { gq.pageSize = s; gq.pageNum = 1; loadGrants() }" />
        </el-tab-pane>

        <!-- ============ 对账差异 ============ -->
        <el-tab-pane :label="t('grant.diffTab')" name="diff">
          <div class="toolbar" style="margin-bottom:10px">
            <DeviceSelect v-model="lockId" width="240px" testid="device-select" />
            <el-button type="primary" :loading="running" @click="runReconcile">
              执行对账
            </el-button>
            <el-button @click="loadDiffs">{{ t('grant.refresh') }}</el-button>
          </div>
          <el-alert type="info" :closable="false" show-icon
                    :title="t('misc4.diffTip')"
                    style="margin-bottom:12px" />
          <el-table :data="diffs" v-loading="loading" border size="small">
            <el-table-column prop="diffType" :label="t('grant.diffType')" width="150">
              <template #default="{ row }">
                <el-tag size="small" :type="row.diffType === 'IOT_EXTRA' ? 'danger' : 'warning'">
                  {{ row.diffTypeLabel || enumLabel('diffType', row.diffType) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="lockId" :label="t('grant.lock')" width="170">
              <template #default="{ row }">{{ row.lockIdName || row.lockId }}</template>
            </el-table-column>
            <el-table-column prop="personId" :label="t('grant.person')" width="120">
              <template #default="{ row }">{{ row.personIdName || row.personId || '—' }}</template>
            </el-table-column>
            <el-table-column prop="localValue" :label="t('grant.localValue')" min-width="200" show-overflow-tooltip />
            <el-table-column prop="iotValue" :label="t('grant.iotValue')" min-width="180" show-overflow-tooltip />
            <el-table-column prop="handleStatus" :label="t('grant.handleStatus')" width="110">
              <template #default="{ row }">
                {{ row.handleStatusLabel || enumLabel('handleStatus', row.handleStatus) }}
              </template>
            </el-table-column>
            <el-table-column :label="t('grant.actions')" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDetail(row)">{{ t('misc4.detail') }}</el-button>
                <el-button v-if="row.diffType === 'LOCAL_MISSING'" link type="primary"
                           :disabled="row.handleStatus !== 'PENDING'"
                           @click="handle(row, 'REGRANT')">{{ t('misc.regrant') }}</el-button>
                <el-button v-if="row.diffType === 'IOT_EXTRA'" link type="danger"
                           :disabled="row.handleStatus !== 'PENDING'"
                           @click="handle(row, 'REVOKE')">{{ t('misc.revoke') }}</el-button>
                <el-button link :disabled="row.handleStatus !== 'PENDING'"
                           @click="handle(row, 'IGNORED')">{{ t('misc.ignore') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                         :total="+total || 0" :page-size="query.pageSize"
                         :current-page="query.pageNum"
                         @current-change="(p) => { query.pageNum = p; loadDiffs() }" />
        </el-tab-pane>

        <!-- ============ 授权审计 ============ -->
        <el-tab-pane :label="t('grant.auditTab')" name="audit">
          <el-alert type="info" :closable="false" show-icon
                    title="授权审计只追加、不可修改删除，用于事后追溯谁在何时授权/撤销了谁" />
          <el-table :data="audits" border size="small" style="margin-top:10px">
            <el-table-column prop="bizType" :label="t('grant.bizType')" width="120">
              <template #default="{ row }">
                {{ row.bizTypeLabel || enumLabel('bizType', row.bizType) }}
              </template>
            </el-table-column>
            <el-table-column prop="personId" :label="t('grant.person')" width="120">
              <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
            </el-table-column>
            <el-table-column prop="operatorName" :label="t('grant.operator')" width="120" />
            <el-table-column prop="reason" :label="t('grant.reason')" min-width="200" />
            <el-table-column prop="result" :label="t('grant.result')" width="100" />
            <el-table-column prop="createTime" :label="t('grant.time')" width="170" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 新建授权 -->
    <el-dialog v-model="createVisible" :title="t('grant.createTitle')" width="560px">
      <el-form :model="gf" label-width="110px">
        <el-form-item :label="t('grant.personId')" required>
          <PersonPicker v-model="gf.personId" width="200px" testid="picker" />
        </el-form-item>
        <el-form-item :label="t('grant.spaceId')" required>
          <el-input v-model.number="gf.spaceId" :placeholder="t('grant.spaceHint')" />
        </el-form-item>
        <el-form-item :label="t('grant.level')" required>
          <el-select v-model="gf.grantLevel" style="width:100%">
            <el-option :label="t('grant.ownership')" value="OWNERSHIP" />
            <el-option :label="t('grant.management')" value="MANAGEMENT" />
            <el-option :label="t('grant.usage')" value="USAGE" />
            <el-option :label="t('grant.visitLevel')" value="VISIT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('grant.validStart')">
          <el-date-picker v-model="gf.validStart" type="datetime" style="width:100%"
                          value-format="YYYY-MM-DDTHH:mm:ss" :placeholder="t('grant.startHint')" />
        </el-form-item>
        <el-form-item :label="t('grant.validEnd')">
          <el-date-picker v-model="gf.validEnd" type="datetime" style="width:100%"
                          value-format="YYYY-MM-DDTHH:mm:ss" :placeholder="t('grant.endHint')" />
        </el-form-item>
        <el-form-item :label="t('grant.remark')">
          <el-input v-model="gf.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('grant.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('grant.saveIssue') }}</el-button>
      </template>
    </el-dialog>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('grant.detail')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * 通行授权：授权管理（新建/撤销/查询） + 对账差异 + 授权审计。
 *
 * 授权对象是「空间」，下发载体是门锁钥匙（keyring），
 * 因此命名用「通行授权」而非「门禁授权」。
 */
import { enumLabel } from '@/constants/enums'
import { reactive, ref, onMounted } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { grantApi } from '@/api/modules'
import DeviceSelect from '@/components/DeviceSelect.vue'
import PersonPicker from '@/components/PersonPicker.vue'
import SpaceSelect from '@/components/SpaceSelect.vue'

const { t } = useI18n()
const tab = ref('grant')

// ---------------- 授权管理 ----------------
const GRANT_STATUS = ['PENDING', 'EFFECTIVE', 'EXPIRED', 'FROZEN', 'REVOKED']
const grants = ref([])
const grantTotal = ref(0)
const grantLoading = ref(false)
const gq = reactive({ pageNum: 1, pageSize: 20, personId: undefined,
  spaceId: undefined, grantStatus: undefined })

async function loadGrants() {
  grantLoading.value = true
  try {
    const params = { pageNum: gq.pageNum, pageSize: gq.pageSize }
    if (gq.personId) params.personId = gq.personId
    if (gq.spaceId) params.spaceId = gq.spaceId
    if (gq.grantStatus) params.grantStatus = gq.grantStatus
    const d = await grantApi.page(params)
    grants.value = d.rows || []
    grantTotal.value = Number(d.total || 0)
  } finally {
    grantLoading.value = false
  }
}

function resetGrantQuery() {
  gq.personId = undefined
  gq.spaceId = undefined
  gq.grantStatus = undefined
  gq.pageNum = 1
  loadGrants()
}

const createVisible = ref(false)
const saving = ref(false)
const gf = reactive({ personId: undefined, spaceId: undefined,
  grantLevel: 'USAGE', validStart: '', validEnd: '', remark: '' })

function openCreate() {
  // 非产权级必须有失效时间（后端规则），默认给一年
  const now = new Date()
  const oneYear = new Date(now.getTime() + 365 * 24 * 3600 * 1000)
  const fmt = (d) => {
    const p = (n) => String(n).padStart(2, '0')
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
      + 'T' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':00'
  }
  Object.assign(gf, { personId: undefined, spaceId: undefined,
    grantLevel: 'USAGE', validStart: fmt(now), validEnd: fmt(oneYear), remark: '' })
  createVisible.value = true
}

async function doCreate() {
  if (!gf.personId || !gf.spaceId) {
    ElMessage.warning('请填写人员与空间')
    return
  }
  if (gf.grantLevel !== 'OWNERSHIP' && !gf.validEnd) {
    ElMessage.warning('非产权级授权需选择失效时间')
    return
  }
  saving.value = true
  try {
    await grantApi.create({
      personId: gf.personId,
      spaceId: gf.spaceId,
      grantLevel: gf.grantLevel,
      validStart: gf.validStart || null,
      validEnd: gf.validEnd || null,
      sourceType: 'MANUAL',
      remark: gf.remark
    })
    ElMessage.success('授权已创建并下发')
    createVisible.value = false
    loadGrants()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    saving.value = false
  }
}

async function revoke(row) {
  try {
    const { value } = await ElMessageBox.prompt(
      `确认撤销「${row.personIdName || row.personId}」对空间 ${row.spaceId} 的授权？`,
      '撤销授权', {
        inputPlaceholder: '撤销原因（必填）',
        inputValidator: (v) => (v && v.trim() ? true : '请填写撤销原因')
      })
    await grantApi.revoke(row.id, value)
    ElMessage.success('已撤销并下发')
    loadGrants()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '撤销失败')
  }
}

function statusTagType(s) {
  if (s === 'EFFECTIVE') return 'success'
  if (s === 'REVOKED' || s === 'FROZEN') return 'danger'
  if (s === 'EXPIRED') return 'info'
  return 'warning'
}

// ---------------- 对账差异 ----------------
const loading = ref(false)
const running = ref(false)
const diffs = ref([])
const total = ref(0)
const stats = ref({})
const lockId = ref('')
const query = reactive({ pageNum: 1, pageSize: 20 })

async function loadDiffs() {
  loading.value = true
  try {
    const d = await grantApi.diffs({ ...query })
    diffs.value = d.rows || []
    total.value = Number(d.total || 0)
    stats.value = await grantApi.reconcileStats()
  } finally {
    loading.value = false
  }
}

async function runReconcile() {
  running.value = true
  try {
    const r = await grantApi.reconcileRun(lockId.value || undefined)
    ElMessage.success(`对账完成：差异 ${r.diffRecorded} 条（${r.conclusion}）`)
    loadDiffs()
  } finally {
    running.value = false
  }
}

async function handle(row, action) {
  await grantApi.handleDiff(row.id, { action, remark: '页面处置' })
  ElMessage.success('已处置')
  loadDiffs()
}

// ---------------- 授权审计 ----------------
const audits = ref([])

async function loadAudits() {
  const a = await grantApi.auditLogs({ pageNum: 1, pageSize: 10 })
  audits.value = a.rows || []
}

// ---------------- 详情 / 切换 ----------------
const dvVisible = ref(false)
const dvRow = ref({})

function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

function onTabChange(name) {
  if (name === 'diff') loadDiffs()
  if (name === 'audit') loadAudits()
  if (name === 'grant') loadGrants()
}

onMounted(async () => {
  await loadGrants()
  try {
    stats.value = await grantApi.reconcileStats()
  } catch (e) {
    stats.value = {}
  }
})
</script>
