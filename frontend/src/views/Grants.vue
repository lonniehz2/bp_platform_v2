<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">通行授权</h3>
        <el-tag size="small" :type="stats.riskLevel === 'HIGH' ? 'danger'
          : (stats.riskLevel === 'MEDIUM' ? 'warning' : 'success')">
          对账风险 {{ stats.riskLevel || '-' }}
        </el-tag>
        <span class="muted">差异待处置 {{ stats.pending ?? 0 }} 条</span>
      </div>

      <el-tabs v-model="tab" @tab-change="onTabChange">
        <!-- ============ 授权管理 ============ -->
        <el-tab-pane label="授权管理" name="grant">
          <div class="toolbar" style="margin-bottom:10px">
            <PersonPicker v-model="gq.personId" width="240px" testid="picker" />
            <SpaceSelect v-model="gq.spaceId" width="240px" testid="spaceselect" />
            <el-select v-model="gq.grantStatus" placeholder="状态" clearable
                       style="width:140px">
              <el-option v-for="s in GRANT_STATUS" :key="s" :label="enumLabel('grantStatus', s)"
                         :value="s" />
            </el-select>
            <el-button type="primary" @click="loadGrants">查询</el-button>
            <el-button @click="resetGrantQuery">清空</el-button>
            <el-button type="success" @click="openCreate">新建授权</el-button>
            <span class="muted">共 {{ grantTotal }} 条</span>
          </div>

          <el-table :data="grants" v-loading="grantLoading" border size="small">
            <el-table-column prop="grantNo" label="授权号" width="180" />
            <el-table-column prop="personIdName" label="人员" width="130">
              <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
            </el-table-column>
            <el-table-column prop="spaceId" label="空间" width="120" />
            <el-table-column prop="grantLevel" label="权限层级" width="110">
              <template #default="{ row }">{{ enumLabel('grantLevel', row.grantLevel) }}</template>
            </el-table-column>
            <el-table-column label="有效期" min-width="230">
              <template #default="{ row }">
                {{ row.validStart || '—' }} ~ {{ row.validEnd || '长期' }}
              </template>
            </el-table-column>
            <el-table-column prop="visitLimitTimes" label="访客次数" width="110">
              <template #default="{ row }">
                <span v-if="row.visitLimitTimes">
                  {{ row.visitUsedTimes || 0 }}/{{ row.visitLimitTimes }}
                </span>
                <span v-else class="muted">—</span>
              </template>
            </el-table-column>
            <el-table-column prop="grantStatus" label="状态" width="110">
              <template #default="{ row }">
                <el-tag size="small" :type="statusTagType(row.grantStatus)">
                  {{ row.grantStatusLabel || enumLabel('grantStatus', row.grantStatus) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="170" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDetail(row)">详情</el-button>
                <el-button link type="danger" :disabled="row.grantStatus === 'REVOKED'"
                           @click="revoke(row)">撤销</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                         :total="grantTotal" :page-size="gq.pageSize"
                         :current-page="gq.pageNum"
                         @current-change="(p) => { gq.pageNum = p; loadGrants() }" />
        </el-tab-pane>

        <!-- ============ 对账差异 ============ -->
        <el-tab-pane label="对账差异" name="diff">
          <div class="toolbar" style="margin-bottom:10px">
            <DeviceSelect v-model="lockId" width="240px" testid="device-select" />
            <el-button type="primary" :loading="running" @click="runReconcile">
              执行对账
            </el-button>
            <el-button @click="loadDiffs">刷新</el-button>
          </div>
          <el-alert type="info" :closable="false" show-icon
                    title="LOCAL_MISSING = 本地有效但设备未下发（住户刷不开门）；IOT_EXTRA = 已撤销但设备仍存在（安全风险）"
                    style="margin-bottom:12px" />
          <el-table :data="diffs" v-loading="loading" border size="small">
            <el-table-column prop="diffType" label="差异类型" width="150">
              <template #default="{ row }">
                <el-tag size="small" :type="row.diffType === 'IOT_EXTRA' ? 'danger' : 'warning'">
                  {{ row.diffTypeLabel || enumLabel('diffType', row.diffType) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="lockId" label="门锁" width="170">
              <template #default="{ row }">{{ row.lockIdName || row.lockId }}</template>
            </el-table-column>
            <el-table-column prop="personId" label="人员" width="120">
              <template #default="{ row }">{{ row.personIdName || row.personId || '—' }}</template>
            </el-table-column>
            <el-table-column prop="localValue" label="本地值" min-width="200" show-overflow-tooltip />
            <el-table-column prop="iotValue" label="IoT 值" min-width="180" show-overflow-tooltip />
            <el-table-column prop="handleStatus" label="处置状态" width="110">
              <template #default="{ row }">
                {{ row.handleStatusLabel || enumLabel('handleStatus', row.handleStatus) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDetail(row)">详情</el-button>
                <el-button v-if="row.diffType === 'LOCAL_MISSING'" link type="primary"
                           :disabled="row.handleStatus !== 'PENDING'"
                           @click="handle(row, 'REGRANT')">重新授权</el-button>
                <el-button v-if="row.diffType === 'IOT_EXTRA'" link type="danger"
                           :disabled="row.handleStatus !== 'PENDING'"
                           @click="handle(row, 'REVOKE')">撤销</el-button>
                <el-button link :disabled="row.handleStatus !== 'PENDING'"
                           @click="handle(row, 'IGNORED')">忽略</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                         :total="total" :page-size="query.pageSize"
                         :current-page="query.pageNum"
                         @current-change="(p) => { query.pageNum = p; loadDiffs() }" />
        </el-tab-pane>

        <!-- ============ 授权审计 ============ -->
        <el-tab-pane label="授权审计" name="audit">
          <el-alert type="info" :closable="false" show-icon
                    title="授权审计只追加、不可修改删除，用于事后追溯谁在何时授权/撤销了谁" />
          <el-table :data="audits" border size="small" style="margin-top:10px">
            <el-table-column prop="bizType" label="类型" width="120">
              <template #default="{ row }">
                {{ row.bizTypeLabel || enumLabel('bizType', row.bizType) }}
              </template>
            </el-table-column>
            <el-table-column prop="personId" label="人员" width="120">
              <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
            </el-table-column>
            <el-table-column prop="operatorName" label="操作人" width="120" />
            <el-table-column prop="reason" label="原因" min-width="200" />
            <el-table-column prop="result" label="结果" width="100" />
            <el-table-column prop="createTime" label="时间" width="170" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 新建授权 -->
    <el-dialog v-model="createVisible" title="新建通行授权" width="560px">
      <el-form :model="gf" label-width="110px">
        <el-form-item label="人员ID" required>
          <PersonPicker v-model="gf.personId" width="200px" testid="picker" />
        </el-form-item>
        <el-form-item label="空间ID" required>
          <el-input v-model.number="gf.spaceId" placeholder="授权到哪个空间（房间/楼栋）" />
        </el-form-item>
        <el-form-item label="权限层级" required>
          <el-select v-model="gf.grantLevel" style="width:100%">
            <el-option label="产权级（可管理、可转授）" value="OWNERSHIP" />
            <el-option label="管理级（可管理）" value="MANAGEMENT" />
            <el-option label="使用级（仅可开门）" value="USAGE" />
            <el-option label="访客级（限次通行）" value="VISIT" />
          </el-select>
        </el-form-item>
        <el-form-item label="生效时间">
          <el-date-picker v-model="gf.validStart" type="datetime" style="width:100%"
                          value-format="YYYY-MM-DDTHH:mm:ss" placeholder="留空=立即生效" />
        </el-form-item>
        <el-form-item label="失效时间">
          <el-date-picker v-model="gf.validEnd" type="datetime" style="width:100%"
                          value-format="YYYY-MM-DDTHH:mm:ss" placeholder="留空=长期" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="gf.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存并下发</el-button>
      </template>
    </el-dialog>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
  </div>
</template>

<script setup>
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
