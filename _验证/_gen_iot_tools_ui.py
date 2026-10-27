# -*- coding: utf-8 -*-
"""前端：IoT 联调工具页（回调日志 / 签名自测 / 重放）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

VIEW = '''<template>
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const ACTIONS = ['event', 'access', 'command/ack', 'grant/ack', 'heartbeat', 'meter',
  'device-status', 'alarm-ack']

const tab = ref('sign')
const signing = ref(false)
const signed = ref({})
const sf = reactive({ action: 'event', appId: '', appSecret: '', timestamp: '', nonce: '',
  body: '{"eventId":"EV-TEST-001","deviceId":"LK00005771","identifier":"LOW_BATTERY","eventLevel":"WARN","eventTime":"2026-10-27 06:00:00","body":"{\\\\"battery\\\\":12}"}' })

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

onMounted(loadLogs)
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
'''

open(os.path.join(ROOT, 'frontend', 'src', 'views', 'IotTools.vue'), 'w',
     encoding='utf-8', newline='').write(VIEW)
print('IotTools.vue 已创建')

# 路由
p = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')
s = io.open(p, encoding='utf-8').read()
if "'/iot-tools'" not in s:
    s = s.replace("""  {
    path: '/dev-commands',""", """  {
    path: '/iot-tools',
    name: 'IotTools',
    component: () => import('@/views/IotTools.vue'),
    meta: { title: 'IoT联调工具', icon: 'Guide', group: '设备与通行',
      perm: 'dev:command:view' }
  },
  {
    path: '/dev-commands',""", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('路由已加 /iot-tools')

# 菜单
p = os.path.join(ROOT, 'frontend', 'src', 'layout', 'menuConfig.js')
s = io.open(p, encoding='utf-8').read()
s = s.replace("paths: ['/devices', '/device-bind', '/dev-events', '/dev-commands']",
              "paths: ['/devices', '/device-bind', '/dev-events', '/dev-commands', '/iot-tools']", 1)
s = s.replace("'/dev-commands': 63,", "'/dev-commands': 63, '/iot-tools': 64,", 1)
s = s.replace("'/dev-commands': '远程开锁/重启/校时/拉合闸（经 IoT 下发）',",
              "'/dev-commands': '远程开锁/重启/校时/拉合闸（经 IoT 下发）',\n  '/iot-tools': '验签自测、回调日志与重放',", 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('菜单已加 /iot-tools')
