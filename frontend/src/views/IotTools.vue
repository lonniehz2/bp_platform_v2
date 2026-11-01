<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('iot.title') }}</h3>
      <el-tag size="small" type="info">{{ t('sysAdminX.verifyTab') }}</el-tag>
      <div class="spacer" />
      <el-button @click="loadLogs">{{ t('iot.refreshLogs') }}</el-button>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane :label="t('iot.signTab')" name="sign">
        <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
                  :title="t('sysAdminX.verifyTip')" />
        <el-form :model="sf" label-width="110px" style="max-width:720px">
          <el-form-item :label="t('iot.action')">
            <el-select v-model="sf.action" style="width:100%">
              <el-option label="event" value="event" />
              <el-option label="access" value="access" />
              <el-option label="command/ack" value="command/ack" />
              <el-option label="grant/ack" value="grant/ack" />
              <el-option label="heartbeat" value="heartbeat" />
              <el-option label="meter" value="meter" />
              <el-option label="device-status" value="device-status" />
              <el-option label="alarm-ack" value="alarm-ack" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('iot.appId')">
            <el-input v-model="sf.appId" :placeholder="t('iot.blankParam')" />
          </el-form-item>
          <el-form-item :label="t('iot.appSecret')">
            <el-input v-model="sf.appSecret" :placeholder="t('sysAdminX.secretHint')" show-password />
          </el-form-item>
          <el-form-item :label="t('iot.timestamp')">
            <el-input v-model="sf.timestamp" :placeholder="t('iot.blankTimestamp')" />
          </el-form-item>
          <el-form-item :label="t('iot.nonce')">
            <el-input v-model="sf.nonce" :placeholder="t('iot.blankNonce')" />
          </el-form-item>
          <el-form-item :label="t('iot.body')">
            <el-input v-model="sf.body" type="textarea" :rows="5" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="signing" @click="doSign">{{ t('iot.calcSign') }}</el-button>
          </el-form-item>
        </el-form>
        <div v-if="signed.signature">
          <el-descriptions :column="1" border size="small" style="max-width:900px">
            <el-descriptions-item label="bodySha256">{{ signed.bodySha256 }}</el-descriptions-item>
            <el-descriptions-item label="canonical">
              <pre class="mono">{{ signed.canonical }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="signature">{{ signed.signature }}</el-descriptions-item>
            <el-descriptions-item :label="t('iot.header')">{{ signed.headerHint }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-tab-pane>

      <el-tab-pane :label="t('iot.capTab')" name="cap">
        <el-alert type="info" :closable="false" show-icon
                  :title="t('sysAdminX.modeTip')"
                  style="margin-bottom:10px" />
        <el-row :gutter="12">
          <el-col :span="12">
            <div class="card-title">{{ t('sysAdminX.clientMode') }}</div>
            <el-table :data="capModeRows" size="small" border>
              <el-table-column prop="name" :label="t('iot.client')" width="140" />
              <el-table-column prop="mode" :label="t('iot.mode')" />
            </el-table>
            <div class="card-title" style="margin-top:12px">{{ t('sysAdminX.callbackConfig') }}</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item :label="t('iot.verify')">{{ cap.callback?.verify }}</el-descriptions-item>
              <el-descriptions-item :label="t('iot.callbackAppId')">{{ cap.callback?.appId || '—' }}</el-descriptions-item>
              <el-descriptions-item :label="t('iot.tsWindow')">
                {{ cap.callback?.timestampToleranceSeconds }} 秒
              </el-descriptions-item>
              <el-descriptions-item :label="t('iot.nonceCache')">
                {{ cap.callback?.nonceCacheMinutes }} 分钟
              </el-descriptions-item>
              <el-descriptions-item :label="t('iot.defaultTenant')">{{ cap.callback?.defaultTenant }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
          <el-col :span="12">
            <div class="card-title">{{ t('sysAdminX.platformCredential') }}</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item :label="t('iot.iotUrl')">{{ cap.iotCredential?.baseUrl || '—' }}</el-descriptions-item>
              <el-descriptions-item :label="t('iot.appId')">
                {{ cap.iotCredential?.appIdConfigured ? t('sysAdminX.configured') : t('sysAdminX.notConfigured') }}
              </el-descriptions-item>
              <el-descriptions-item :label="t('iot.secret')">
                {{ cap.iotCredential?.appSecretConfigured ? t('sysAdminX.configured') : t('sysAdminX.notConfigured') }}
              </el-descriptions-item>
              <el-descriptions-item :label="t('iot.canSwitch')">
                {{ cap.readyForReal ? t('sysAdminX.readyReal') : t('sysAdminX.notReady') }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="card-title" style="margin-top:12px">
              仍需 IoT 提供（{{ (cap.pendingFromIot || []).length }}）
            </div>
            <el-table :data="cap.pendingFromIot || []" size="small" border>
              <el-table-column prop="name" :label="t('iot.item')" min-width="180" show-overflow-tooltip />
              <el-table-column prop="note" :label="t('iot.note')" min-width="200" show-overflow-tooltip />
            </el-table>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane :label="t('iot.credTab')" name="cred">
        <div class="toolbar" style="margin-bottom:10px">
          <el-select v-model="credQuery.status" :placeholder="t('iot.syncStatus')" clearable
                     style="width:140px" @change="reloadCred">
            <el-option :label="t('iot.success')" value="SUCCESS" />
            <el-option :label="t('iot.failed')" value="FAILED" />
            <el-option :label="t('iot.pending')" value="PENDING" />
          </el-select>
          <el-button type="primary" @click="reloadCred">{{ t('iot.search') }}</el-button>
          <span class="muted">共 {{ credTotal }} 条 ｜ 密码/卡/人脸/离线码下发记录</span>
        </div>
        <el-table :data="creds" border size="small">
          <el-table-column prop="createTime" :label="t('iot.time')" width="170" />
          <el-table-column prop="keyType" :label="t('iot.type')" width="130" />
          <el-table-column prop="action" :label="t('iot.actionCol')" width="100" />
          <el-table-column prop="keyringId" :label="t('iot.keyringId')" width="190" />
          <el-table-column prop="personId" :label="t('iot.personId')" width="190" />
          <el-table-column :label="t('iot.status')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'SUCCESS' ? 'success'
                : (row.status === 'FAILED' ? 'danger' : 'info')">
                {{ row.status === 'SUCCESS' ? '成功' : (row.status === 'FAILED' ? '失败' : '待同步') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="errorMsg" :label="t('iot.error')" min-width="160" show-overflow-tooltip />
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                       :total="+credTotal || 0" :page-size="credQuery.pageSize"
                       :current-page="credQuery.pageNum"
                       @current-change="(p) => { credQuery.pageNum = p; loadCred() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { credQuery.pageSize = s; credQuery.pageNum = 1; loadCred() }" />
      </el-tab-pane>

      <el-tab-pane :label="t('iot.logTab')" name="logs">
        <div class="toolbar" style="margin-bottom:10px">
          <el-select v-model="query.msgType" :placeholder="t('iot.msgType')" clearable style="width:160px"
                     @change="reloadLogs">
            <el-option v-for="a in ACTIONS" :key="a" :label="a" :value="a" />
          </el-select>
          <el-select v-model="query.processStatus" :placeholder="t('iot.processStatus')" clearable
                     style="width:140px" @change="reloadLogs">
            <el-option :label="t('iot.done')" value="DONE" />
            <el-option :label="t('iot.handleFailed')" value="FAILED" />
            <el-option :label="t('iot.rejected')" value="REJECTED" />
            <el-option :label="t('iot.duplicate')" value="DUPLICATE" />
          </el-select>
          <el-button type="primary" @click="reloadLogs">{{ t('iot.search') }}</el-button>
          <el-button type="warning" plain :loading="replaying" @click="replayRange">
            {{ t('iot.replayFailures') }}
          </el-button>
          <span class="muted">共 {{ total }} 条</span>
        </div>
        <el-table :data="logs" border size="small">
          <el-table-column prop="receiveTime" :label="t('iot.receiveTime')" width="170" />
          <el-table-column prop="msgType" :label="t('iot.msgType')" width="130" />
          <el-table-column prop="eventId" :label="t('iot.eventId')" width="230" />
          <el-table-column label="验签" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.signOk ? 'success' : 'danger'">
                {{ row.signOk ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('iot.process')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="statusType(row.processStatus)">
                {{ statusLabel(row.processStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="errorMsg" label="错误" min-width="160" show-overflow-tooltip />
          <el-table-column prop="rawBody" :label="t('iot.bodyCol')" min-width="220" show-overflow-tooltip />
          <el-table-column :label="t('iot.actions')" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="replay(row)">{{ t('iot.replay') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="+total || 0" :page-size="query.pageSize" :current-page="query.pageNum"
                       @current-change="(p) => { query.pageNum = p; loadLogs() }" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * IoT 联调工具：签名自测、回调日志、历史回调重放。
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const { t } = useI18n()
const ACTIONS = ['event', 'access', 'command/ack', 'grant/ack', 'heartbeat', 'meter',
  'device-status', 'alarm-ack']

const tab = ref('sign')
const signing = ref(false)
const signed = ref({})
const sf = reactive({ action: 'event', appId: '', appSecret: '', timestamp: '', nonce: '',
  body: '{"eventId":"EV-TEST-001","deviceId":"LK00005771","identifier":"LOW_BATTERY","eventLevel":"WARN","eventTime":"2026-10-27 06:00:00","body":"{\\"battery\\":12}"}' })

const cap = ref({})
const capModeRows = computed(() => {
  const m = cap.value.modes || {}
  const name = { command: '指令下发', device: '设备台账', meter: '表计拉取', credential: '凭据下发' }
  return Object.keys(name).map((k) => ({ name: name[k], mode: m[k] || '—' }))
})

async function loadCapabilities() {
  try {
    cap.value = await req.get('/iot/capabilities')
  } catch (e) { cap.value = {} }
}

const creds = ref([])
const credTotal = ref(0)
const credQuery = reactive({ pageNum: 1, pageSize: 20, status: '' })

const replaying = ref(false)

/** 断线补推/失败重试：批量重放近 24 小时 FAILED 的回调 */
async function replayRange() {
  replaying.value = true
  try {
    const to = new Date()
    const from = new Date(to.getTime() - 24 * 3600 * 1000)
    const fmt = (d) => d.toISOString().slice(0, 19).replace('T', ' ')
    const r = await req.post('/iot/callback-logs/replay-range', null,
      { params: { from: fmt(from), to: fmt(to), status: 'FAILED', limit: 100 } })
    ElMessage.success('重放 ' + (r?.matched || 0) + ' 条：成功 ' + (r?.success || 0)
      + '，失败 ' + (r?.failed || 0))
    loadLogs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '批量重放失败')
  } finally { replaying.value = false }
}

const logs = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, msgType: '', processStatus: '' })

const STATUS = { DONE: { label: '已处理', type: 'success' },
  FAILED: { label: '处理失败', type: 'danger' },
  REJECTED: { label: '已拒绝', type: 'warning' },
  DUPLICATE: { label: '重复', type: 'info' },
  RECEIVED: { label: '已接收', type: 'info' } }

function statusLabel(s) { return (STATUS[s] || {}).label || s || '—' }
function statusType(s) { return (STATUS[s] || {}).type || 'info' }

async function doSign() {
  signing.value = true
  try {
    signed.value = await req.post('/iot/sign-preview', { ...sf })
  } catch (e) {
    ElMessage.error('签名计算失败')
  } finally { signing.value = false }
}

async function loadCred() {
  try {
    const d = await req.get('/iot/credential-sync', {
      params: { pageNum: credQuery.pageNum, pageSize: credQuery.pageSize,
        status: credQuery.status || undefined }
    })
    creds.value = d.rows || []
    credTotal.value = Number(d.total || 0)
  } catch (e) {
    creds.value = []; credTotal.value = 0
  }
}

function reloadCred() { credQuery.pageNum = 1; loadCred() }

async function loadLogs() {
  try {
    const d = await req.get('/iot/callback-logs', {
      params: { pageNum: query.pageNum, pageSize: query.pageSize,
        msgType: query.msgType || undefined,
        processStatus: query.processStatus || undefined }
    })
    logs.value = d.rows || []
    total.value = Number(d.total || 0)
  } catch (e) {
    logs.value = []; total.value = 0
  }
}

function reloadLogs() { query.pageNum = 1; loadLogs() }

async function replay(row) {
  await ElMessageBox.confirm(
    `用当前密钥重新签名并重放该回调（动作 ${row.msgType}）？`, '重放', { type: 'warning' })
  const r = await req.post(`/iot/callback-logs/${row.id}/replay`)
  ElMessage.success(`重放结果：${r.code}（HTTP ${r.httpStatus}）`)
  loadLogs()
}

onMounted(() => { loadLogs(); loadCred(); loadCapabilities() })
</script>

<style scoped>
.mono {
  margin: 0;
  font-family: Consolas, monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
