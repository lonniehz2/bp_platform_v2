<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <HouseSelect v-model="query.houseId" width="210px" testid="house-select" />
        <PersonPicker v-model="query.personId" width="240px" testid="person-picker" />
        <el-select v-model="query.openType" clearable :placeholder="t('access.openType')"
                   style="width:130px">
          <el-option v-for="x in ['CARD','FACE','PASSWORD','QRCODE']" :key="x"
                     :label="enumLabel('openType', x)" :value="x" />
        </el-select>
        <el-checkbox v-model="query.abnormalOnly">{{ t('misc2.abnormalOnly') }}</el-checkbox>
        <el-button type="primary" @click="load">{{ t('access.search') }}</el-button>
        <el-button @click="resetQuery">{{ t('access.reset') }}</el-button>
        <div class="spacer" />
        <el-button @click="openIdle">
          <el-icon><Warning /></el-icon>{{ t('access.idle') }}
        </el-button>
        <el-button @click="openRatio">{{ t('access.ratio') }}</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('misc.emptyDefault')">
        <el-table-column prop="openTime" :label="t('access.openTime')" width="170" />
        <el-table-column prop="openTypeName" :label="t('access.method')" width="100" />
        <el-table-column prop="houseId" :label="t('access.house')" width="110">
          <template #default="{ row }">{{ row.houseIdName || row.houseId }}</template>
        </el-table-column>
        <el-table-column :label="t('access.person')" width="150">
          <template #default="{ row }">
            <span v-if="row.personIdName">{{ row.personIdName }}</span>
            <span v-else-if="row.targetUserMobile" class="muted">
              {{ row.targetUserMobile }}{{ t('misc2.unmatchedPerson') }}
            </span>
            <span v-else class="muted">{{ t('misc2.unmatched') }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lockId" :label="t('access.lock')" width="170">
          <template #default="{ row }">{{ row.lockIdName || row.lockId }}</template>
        </el-table-column>
        <el-table-column prop="trusted" :label="t('access.trusted')" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.trusted ? 'success' : 'warning'">
              {{ row.trusted ? t('misc2.trusted') : t('misc2.untrusted') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="abnormal" :label="t('access.abnormal')" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.abnormal" type="danger" size="small">{{ t('misc2.abnormal') }}</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="abnormalType" :label="t('access.abnormalType')" width="120">
          <template #default="{ row }">{{ row.abnormalTypeLabel || enumLabel('abnormalType', row.abnormalType) }}</template>
        </el-table-column>
        <el-table-column :label="t('access.trace')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openTrace(row)">{{ t('access.view') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                     :total="+total || 0" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />
    </div>

    <el-dialog v-model="traceVisible" :title="t('access.traceTitle')" width="640px">
      <el-alert type="info" :closable="false" show-icon :title="traceText" />
      <el-timeline style="margin-top:14px;max-height:420px;overflow:auto">
        <el-timeline-item v-for="t in trace?.timeline || []" :key="t.id"
                          :timestamp="t.openTime" placement="top"
                          :type="t.abnormal ? 'danger' : 'primary'">
          {{ t.openTypeName }} — {{ t('access.housePrefix', { id: t.houseId }) }}
          <span v-if="t.abnormal" class="muted">({{ t.abnormalType }})</span>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>

    <el-dialog v-model="idleVisible" :title="t('access.idleTitle')" width="640px">
      <el-alert type="warning" :closable="false" show-icon
                title="连续无开门天数超过阈值即判定疑似空置，可作为「长期空置」违规的客观依据" />
      <el-table :data="idleList" border size="small" style="margin-top:12px">
        <el-table-column prop="houseId" :label="t('access.house')" width="120">
          <template #default="{ row }">{{ row.houseIdName || row.houseId }}</template>
        </el-table-column>
        <el-table-column prop="lastOpenTime" :label="t('access.lastOpen')" width="180" />
        <el-table-column prop="idleDays" :label="t('access.idleDays')" width="110" />
        <el-table-column prop="suspectIdle" :label="t('access.suspectIdle')" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.suspectIdle ? 'danger' : 'success'">
              {{ row.suspectIdle ? t('misc2.yes') : t('misc2.no') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" :label="t('access.remark')" min-width="200" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="ratioVisible" :title="t('access.ratioTitle')" width="420px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item :label="t('access.total')">{{ ratio.total }}</el-descriptions-item>
        <el-descriptions-item :label="t('access.untrusted')">{{ ratio.untrusted }}</el-descriptions-item>
        <el-descriptions-item :label="t('access.ratio')">{{ ratio.untrustedRatio }}%</el-descriptions-item>
        <el-descriptions-item :label="t('access.threshold')">{{ ratio.threshold }}%</el-descriptions-item>
        <el-descriptions-item :label="t('misc2.meetTarget')">
          <el-tag :type="ratio.pass ? 'success' : 'danger'" size="small">
            {{ ratio.pass ? '达标' : '超标' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { enumLabel } from '@/constants/enums'
import { computed, ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PersonPicker from '@/components/PersonPicker.vue'
import { devApi } from '@/api/modules'

const { t } = useI18n()
const route = useRoute()
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({
  pageNum: 1, pageSize: 20, houseId: '', personId: '', openType: '', abnormalOnly: false
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
      openType: query.openType || undefined,
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

onMounted(() => {
  if (route.query.houseId) query.houseId = String(route.query.houseId)
  load()
})
</script>
