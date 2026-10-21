# -*- coding: utf-8 -*-
"""前端补全：4 个缺失页面（工单/告警规则/钥匙包/授权对账）+ 路由 + 分包"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['src/views/WorkOrders.vue'] = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">工单与维保</h3>
      <el-select v-model="query.orderStatus" placeholder="状态" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
      </el-select>
      <div class="spacer" />
      <el-button type="primary" @click="reload">刷新</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="orderNo" label="工单号" width="170" />
      <el-table-column prop="orderType" label="类型" width="110" />
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.priority === 'URGENT' ? 'danger' : 'info'">
            {{ row.priority }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="orderStatus" label="状态" width="120" />
      <el-table-column prop="slaOverdue" label="SLA" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.slaOverdue" type="danger" size="small">超时</el-tag>
          <span v-else class="muted">正常</span>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="170" />
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="act(row, 'accept')">接单</el-button>
          <el-button link type="primary" @click="act(row, 'start')">开始</el-button>
          <el-button link type="success" @click="finish(row)">完成</el-button>
          <el-button link @click="logs(row)">日志</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <el-drawer v-model="logVisible" title="工单日志" size="460px">
      <el-timeline>
        <el-timeline-item v-for="l in logList" :key="l.id" :timestamp="l.createTime">
          {{ l.action }} — {{ l.operatorName }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!logList.length" description="暂无日志" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { workOrderApi } from '@/api/modules'

const statuses = ['PENDING', 'ASSIGNED', 'ACCEPTED', 'PROCESSING', 'FINISHED',
  'CLOSED', 'CANCELLED']
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, orderStatus: '' })
const logVisible = ref(false)
const logList = ref([])

async function load() {
  loading.value = true
  try {
    const data = await workOrderApi.page({
      pageNum: query.pageNum, pageSize: query.pageSize,
      orderStatus: query.orderStatus || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}
function reload() { query.pageNum = 1; load() }

async function act(row, action) {
  await workOrderApi[action](row.id)
  ElMessage.success('操作成功')
  load()
}
async function finish(row) {
  await workOrderApi.finish(row.id, { finishRemark: '现场处理完成' })
  ElMessage.success('工单已完成')
  load()
}
async function logs(row) {
  logList.value = await workOrderApi.logs(row.id)
  logVisible.value = true
}
onMounted(load)
</script>
'''

F['src/views/Alerts.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">告警与规则引擎</h3>
        <el-select v-model="domain" style="width:140px" @change="loadRulesets">
          <el-option label="预警" value="ALERT" />
          <el-option label="资格" value="QUALIFY" />
          <el-option label="计费" value="BILLING" />
        </el-select>
        <div class="spacer" />
        <el-button type="primary" @click="load">刷新</el-button>
      </div>

      <el-tabs v-model="tab">
        <el-tab-pane label="告警列表" name="alerts">
          <el-table :data="alerts" v-loading="loading" border size="small">
            <el-table-column prop="alertNo" label="告警号" width="170" />
            <el-table-column prop="alertTitle" label="标题" min-width="200" />
            <el-table-column prop="alertLevel" label="级别" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="row.alertLevel === 'URGENT'
                  ? 'danger' : (row.alertLevel === 'IMPORTANT' ? 'warning' : 'info')">
                  {{ row.alertLevel }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="alertStatus" label="状态" width="110" />
            <el-table-column prop="createTime" label="时间" width="170" />
            <el-table-column label="操作" width="130">
              <template #default="{ row }">
                <el-button link type="primary" @click="toWorkOrder(row)">转工单</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="规则集与阈值" name="rules">
          <div class="toolbar">
            <el-select v-model="rulesetId" placeholder="选择规则集"
                       style="width:280px" @change="loadRules">
              <el-option v-for="r in rulesets" :key="r.id"
                         :label="`${r.rulesetCode} v${r.rulesetVersion}（${r.rulesetStatus}）`"
                         :value="r.id" />
            </el-select>
            <el-button :disabled="!rulesetId" @click="publish">发布</el-button>
            <span class="muted">阈值可改，改完新建版本再发布</span>
          </div>
          <el-table :data="rules" border size="small">
            <el-table-column prop="ruleCode" label="规则编码" width="170" />
            <el-table-column prop="ruleName" label="名称" min-width="160" />
            <el-table-column prop="thresholdJson" label="阈值配置" min-width="260"
                             show-overflow-tooltip />
            <el-table-column prop="severity" label="级别" width="100" />
            <el-table-column prop="ruleStatus" label="状态" width="100" />
          </el-table>
          <div class="muted" style="margin-top:10px">
            命中统计：{{ stats.hits }} / {{ stats.executions }} 次（{{ stats.hitRate }}%）
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { alertApi, ruleApi } from '@/api/modules'

const tab = ref('alerts')
const domain = ref('ALERT')
const loading = ref(false)
const alerts = ref([])
const rulesets = ref([])
const rulesetId = ref(null)
const rules = ref([])
const stats = ref({})

async function loadAlerts() {
  loading.value = true
  try {
    const d = await alertApi.page({ pageNum: 1, pageSize: 50 })
    alerts.value = d.rows || []
  } finally { loading.value = false }
}

async function loadRulesets() {
  rulesets.value = await ruleApi.rulesets({ domain: domain.value })
}

async function loadRules() {
  if (!rulesetId.value) return
  rules.value = await ruleApi.rules(rulesetId.value)
  stats.value = await ruleApi.stats(rulesetId.value)
}

async function publish() {
  await ruleApi.publish(rulesetId.value)
  ElMessage.success('规则集已发布（同编码旧版本自动停用）')
  loadRulesets()
}

async function toWorkOrder(row) {
  await alertApi.toWorkOrder(row.id, {})
  ElMessage.success('已转为工单')
  loadAlerts()
}

function load() { loadAlerts(); loadRulesets(); loadRules() }
onMounted(load)
</script>
'''

F['src/views/Keyring.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">钥匙包（四级权限）</h3>
        <el-input v-model.number="personId" placeholder="保障对象ID"
                  style="width:180px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <div class="spacer" />
        <el-button type="success" :disabled="!personId" @click="openAdd">
          新增钥匙
        </el-button>
      </div>

      <div v-if="summary.total !== undefined" class="stat-grid"
           style="margin-bottom:14px">
        <div class="stat-card"><div class="label">钥匙总数</div>
          <div class="value">{{ summary.total }}</div></div>
        <div class="stat-card ok"><div class="label">实名介质</div>
          <div class="value">{{ summary.realCount }}</div></div>
        <div class="stat-card warn"><div class="label">弱安全介质</div>
          <div class="value">{{ summary.weakCount }}</div></div>
        <div class="stat-card" :class="summary.meetsStrongSecurity ? 'ok' : 'danger'">
          <div class="label">强安全要求</div>
          <div class="value">{{ summary.meetsStrongSecurity ? '满足' : '不满足' }}</div>
        </div>
      </div>

      <el-alert v-if="summary.advice" :closable="false" show-icon
                :type="summary.meetsStrongSecurity ? 'success' : 'warning'"
                :title="summary.advice" style="margin-bottom:12px" />

      <el-table :data="keys" v-loading="loading" border size="small">
        <el-table-column prop="keyTypeLabel" label="类型" width="110" />
        <el-table-column prop="keyClassLabel" label="分类（四分类）" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.real ? 'success' : 'warning'">
              {{ row.keyClassLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="keyAlias" label="别名" width="140" />
        <el-table-column prop="real" label="实名" width="90">
          <template #default="{ row }">{{ row.real ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column prop="keySource" label="来源" width="120" />
        <el-table-column prop="expireTime" label="有效期" width="170" />
        <el-table-column prop="keyStatus" label="状态" width="100" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" @click="setStatus(row, 'FROZEN')">冻结</el-button>
            <el-button link type="success" @click="setStatus(row, 'ACTIVE')">启用</el-button>
            <el-button link type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !keys.length" description="该人员暂无钥匙" />
    </div>

    <el-dialog v-model="addVisible" title="新增钥匙" width="520px">
      <el-alert type="info" :closable="false" show-icon
                title="分类由「类型 + 核验方式 + 来源」自动推导：只有实名介质可开大门，非实名必须设有效期" />
      <el-form :model="form" label-width="100px" style="margin-top:12px">
        <el-form-item label="钥匙类型">
          <el-select v-model="form.keyType" style="width:100%">
            <el-option label="人脸" value="FACE" />
            <el-option label="指纹" value="FINGERPRINT" />
            <el-option label="掌静脉" value="PALM_VEIN" />
            <el-option label="密码" value="PASSWORD" />
            <el-option label="卡片" value="CARD" />
            <el-option label="身份证" value="IDCARD" />
          </el-select>
        </el-form-item>
        <el-form-item label="别名">
          <el-input v-model="form.keyAlias" placeholder="如 右手大拇指" />
        </el-form-item>
        <el-form-item label="介质值">
          <el-input v-model="form.channelValue" placeholder="卡号/密码/模板（加密存储）" />
        </el-form-item>
        <el-form-item label="核验方式">
          <el-select v-model="form.verifyWay" clearable style="width:100%">
            <el-option label="人证核验" value="FACE_VERIFY" />
            <el-option label="组织担保" value="ORG_VERIFY" />
            <el-option label="无" value="NONE" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="form.keySource" style="width:100%">
            <el-option label="后台录入" value="ADMIN" />
            <el-option label="自助录入" value="SELF_APP" />
            <el-option label="身份证下发" value="IDCARD" />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期">
          <el-input v-model="form.expireTime" placeholder="yyyy-MM-dd HH:mm:ss（弱安全必填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { keyringApi } from '@/api/modules'

const personId = ref(null)
const loading = ref(false)
const saving = ref(false)
const keys = ref([])
const summary = ref({})
const addVisible = ref(false)
const form = reactive({
  keyType: 'FACE', keyAlias: '', channelValue: '', verifyWay: 'FACE_VERIFY',
  keySource: 'ADMIN', expireTime: ''
})

async function load() {
  if (!personId.value) { ElMessage.warning('请输入保障对象ID'); return }
  loading.value = true
  try {
    keys.value = await keyringApi.byPerson(personId.value)
    summary.value = await keyringApi.summary(personId.value)
  } finally { loading.value = false }
}

function openAdd() {
  Object.assign(form, { keyType: 'FACE', keyAlias: '', channelValue: '',
    verifyWay: 'FACE_VERIFY', keySource: 'ADMIN', expireTime: '' })
  addVisible.value = true
}

async function save() {
  saving.value = true
  try {
    await keyringApi.add({ ...form, personId: personId.value })
    ElMessage.success('钥匙已入包')
    addVisible.value = false
    load()
  } finally { saving.value = false }
}

async function setStatus(row, status) {
  await keyringApi.setStatus(row.id, status)
  ElMessage.success('状态已变更')
  load()
}

async function remove(row) {
  await ElMessageBox.confirm('确认删除该钥匙？删除后不可恢复', '提示',
    { type: 'warning' })
  await keyringApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(() => { /* 等用户输入人员ID */ })
</script>
'''

F['src/views/Grants.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">授权与对账</h3>
        <el-tag size="small" :type="stats.riskLevel === 'HIGH' ? 'danger'
          : (stats.riskLevel === 'MEDIUM' ? 'warning' : 'success')">
          风险 {{ stats.riskLevel || '-' }}
        </el-tag>
        <span class="muted">待处置 {{ stats.pending ?? 0 }} 条</span>
        <div class="spacer" />
        <el-input v-model="lockId" placeholder="门锁ID（可空=全部）"
                  style="width:200px" />
        <el-button type="primary" :loading="running" @click="runReconcile">
          执行对账
        </el-button>
      </div>

      <el-alert type="info" :closable="false" show-icon
                title="LOCAL_MISSING = 本地有效但设备未下发（住户刷不开门）；IOT_EXTRA = 已撤销但设备仍存在（安全风险）"
                style="margin-bottom:12px" />

      <el-table :data="diffs" v-loading="loading" border size="small">
        <el-table-column prop="diffType" label="差异类型" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.diffType === 'IOT_EXTRA' ? 'danger' : 'warning'">
              {{ row.diffType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lockId" label="门锁" width="170" />
        <el-table-column prop="personId" label="人员" width="120" />
        <el-table-column prop="localValue" label="本地值" min-width="200"
                         show-overflow-tooltip />
        <el-table-column prop="iotValue" label="IoT 值" min-width="180"
                         show-overflow-tooltip />
        <el-table-column prop="handleStatus" label="处置状态" width="110" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
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
                     @current-change="(p) => { query.pageNum = p; load() }" />
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">授权审计（只追加，不可改删）</h4>
      <el-table :data="audits" border size="small">
        <el-table-column prop="bizType" label="类型" width="120" />
        <el-table-column prop="personId" label="人员" width="120" />
        <el-table-column prop="operatorName" label="操作人" width="120" />
        <el-table-column prop="reason" label="原因" min-width="200" />
        <el-table-column prop="result" label="结果" width="100" />
        <el-table-column prop="createTime" label="时间" width="170" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { grantApi } from '@/api/modules'

const loading = ref(false)
const running = ref(false)
const diffs = ref([])
const total = ref(0)
const stats = ref({})
const audits = ref([])
const lockId = ref('')
const query = reactive({ pageNum: 1, pageSize: 20 })

async function load() {
  loading.value = true
  try {
    const d = await grantApi.diffs({ ...query })
    diffs.value = d.rows || []
    total.value = Number(d.total || 0)
    stats.value = await grantApi.reconcileStats()
    const a = await grantApi.auditLogs({ pageNum: 1, pageSize: 10 })
    audits.value = a.rows || []
  } finally { loading.value = false }
}

async function runReconcile() {
  running.value = true
  try {
    const r = await grantApi.reconcileRun(lockId.value || undefined)
    ElMessage.success(`对账完成：差异 ${r.diffRecorded} 条（${r.conclusion}）`)
    load()
  } finally { running.value = false }
}

async function handle(row, action) {
  await grantApi.handleDiff(row.id, { action, remark: '页面处置' })
  ElMessage.success('已处置')
  load()
}

onMounted(load)
</script>
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个页面' % count)
