<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">IoT 联调工具</h3>
      <el-tag size="small" type="info">验签 / 回调日志 / 重放</el-tag>
      <div class="spacer" />
      <el-button @click="loadLogs">刷新日志</el-button>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="签名自测" name="sign">
        <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
                  title="用于与 IoT 方对照签名：填写同样的 appId/时间戳/nonce/body，双方算出的 signature 应完全一致。" />
        <el-form :model="sf" label-width="110px" style="max-width:720px">
          <el-form-item label="回调动作">
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
          <el-form-item label="appId">
            <el-input v-model="sf.appId" placeholder="留空用系统参数" />
          </el-form-item>
          <el-form-item label="appSecret">
            <el-input v-model="sf.appSecret" placeholder="留空用系统参数" show-password />
          </el-form-item>
          <el-form-item label="timestamp">
            <el-input v-model="sf.timestamp" placeholder="留空取当前秒" />
          </el-form-item>
          <el-form-item label="nonce">
            <el-input v-model="sf.nonce" placeholder="留空用 testnonce" />
          </el-form-item>
          <el-form-item label="body">
            <el-input v-model="sf.body" type="textarea" :rows="5" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="signing" @click="doSign">计算签名</el-button>
          </el-form-item>
        </el-form>
        <div v-if="signed.signature">
          <el-descriptions :column="1" border size="small" style="max-width:900px">
            <el-descriptions-item label="bodySha256">{{ signed.bodySha256 }}</el-descriptions-item>
            <el-descriptions-item label="canonical">
              <pre class="mono">{{ signed.canonical }}</pre>
            </el-descriptions-item>
            <el-descriptions-item label="signature">{{ signed.signature }}</el-descriptions-item>
            <el-descriptions-item label="请求头">{{ signed.headerHint }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-tab-pane>

      <el-tab-pane label="对接能力" name="cap">
        <el-alert type="info" :closable="false" show-icon
                  title="展示当前接入模式、凭证配置与仍需 IoT 提供的能力（联调/上线切换前先看这里）"
                  style="margin-bottom:10px" />
        <el-row :gutter="12">
          <el-col :span="12">
            <div class="card-title">客户端模式</div>
            <el-table :data="capModeRows" size="small" border>
              <el-table-column prop="name" label="客户端" width="140" />
              <el-table-column prop="mode" label="当前模式" />
            </el-table>
            <div class="card-title" style="margin-top:12px">回调配置</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="验签">{{ cap.callback?.verify }}</el-descriptions-item>
              <el-descriptions-item label="回调 AppId">{{ cap.callback?.appId || '—' }}</el-descriptions-item>
              <el-descriptions-item label="时间戳窗口">
                {{ cap.callback?.timestampToleranceSeconds }} 秒
              </el-descriptions-item>
              <el-descriptions-item label="Nonce 缓存">
                {{ cap.callback?.nonceCacheMinutes }} 分钟
              </el-descriptions-item>
              <el-descriptions-item label="默认租户">{{ cap.callback?.defaultTenant }}</el-descriptions-item>
            </el-descriptions>
          </el-col>
          <el-col :span="12">
            <div class="card-title">平台凭证</div>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="IoT 地址">{{ cap.iotCredential?.baseUrl || '—' }}</el-descriptions-item>
              <el-descriptions-item label="AppId">
                {{ cap.iotCredential?.appIdConfigured ? '已配置' : '未配置' }}
              </el-descriptions-item>
              <el-descriptions-item label="Secret">
                {{ cap.iotCredential?.appSecretConfigured ? '已配置' : '未配置' }}
              </el-descriptions-item>
              <el-descriptions-item label="可切真实环境">
                {{ cap.readyForReal ? '是' : '否（凭证未配齐）' }}
              </el-descriptions-item>
            </el-descriptions>

            <div class="card-title" style="margin-top:12px">
              仍需 IoT 提供（{{ (cap.pendingFromIot || []).length }}）
            </div>
            <el-table :data="cap.pendingFromIot || []" size="small" border>
              <el-table-column prop="name" label="事项" min-width="180" show-overflow-tooltip />
              <el-table-column prop="note" label="说明" min-width="200" show-overflow-tooltip />
            </el-table>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="凭据同步" name="cred">
        <div class="toolbar" style="margin-bottom:10px">
          <el-select v-model="credQuery.status" placeholder="同步状态" clearable
                     style="width:140px" @change="reloadCred">
            <el-option label="成功" value="SUCCESS" />
            <el-option label="失败" value="FAILED" />
            <el-option label="待同步" value="PENDING" />
          </el-select>
          <el-button type="primary" @click="reloadCred">查询</el-button>
          <span class="muted">共 {{ credTotal }} 条 ｜ 密码/卡/人脸/离线码下发记录</span>
        </div>
        <el-table :data="creds" border size="small">
          <el-table-column prop="createTime" label="时间" width="170" />
          <el-table-column prop="keyType" label="类型" width="130" />
          <el-table-column prop="action" label="动作" width="100" />
          <el-table-column prop="keyringId" label="钥匙ID" width="190" />
          <el-table-column prop="personId" label="人员ID" width="190" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'SUCCESS' ? 'success'
                : (row.status === 'FAILED' ? 'danger' : 'info')">
                {{ row.status === 'SUCCESS' ? '成功' : (row.status === 'FAILED' ? '失败' : '待同步') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="errorMsg" label="错误" min-width="160" show-overflow-tooltip />
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="credTotal" :page-size="credQuery.pageSize"
                       :current-page="credQuery.pageNum"
                       @current-change="(p) => { credQuery.pageNum = p; loadCred() }" />
      </el-tab-pane>

      <el-tab-pane label="回调日志" name="logs">
        <div class="toolbar" style="margin-bottom:10px">
          <el-select v-model="query.msgType" placeholder="动作" clearable style="width:160px"
                     @change="reloadLogs">
            <el-option v-for="a in ACTIONS" :key="a" :label="a" :value="a" />
          </el-select>
          <el-select v-model="query.processStatus" placeholder="处理状态" clearable
                     style="width:140px" @change="reloadLogs">
            <el-option label="已处理" value="DONE" />
            <el-option label="处理失败" value="FAILED" />
            <el-option label="已拒绝" value="REJECTED" />
            <el-option label="重复" value="DUPLICATE" />
          </el-select>
          <el-button type="primary" @click="reloadLogs">查询</el-button>
          <span class="muted">共 {{ total }} 条</span>
        </div>
        <el-table :data="logs" border size="small">
          <el-table-column prop="receiveTime" label="接收时间" width="170" />
          <el-table-column prop="msgType" label="动作" width="130" />
          <el-table-column prop="eventId" label="事件/幂等号" width="230" />
          <el-table-column label="验签" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.signOk ? 'success' : 'danger'">
                {{ row.signOk ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="处理" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="statusType(row.processStatus)">
                {{ statusLabel(row.processStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="errorMsg" label="错误" min-width="160" show-overflow-tooltip />
          <el-table-column prop="rawBody" label="报文" min-width="220" show-overflow-tooltip />
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="replay(row)">重放</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                       :total="total" :page-size="query.pageSize" :current-page="query.pageNum"
                       @current-change="(p) => { query.pageNum = p; loadLogs() }" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
/**
 * IoT 联调工具：签名自测、回调日志、历史回调重放。
 */
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

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
