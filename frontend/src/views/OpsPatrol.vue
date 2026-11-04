<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 style="margin:0">{{ t('opsPatrol.title') }}</h2>
      <el-tag size="small" type="info">{{ t('opsPatrol.subtitle') }}</el-tag>
      <div class="spacer" />
      <el-button @click="goSettings">{{ t('opsPatrol.editSettings') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon :title="t('opsPatrol.hint')"
              style="margin:12px 0" />

    <el-row :gutter="12">
      <el-col :span="12">
        <el-card shadow="never">
          <div class="toolbar">
            <h4 style="margin:0">{{ t('sysAdminX.patrolTitle') }}</h4>
            <div class="spacer" />
            <el-button type="primary" :loading="patrolRunning" @click="runPatrol">
              {{ t('opsPatrol.runPatrol') }}
            </el-button>
          </div>
          <el-table :data="patrolRows" border size="small" style="margin-top:10px">
            <el-table-column prop="label" :label="t('sys.param')" />
            <el-table-column prop="value" :label="t('sys.value')" width="120" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <div class="toolbar">
            <h4 style="margin:0">{{ t('sysAdminX.arrearsTitle') }}</h4>
            <div class="spacer" />
            <el-button type="warning" :loading="arrearsRunning" @click="runArrears">
              {{ t('opsPatrol.runArrears') }}
            </el-button>
          </div>
          <el-table :data="arrearsRows" border size="small" style="margin-top:10px">
            <el-table-column prop="label" :label="t('sys.param')" />
            <el-table-column prop="value" :label="t('sys.value')" width="120" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="lastResult" shadow="never" style="margin-top:12px">
      <div class="muted">{{ t('opsPatrol.lastResult') }}</div>
      <pre class="raw" style="white-space:pre-wrap">{{ lastResult }}</pre>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { sysApi } from '@/api/modules'

const { t } = useI18n()
const router = useRouter()
const patrolRows = ref([])
const arrearsRows = ref([])
const patrolRunning = ref(false)
const arrearsRunning = ref(false)
const lastResult = ref('')

const PATROL_META = [
  ['patrol.enabled', 'sysAdminX.patrolEnabled', 'true'],
  ['patrol.noOpenDays', 'sysAdminX.noOpenDays', '30'],
  ['patrol.lowBatteryPercent', 'sysAdminX.lowBattery', '20'],
  ['patrol.contractExpireDays', 'sysAdminX.expireDays', '30'],
  ['patrol.deviceOfflineHours', 'sysAdminX.offlineHours', '24'],
  ['patrol.idleDays', 'sysAdminX.idleDays', '30']
]
const ARREARS_META = [
  ['arrears.autoFreezeEnabled', 'sysAdminX.autoFreeze', 'false'],
  ['arrears.autoFreezeDays', 'sysAdminX.autoFreezeDays', '30'],
  ['arrears.autoRestoreEnabled', 'sysAdminX.autoRestore', 'true']
]

function displayValue(v) {
  if (v === 'true') return t('opsPatrol.enabled')
  if (v === 'false') return t('opsPatrol.disabled')
  return v
}

async function loadSettings() {
  try {
    const list = await sysApi.configs() || []
    const map = {}
    list.forEach((x) => { map[x.configKey] = x.configValue })
    patrolRows.value = PATROL_META.map(([key, label, def]) => ({ label: t(label), value: displayValue(map[key] ?? def) }))
    arrearsRows.value = ARREARS_META.map(([key, label, def]) => ({ label: t(label), value: displayValue(map[key] ?? def) }))
  } catch (e) {
    patrolRows.value = []
    arrearsRows.value = []
  }
}

async function runPatrol() {
  patrolRunning.value = true
  try {
    const r = await req.post('/ops/patrol/run')
    lastResult.value = JSON.stringify(r)
    ElMessage.success(t('opsPatrol.done'))
  } finally { patrolRunning.value = false }
}

async function runArrears() {
  arrearsRunning.value = true
  try {
    const r = await req.post('/ops/arrears/run')
    lastResult.value = JSON.stringify(r)
    ElMessage.success(t('opsPatrol.done'))
  } finally { arrearsRunning.value = false }
}

function goSettings() {
  router.push('/sys/config')
}

onMounted(loadSettings)
</script>
