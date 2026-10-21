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
                {{ row.auditLevel }}
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
        </el-table>
        <div class="muted" style="margin-top:8px">
          系统内置 dict_type 的 tenant_id 为空；租户新增同名编码会覆盖内置项
        </div>
      </el-tab-pane>

      <el-tab-pane label="系统参数" name="config">
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
const dictTypes = ref([])
const dictType = ref('HOUSE_TYPE')
const dicts = ref([])
const configs = ref([])

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

async function loadDictTypes() {
  try { dictTypes.value = await sysApi.dictTypes() } catch (e) { dictTypes.value = [] }
}

async function loadDict() {
  if (!dictType.value) return
  dicts.value = await sysApi.dicts(dictType.value)
}

async function loadConfigs() {
  configs.value = await sysApi.configs()
}

async function load() { loadAudit(); loadDictTypes(); loadDict(); loadConfigs() }
onMounted(load)
</script>
