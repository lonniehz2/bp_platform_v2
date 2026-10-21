<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="query.houseId" placeholder="房源ID" clearable
                  style="width:210px" @keyup.enter="load" />
        <el-input v-model="query.personId" placeholder="人员ID" clearable
                  style="width:210px" @keyup.enter="load" />
        <el-checkbox v-model="query.abnormalOnly">只看异常</el-checkbox>
        <el-button type="primary" @click="load">查询</el-button>
        <el-button @click="resetQuery">清空</el-button>
        <div class="spacer" />
        <el-button @click="openIdle">
          <el-icon><Warning /></el-icon>空置判定
        </el-button>
        <el-button @click="openRatio">不可信占比</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="openTime" label="开门时间" width="170" />
        <el-table-column prop="openTypeName" label="方式" width="100" />
        <el-table-column prop="houseId" label="房源" width="110">
          <template #default="{ row }">{{ row.houseIdName || row.houseId }}</template>
        </el-table-column>
        <el-table-column prop="personId" label="人员" width="110">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="lockId" label="门锁" width="170">
          <template #default="{ row }">{{ row.lockIdName || row.lockId }}</template>
        </el-table-column>
        <el-table-column prop="trusted" label="可信" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.trusted ? 'success' : 'warning'">
              {{ row.trusted ? '可信' : '不可信' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="abnormal" label="异常" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.abnormal" type="danger" size="small">异常</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="abnormalType" label="异常类型" width="120">
          <template #default="{ row }">{{ row.abnormalTypeLabel || enumLabel('abnormalType', row.abnormalType) }}</template>
        </el-table-column>
        <el-table-column label="轨迹" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openTrace(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }" />
    </div>

    <el-dialog v-model="traceVisible" title="行为轨迹" width="640px">
      <el-alert type="info" :closable="false" show-icon :title="trace?.summary || ''" />
      <el-timeline style="margin-top:14px;max-height:420px;overflow:auto">
        <el-timeline-item v-for="t in trace?.timeline || []" :key="t.id"
                          :timestamp="t.openTime" placement="top"
                          :type="t.abnormal ? 'danger' : 'primary'">
          {{ t.openTypeName }} — 房源 {{ t.houseId }}
          <span v-if="t.abnormal" class="muted">（{{ t.abnormalType }}）</span>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>

    <el-dialog v-model="idleVisible" title="空置判定" width="640px">
      <el-alert type="warning" :closable="false" show-icon
                title="连续无开门天数超过阈值即判定疑似空置，可作为「长期空置」违规的客观依据" />
      <el-table :data="idleList" border size="small" style="margin-top:12px">
        <el-table-column prop="houseId" label="房源" width="120">
          <template #default="{ row }">{{ row.houseIdName || row.houseId }}</template>
        </el-table-column>
        <el-table-column prop="lastOpenTime" label="最近开门" width="180" />
        <el-table-column prop="idleDays" label="连续天数" width="110" />
        <el-table-column prop="suspectIdle" label="疑似空置" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.suspectIdle ? 'danger' : 'success'">
              {{ row.suspectIdle ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="说明" min-width="200" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="ratioVisible" title="不可信开门占比（考核指标）" width="420px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="总开门次数">{{ ratio.total }}</el-descriptions-item>
        <el-descriptions-item label="不可信次数">{{ ratio.untrusted }}</el-descriptions-item>
        <el-descriptions-item label="占比">{{ ratio.untrustedRatio }}%</el-descriptions-item>
        <el-descriptions-item label="阈值">{{ ratio.threshold }}%</el-descriptions-item>
        <el-descriptions-item label="是否达标">
          <el-tag :type="ratio.pass ? 'success' : 'danger'" size="small">
            {{ ratio.pass ? '达标' : '超标' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { devApi } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({
  pageNum: 1, pageSize: 20, houseId: '', personId: '', abnormalOnly: false
})

const traceVisible = ref(false)
const trace = ref(null)
const idleVisible = ref(false)
const idleList = ref([])
const ratioVisible = ref(false)
const ratio = ref({})

async function load() {
  loading.value = true
  try {
    const data = await devApi.accessRecords({
      pageNum: query.pageNum, pageSize: query.pageSize,
      houseId: query.houseId || undefined,
      personId: query.personId || undefined,
      abnormalOnly: query.abnormalOnly || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

async function openTrace(row) {
  trace.value = row.houseId
    ? await devApi.traceByHouse(row.houseId)
    : await devApi.traceByPerson(row.personId)
  traceVisible.value = true
}

async function openIdle() {
  idleList.value = await devApi.idle({ idleDays: 30 })
  idleVisible.value = true
}

async function openRatio() {
  ratio.value = await devApi.untrustedRatio()
  ratioVisible.value = true
}

const query0 = JSON.parse(JSON.stringify(query))
function resetQuery() {
  Object.assign(query, query0)
  load()
}

onMounted(load)
</script>
