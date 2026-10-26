<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">系统支撑</h3>
      <div class="spacer" />
      <el-button @click="load">刷新</el-button>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="审计日志" name="audit">
        <div class="toolbar">
          <el-select v-model="auditQuery.level" placeholder="级别" clearable
                     style="width:140px" @change="loadAudit">
            <el-option label="严重" value="CRITICAL" />
            <el-option label="重要" value="IMPORTANT" />
            <el-option label="普通" value="NORMAL" />
          </el-select>
          <el-input v-model="auditQuery.operatorName" placeholder="操作人"
                    clearable style="width:150px" @keyup.enter="loadAudit" />
          <el-button type="primary" @click="loadAudit" data-testid="sys-audit-search">查询</el-button>
          <el-button @click="resetAuditQuery" data-testid="sys-audit-reset">清空</el-button>
        </div>
        <el-table :data="audits" border size="small" v-loading="loading">
          <el-table-column prop="auditTime" label="时间" width="170" />
          <el-table-column prop="auditType" label="类型" width="110">
            <template #default="{ row }">{{ row.auditTypeLabel || enumLabel('auditType', row.auditType) }}</template>
          </el-table-column>
          <el-table-column prop="auditLevel" label="级别" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.auditLevel === 'CRITICAL' ? 'danger'
                : (row.auditLevel === 'IMPORTANT' ? 'warning' : 'info')">
                {{ row.auditLevelLabel || enumLabel('auditLevel', row.auditLevel) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="action" label="动作" min-width="160" />
          <el-table-column prop="operatorName" label="操作人" width="120" />
          <el-table-column prop="targetType" label="目标方法" min-width="200"
                           show-overflow-tooltip />
        </el-table>
        <div class="muted" style="margin-top:8px">
          审计日志只追加，不提供修改与删除接口
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据字典" name="dict">
        <div class="toolbar">
          <el-select v-model="dictType" style="width:240px" @change="loadDict">
            <el-option v-for="t in dictTypes" :key="t" :label="dictTypeLabel(t)" :value="t" />
          </el-select>
        </div>
        <el-table :data="dicts" border size="small">
          <el-table-column prop="dictCode" label="编码" width="200" />
          <el-table-column prop="dictLabel" label="标签" min-width="180" />
          <el-table-column prop="sortNo" label="排序" width="90" />
          <el-table-column prop="dictStatus" label="状态" width="110">
            <template #default="{ row }">{{ row.dictStatusLabel || enumLabel('dictStatus', row.dictStatus) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.dictStatus === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleDictStatus(row)">
                {{ row.dictStatus === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="muted" style="margin-top:8px">
          系统内置 dict_type 的 tenant_id 为空；租户新增同名编码会覆盖内置项
        </div>
      </el-tab-pane>

      <el-tab-pane label="系统参数" name="config">
        <!-- IoT 对接参数（契约参数，可配置） -->
        <el-card shadow="never" style="margin-bottom:14px"
                 body-style="padding:12px 14px">
          <div class="toolbar" style="margin-bottom:10px">
            <h4 style="margin:0">IoT 对接参数</h4>
            <el-tag size="small" type="info">分组 IOT · 与 IoT 平台联调前先确认</el-tag>
            <div class="spacer" />
            <el-button size="small" @click="loadIotConfigs">重新读取</el-button>
            <el-button size="small" type="primary" :loading="iotSaving"
                       @click="saveIotAll">保存全部</el-button>
          </div>
          <el-table :data="iotRows" border size="small">
            <el-table-column prop="label" label="参数" width="230" />
            <el-table-column label="值" width="260">
              <template #default="{ row }">
                <el-select v-if="row.options" v-model="row.value" size="small"
                           style="width:100%">
                  <el-option v-for="o in row.options" :key="o.value"
                             :label="o.label" :value="o.value" />
                </el-select>
                <el-input v-else v-model="row.value" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="单位" width="90" />
            <el-table-column prop="description" label="说明" min-width="260" />
            <el-table-column label="操作" width="90">
              <template #default="{ row }">
                <el-button link type="primary" @click="saveIotOne(row)">保存</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="muted" style="margin-top:8px">
            默认值：签名 v2-hmac-sha256、时间容忍 300 秒、指令超时 10 秒 / 重试 3 次、
            授权任务超时 180 秒、心跳 60 秒 / 离线 180 秒、表计上报 每日。
            修改后立即生效，无需重启。
          </div>
        </el-card>

        <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="configGroup" placeholder="参数分组，如 SYSTEM / FINANCE"
                    clearable style="width:260px" data-testid="sys-config-group"
                    @keyup.enter="loadConfigs" />
          <el-button type="primary" @click="loadConfigs" data-testid="sys-config-search">查询</el-button>
          <el-button @click="resetConfigQuery" data-testid="sys-config-reset">清空</el-button>
        </div>
        <el-table :data="configs" border size="small">
          <el-table-column prop="configKey" label="参数键" width="320" />
          <el-table-column prop="configValue" label="当前值" width="140" />
          <el-table-column prop="valueType" label="类型" width="100">
            <template #default="{ row }">{{ row.valueTypeLabel || enumLabel('valueType', row.valueType) }}</template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="240" />
        </el-table>
        <div class="muted" style="margin-top:8px">
          政策参数（公示天数/禁申年限/过渡期/加价倍率）改这里即生效，无需改代码
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { enumLabel, dictTypeLabel } from '@/constants/enums'
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sysApi } from '@/api/modules'
import req from '@/api/request'
import { ElMessage } from 'element-plus'

const TABS = ['audit', 'dict', 'config']
const route = useRoute()
const router = useRouter()
const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : 'audit')
watch(() => route.params.tab, (v) => {
  const t = TABS.includes(v) ? v : 'audit'
  if (t !== tab.value) tab.value = t
})
watch(tab, (v) => {
  if (route.params.tab !== v) router.replace('/sys/' + v)
})
const loading = ref(false)
const audits = ref([])
const auditQuery = reactive({ level: '', operatorName: '' })
/** 清空审计筛选并重查 */
function resetAuditQuery() {
  auditQuery.level = ''
  auditQuery.operatorName = ''
  loadAudit()
}
const dictTypes = ref([])
const dictType = ref('HOUSE_TYPE')
const dicts = ref([])
const configs = ref([])
/** 系统参数分组筛选（后端 sysApi.configs(group) 支持） */
const configGroup = ref('')
function resetConfigQuery() {
  configGroup.value = ''
  loadConfigs()
}

async function loadAudit() {
  loading.value = true
  try {
    const d = await sysApi.auditLogs({
      pageNum: 1, pageSize: 50,
      level: auditQuery.level || undefined,
      operatorName: auditQuery.operatorName || undefined
    })
    audits.value = d.rows || []
  } finally { loading.value = false }
}


/** 字典项启用 / 停用 */
async function toggleDictStatus(row) {
  const next = row.dictStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/sys/dicts/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    loadDict()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

async function loadDictTypes() {
  try { dictTypes.value = await sysApi.dictTypes() } catch (e) { dictTypes.value = [] }
}

async function loadDict() {
  if (!dictType.value) return
  // 管理页需要看到已停用项，否则停用后无法再启用
  dicts.value = await req.get('/sys/dicts/' + dictType.value,
    { params: { includeDisabled: true } })
}

async function loadConfigs() {
  configs.value = await sysApi.configs(configGroup.value || undefined)
}

async function load() { loadAudit(); loadDictTypes(); loadDict(); loadConfigs() }
onMounted(() => {
  load()
  loadIotConfigs()
})
// ---------------- IoT 对接参数（分组 IOT，可配置） ----------------
const IOT_META = [
  { key: 'iot.callback.signAlgorithm', label: '回调签名算法', unit: '',
    options: [{ label: 'v2-hmac-sha256（推荐）', value: 'v2-hmac-sha256' },
      { label: 'legacy-md5-aes（旧协议）', value: 'legacy-md5-aes' }],
    description: '回调验签使用的算法' },
  { key: 'iot.callback.timestampToleranceSeconds', label: '时间戳容忍窗口', unit: '秒',
    description: '超出该窗口的回调视为重放，直接拒绝' },
  { key: 'iot.callback.nonceCacheMinutes', label: 'Nonce 缓存时长', unit: '分钟',
    description: '防重放窗口内相同 Nonce 只接受一次' },
  { key: 'iot.callback.batchLimit', label: '单次批量上限', unit: '条',
    description: '回调/批量接口单次最大条数' },
  { key: 'iot.callback.qps', label: '回调限流', unit: '次/秒',
    description: '0 表示不限流' },
  { key: 'iot.command.timeoutSeconds', label: '指令超时', unit: '秒',
    description: '超时转 TIMEOUT 并按重试次数重发' },
  { key: 'iot.command.maxRetry', label: '指令最大重试', unit: '次',
    description: '超过后置 FAILED 并告警' },
  { key: 'iot.grantTask.timeoutSeconds', label: '授权任务超时', unit: '秒',
    description: '授权下发未回执的超时判定' },
  { key: 'iot.heartbeat.intervalSeconds', label: '心跳间隔', unit: '秒',
    description: 'IoT 上报心跳的参考频率（告知 IoT 方）' },
  { key: 'iot.offline.thresholdSeconds', label: '离线判定阈值', unit: '秒',
    description: '超过该时长无心跳即判离线并产生事件' },
  { key: 'iot.meter.reportPeriod', label: '表计上报周期', unit: '',
    description: '如 ELEC:DAILY,WATER:DAILY（电表/水表均为每日）' },
  { key: 'iot.meter.switch.delayMinutes', label: '拉闸延迟', unit: '分钟',
    description: '延迟执行窗口内可撤销' }
]

const iotRows = ref(IOT_META.map((m) => ({ ...m, value: '' })))
const iotSaving = ref(false)

async function loadIotConfigs() {
  try {
    const list = await sysApi.configs('IOT') || []
    const map = {}
    list.forEach((x) => { map[x.configKey] = x.configValue })
    iotRows.value = IOT_META.map((m) => ({ ...m, value: map[m.key] ?? '' }))
  } catch (e) {
    iotRows.value = IOT_META.map((m) => ({ ...m, value: '' }))
  }
}

async function saveIotOne(row) {
  if (row.value === '' || row.value === null || row.value === undefined) {
    ElMessage.warning('『' + row.label + '』不能为空')
    return
  }
  await sysApi.setConfig({ key: row.key, value: String(row.value), description: row.description })
  ElMessage.success('已保存：' + row.label)
}

async function saveIotAll() {
  iotSaving.value = true
  try {
    for (const row of iotRows.value) {
      if (row.value === '' || row.value === null || row.value === undefined) continue
      await sysApi.setConfig({ key: row.key, value: String(row.value), description: row.description })
    }
    ElMessage.success('IoT 对接参数已全部保存')
    loadIotConfigs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally { iotSaving.value = false }
}

</script>
