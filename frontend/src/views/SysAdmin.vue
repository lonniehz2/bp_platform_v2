<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('sys.title') }}</h3>
      <div class="spacer" />
      <el-button @click="load">{{ t('sys.refresh') }}</el-button>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane :label="t('sys.auditTab')" name="audit">
        <div class="toolbar">
          <el-select v-model="auditQuery.level" :placeholder="t('sys.level')" clearable
                     style="width:140px" @change="loadAudit">
            <el-option :label="t('sys.critical')" value="CRITICAL" />
            <el-option :label="t('sys.important')" value="IMPORTANT" />
            <el-option :label="t('sys.normal')" value="NORMAL" />
          </el-select>
          <el-input v-model="auditQuery.operatorName" :placeholder="t('sys.operator')"
                    clearable style="width:150px" @keyup.enter="loadAudit" />
          <el-button type="primary" @click="loadAudit" data-testid="sys-audit-search">{{ t('sys.search') }}</el-button>
          <el-button @click="resetAuditQuery" data-testid="sys-audit-reset">{{ t('sys.reset') }}</el-button>
        </div>
        <el-table :data="audits" border size="small" v-loading="loading">
          <el-table-column prop="auditTime" :label="t('sys.time')" width="170" />
          <el-table-column prop="auditType" :label="t('sys.type')" width="110">
            <template #default="{ row }">{{ row.auditTypeLabel || enumLabel('auditType', row.auditType) }}</template>
          </el-table-column>
          <el-table-column prop="auditLevel" :label="t('sys.levelCol')" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.auditLevel === 'CRITICAL' ? 'danger'
                : (row.auditLevel === 'IMPORTANT' ? 'warning' : 'info')">
                {{ row.auditLevelLabel || enumLabel('auditLevel', row.auditLevel) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="action" :label="t('sys.action')" min-width="160" />
          <el-table-column prop="operatorName" :label="t('sys.operatorCol')" width="120" />
          <el-table-column prop="targetType" :label="t('sys.target')" min-width="200"
                           show-overflow-tooltip />
        </el-table>
        <div class="muted" style="margin-top:8px">
          {{ t('sysAdminX.auditAppendOnly') }}
        </div>
      </el-tab-pane>

      <el-tab-pane :label="t('sys.dictTab')" name="dict">
        <div class="toolbar">
          <el-select v-model="dictType" style="width:240px" @change="loadDict">
            <el-option v-for="t in dictTypes" :key="t" :label="dictTypeLabel(t)" :value="t" />
          </el-select>
        </div>
        <el-table :data="dicts" border size="small">
          <el-table-column prop="dictCode" :label="t('sys.code')" width="200" />
          <el-table-column prop="dictLabel" :label="t('sys.label')" min-width="180" />
          <el-table-column prop="sortNo" :label="t('sys.sort')" width="90" />
          <el-table-column prop="dictStatus" :label="t('sys.status')" width="110">
            <template #default="{ row }">{{ row.dictStatusLabel || enumLabel('dictStatus', row.dictStatus) }}</template>
          </el-table-column>
          <el-table-column :label="t('sys.actions')" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.dictStatus === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleDictStatus(row)">
                {{ row.dictStatus === 'ENABLED' ? t('sys.disable') : t('sys.enable') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="muted" style="margin-top:8px">
          {{ t('sysAdminX.dictBuiltin') }}
        </div>
      </el-tab-pane>

      <el-tab-pane :label="t('sys.configTab')" name="config">
        <!-- IoT 对接参数（契约参数，可配置） -->
        <el-card shadow="never" style="margin-bottom:14px"
                 body-style="padding:12px 14px">
          <div class="toolbar" style="margin-bottom:10px">
            <h4 style="margin:0">{{ t('sysAdminX.iotTitle') }}</h4>
            <el-tag size="small" type="info">{{ t('sysAdminX.iotGroup') }}</el-tag>
            <div class="spacer" />
            <el-button size="small" @click="loadIotConfigs">{{ t('sys.reloadIot') }}</el-button>
            <el-button size="small" type="primary" :loading="iotSaving"
                       @click="saveIotAll">{{ t('sysAdminX.saveAll') }}</el-button>
          </div>
          <el-table :data="iotRows" border size="small">
            <el-table-column prop="label" :label="t('sys.param')" width="230" />
            <el-table-column :label="t('sys.value')" width="260">
              <template #default="{ row }">
                <el-select v-if="row.options" v-model="row.value" size="small"
                           style="width:100%">
                  <el-option v-for="o in row.options" :key="o.value"
                             :label="o.label" :value="o.value" />
                </el-select>
                <el-input v-else v-model="row.value" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="unit" :label="t('sys.unit')" width="90" />
            <el-table-column prop="description" :label="t('sys.desc')" min-width="260" />
            <el-table-column :label="t('sys.actions')" width="90">
              <template #default="{ row }">
                <el-button link type="primary" @click="saveIotOne(row)">{{ t('sys.save') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="muted" style="margin-top:8px">
            {{ t('sysAdminX.iotDefaults') }} {{ t('sysAdminX.iotEffective') }}
          </div>
        </el-card>

        <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="configGroup" :placeholder="t('sys.groupHint')"
                    clearable style="width:260px" data-testid="sys-config-group"
                    @keyup.enter="loadConfigs" />
          <el-button type="primary" @click="loadConfigs" data-testid="sys-config-search">{{ t('sys.search') }}</el-button>
          <el-button @click="resetConfigQuery" data-testid="sys-config-reset">{{ t('sys.reset') }}</el-button>
        </div>
        <el-table :data="configs" border size="small">
          <el-table-column prop="configKey" :label="t('sys.configKey')" width="320" />
          <el-table-column prop="configValue" :label="t('sys.currentValue')" width="140" />
          <el-table-column prop="valueType" :label="t('sys.type')" width="100">
            <template #default="{ row }">{{ row.valueTypeLabel || enumLabel('valueType', row.valueType) }}</template>
          </el-table-column>
          <el-table-column prop="description" :label="t('sys.desc')" min-width="240" />
          <el-table-column :label="t('common.operation')" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" data-testid="sys-config-edit"
                         @click="openConfigEdit(row)">修改</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="muted" style="margin-top:8px">
          政策参数（公示天数/禁申年限/过渡期/加价倍率）改这里即生效，无需改代码
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 修改系统参数 -->
    <el-dialog v-model="configEditVisible" :title="t('sys.configEditTitle')" width="560px">
      <el-form :model="configForm" label-width="90px">
        <el-form-item :label="t('sys.configKey')">
          <el-input v-model="configForm.configKey" disabled />
        </el-form-item>
        <el-form-item :label="t('sys.currentValue')">
          <el-input v-model="configForm.oldValue" disabled />
        </el-form-item>
        <el-form-item :label="t('sys.newValue')" required>
          <el-input v-model="configForm.value" data-testid="sys-config-value"
                    :placeholder="t('sys.newValueHint')" />
        </el-form-item>
        <el-form-item :label="t('sys.desc')">
          <el-input v-model="configForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <el-alert type="warning" :closable="false" show-icon
                title="修改后立即生效；公示天数这类政策参数会影响后续业务校验，请谨慎调整。" />
      <template #footer>
        <el-button @click="configEditVisible = false">{{ t('sys.cancel') }}</el-button>
        <el-button type="primary" :loading="configSaving" @click="saveConfig">{{ t('sys.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { enumLabel, dictTypeLabel } from '@/constants/enums'
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sysApi } from '@/api/modules'
import req from '@/api/request'
import { ElMessage } from 'element-plus'

const { t } = useI18n()
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
const configEditVisible = ref(false)
const configSaving = ref(false)
const configForm = reactive({ configKey: '', oldValue: '', value: '', description: '' })

function openConfigEdit(row) {
  configForm.configKey = row.configKey
  configForm.oldValue = row.configValue
  configForm.value = row.configValue
  configForm.description = row.description || ''
  configEditVisible.value = true
}

async function saveConfig() {
  if (!configForm.value) { ElMessage.warning('请填写新值'); return }
  configSaving.value = true
  try {
    await sysApi.setConfig({
      key: configForm.configKey,
      value: String(configForm.value),
      description: configForm.description || undefined
    })
    ElMessage.success('已保存，新值立即生效')
    configEditVisible.value = false
    loadConfigs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally { configSaving.value = false }
}
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
  { key: 'iot.callback.signAlgorithm', label: t('sysAdminX.signAlgo'), unit: '',
    options: [{ label: t('sysAdminX.v2'), value: 'v2-hmac-sha256' },
      { label: t('sysAdminX.legacy'), value: 'legacy-md5-aes' }],
    description: t('sysAdminX.signAlgoDesc') },
  { key: 'iot.callback.timestampToleranceSeconds', label: t('sysAdminX.tsWindow'), unit: t('sysAdminX.seconds'),
    description: t('sysAdminX.tsWindowDesc') },
  { key: 'iot.callback.nonceCacheMinutes', label: t('sysAdminX.nonceCache'), unit: t('sysAdminX.minutes'),
    description: t('sysAdminX.nonceCacheDesc') },
  { key: 'iot.callback.batchLimit', label: t('sysAdminX.batchLimit'), unit: t('sysAdminX.items'),
    description: t('sysAdminX.batchLimitDesc') },
  { key: 'iot.callback.qps', label: t('sysAdminX.qps'), unit: t('sysAdminX.perSecond'),
    description: t('sysAdminX.qpsDesc') },
  { key: 'iot.command.timeoutSeconds', label: t('sysAdminX.cmdTimeout'), unit: t('sysAdminX.seconds'),
    description: t('sysAdminX.cmdTimeoutDesc') },
  { key: 'iot.command.maxRetry', label: t('sysAdminX.maxRetry'), unit: t('sysAdminX.times'),
    description: t('sysAdminX.maxRetryDesc') },
  { key: 'iot.grantTask.timeoutSeconds', label: t('sysAdminX.grantTimeout'), unit: t('sysAdminX.seconds'),
    description: t('sysAdminX.grantTimeoutDesc') },
  { key: 'iot.heartbeat.intervalSeconds', label: t('sysAdminX.heartbeat'), unit: t('sysAdminX.seconds'),
    description: t('sysAdminX.heartbeatDesc') },
  { key: 'iot.offline.thresholdSeconds', label: t('sysAdminX.offlineThreshold'), unit: t('sysAdminX.seconds'),
    description: t('sysAdminX.offlineThresholdDesc') },
  { key: 'iot.meter.reportPeriod', label: t('sysAdminX.meterPeriod'), unit: '',
    description: t('sysAdminX.meterPeriodDesc') },
  { key: 'iot.meter.switch.delayMinutes', label: t('sysAdminX.switchDelay'), unit: t('sysAdminX.minutes'),
    description: t('sysAdminX.switchDelayDesc') }
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
