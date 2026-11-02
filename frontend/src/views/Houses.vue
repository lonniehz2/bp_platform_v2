<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('house.title') }}</h3>
      <div class="spacer" />
      <el-select v-model="orgFilter" :placeholder="t('house.org')" clearable filterable
                 style="width:200px" data-testid="house-org-filter"
                 @change="reload">
        <el-option v-for="o in orgOptions" :key="o.id"
                   :label="o.orgName" :value="o.id" />
      </el-select>
      <el-input v-model="keyword" :placeholder="t('house.keyword')" clearable
                style="width:180px" @keyup.enter="reload" />
      <el-select v-model="houseStatus" :placeholder="t('house.status')" clearable
                 style="width:140px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
        <el-select v-model="houseTypeFilter" :placeholder="t('house.type')" clearable
                   style="width:150px" @change="reload" data-testid="house-type-filter">
          <el-option v-for="t in houseTypes" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
      <el-button type="primary" @click="reload">{{ t('house.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('house.reset') }}</el-button>
      <el-button type="success" @click="openCreate">{{ t('house.create') }}</el-button>
        <el-button type="primary" plain @click="openBeds"
                   data-testid="house-beds">{{ t('house.beds') }}</el-button>
        <el-button type="warning" plain @click="importVisible = true"
                   data-testid="house-import">{{ t('house.import') }}</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('house.empty')">
      <el-table-column prop="houseCode" :label="t('house.code')" width="150" />
      <el-table-column prop="houseName" :label="t('house.name')" min-width="140" />
      <el-table-column prop="orgId" :label="t('house.orgCol')" width="150">
        <template #default="{ row }">{{ row.orgIdName || row.orgId }}    <el-dialog v-model="statusVisible" :title="t('house.changeStatus')" width="420px">
      <el-form label-width="90px">
        <el-form-item :label="t('house.status')">
          <el-select v-model="statusValue" style="width:100%">
            <el-option v-for="st in statuses" :key="st"
                       :label="enumLabel('houseStatus', st)" :value="st" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="statusVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doChangeStatus">
          {{ t('common.save') }}
        </el-button>
      </template>
    </el-dialog>
</template>
      </el-table-column>
      <el-table-column :label="t('house.space')" width="170" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.spaceName">
                <el-tag v-if="row.spaceType === 'BED'" size="small" type="warning">{{ t('misc7.bed') }}</el-tag>
                {{ row.spaceName }}
              </span>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('house.typeCol')" width="130">
        <template #default="{ row }">{{ row.houseTypeLabel || enumLabel('houseType', row.houseType) }}</template>
      </el-table-column>
      <el-table-column :label="t('house.statusCol')" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="statusType(row.houseStatus)">
            {{ row.houseStatusLabel || enumLabel('houseStatus', row.houseStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="area" :label="t('house.area')" width="100" />
      <el-table-column :label="t('house.rent')" width="120">
        <template #default="{ row }">{{ row.rentStandard || '-' }}</template>
      </el-table-column>
      <el-table-column :label="t('house.actions')" width="210" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="changeStatus(row)">{{ t('house.changeStatus') }}</el-button>
          <el-button link @click="detail = row; show = true">{{ t('house.detail') }}</el-button>
          <el-button link type="primary" @click="openOccupancy(row)">{{ t('house.occupancy') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <el-dialog v-model="occVisible" :title="t('house.occTitle')" width="560px">
      <el-descriptions v-if="occ && occ.occupied" :column="1" border size="small">
        <el-descriptions-item :label="t('house.contractNo')">{{ occ.contractNo }}</el-descriptions-item>
        <el-descriptions-item :label="t('house.lease')">{{ occ.leaseStart }} ~ {{ occ.leaseEnd }}</el-descriptions-item>
        <el-descriptions-item :label="t('house.lessee')">{{ occ.tenantName || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('house.phone')">{{ occ.tenantPhone || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('house.tenants')">{{ occ.tenantCount }} 人</el-descriptions-item>
        <el-descriptions-item :label="t('house.cohabitants')">
          <div v-if="!occ.cohabitants || !occ.cohabitants.length" class="muted">{{ t('misc7.none') }}</div>
          <div v-for="(c, i) in occ.cohabitants" :key="i">
            {{ c.name }}（{{ c.relation || t('misc7.cohabitant') }}）{{ c.id_card_mask || '' }}
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <el-empty v-else :description="t('misc7.noContract')" />
      <template #footer>
        <el-button @click="occVisible = false">{{ t('house.close') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="createVisible" :title="t('house.createTitle')" width="640px">
      <el-form :model="f" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('house.orgCol')">
            <el-select v-model="f.orgId" filterable clearable style="width:100%"
                       :placeholder="t('house.selectOrg')"
                       @change="onOrgChange">
              <el-option v-for="o in orgOptions" :key="o.id"
                         :label="o.orgName" :value="o.id" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.spaceNode')" required>
            <el-tree-select v-model="f.spaceId" :data="spaceTree" check-strictly
                            filterable :render-after-expand="false"
                            :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                            :placeholder="t('house.spaceSearch')" style="width:100%"
                            @change="onSpacePicked" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.houseCode')" required>
            <el-input v-model="f.houseCode" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.houseName')" required>
            <el-input v-model="f.houseName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.houseType')" required>
            <el-select v-model="f.houseType" style="width:100%">
              <el-option :label="t('misc7.publicRental')" value="PUBLIC_RENTAL" />
              <el-option :label="t('misc7.affordableRental')" value="AFFORDABLE_RENTAL" />
              <el-option :label="t('misc7.talentApartment')" value="TALENT" />
              <el-option :label="t('misc7.apartment')" value="APARTMENT" />
              <el-option :label="t('misc7.dormitory')" value="DORMITORY" />
              <el-option :label="t('misc7.rental')" value="RENTAL" />
              <el-option :label="t('misc7.hotel')" value="HOTEL" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.buildArea')" required>
            <el-input-number v-model="f.area" :min="0.01" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.innerArea')">
            <el-input-number v-model="f.innerArea" :min="0" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.buildType')">
            <el-select v-model="f.structType" style="width:100%">
              <el-option :label="t('misc8.multi')" value="MULTI" />
              <el-option :label="t('misc8.smallHigh')" value="SMALL_HIGH" />
              <el-option :label="t('misc8.high')" value="HIGH" />
              <el-option :label="t('misc8.superHigh')" value="SUPER_HIGH" />
              <el-option :label="t('misc8.villa')" value="VILLA" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('house.purpose')">
            <el-select v-model="f.useType" style="width:100%">
              <el-option :label="t('misc8.civil')" value="CIVIL" />
              <el-option :label="t('misc8.commercial')" value="COMMERCIAL" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.layout')">
            <el-input v-model="f.unitLayout" :placeholder="t('misc8.layoutHint')" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.floor')">
            <el-input-number v-model="f.floorNo" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.orientation')">
            <el-select v-model="f.orientation" clearable style="width:100%"
                       :placeholder="t('misc8.orientationHint')">
              <el-option v-for="o in ORIENTATIONS" :key="o.value" :label="o.label"
                         :value="o.value" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.decoration')">
            <el-select v-model="f.decorateLevel" style="width:100%">
              <el-option :label="t('misc8.rough')" value="ROUGH" />
              <el-option :label="t('misc8.simple')" value="SIMPLE" />
              <el-option :label="t('misc8.fine')" value="FINE" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.rentStandard')">
            <el-input-number v-model="f.rentStandard" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.rentUnit')">
            <el-select v-model="f.rentUnit" style="width:100%">
              <el-option :label="t('misc8.areaMonth')" value="AREA_MONTH" />
              <el-option :label="t('misc8.houseMonth')" value="HOUSE_MONTH" />
              <el-option :label="t('misc8.bedMonth')" value="BED_MONTH" />
              <el-option :label="t('misc8.houseNight')" value="HOUSE_NIGHT" />
              <el-option :label="t('misc8.bedNight')" value="BED_NIGHT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.meterMode')">
            <el-select v-model="f.meterMode" style="width:100%">
              <el-option :label="t('misc8.independent')" value="INDEPENDENT" />
              <el-option :label="t('misc8.shared')" value="SHARED" />
              <el-option :label="t('misc8.mixed')" value="MIXED" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('misc8.maxCapacity')">
            <el-input-number v-model="f.maxCapacity" :min="1" style="width:100%" />
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('person.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('misc8.save') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" :title="t('misc8.detail')" size="560px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 批量导入房源（CSV）：选择 → 校验预览 → 提交 -->
    <el-dialog v-model="importVisible" :title="t('misc8.importTitle')" width="820px"
               @close="resetImport">
      <el-steps :active="importStep" simple style="margin-bottom:14px">
        <el-step :title="t('misc8.stepFile')" />
        <el-step :title="t('misc8.stepPreview')" />
        <el-step :title="t('misc8.stepResult')" />
      </el-steps>

      <div v-if="importStep === 1">
        <el-alert type="info" :closable="false" show-icon
                  :title="t('misc10.csvOrder')" />
        <div style="margin:12px 0;display:flex;gap:8px;align-items:center">
          <el-button size="small" @click="downloadTemplate">{{ t('misc10.downloadTemplate') }}</el-button>
          <span class="muted" style="font-size:12px">
            {{ t('misc10.importHint') }}
          </span>
        </div>
        <el-upload :auto-upload="false" :limit="1" accept=".csv"
                   :on-change="onImportFile" :file-list="importFiles">
          <el-button type="primary" plain>{{ t('misc10.chooseCsv') }}</el-button>
        </el-upload>
      </div>

      <div v-else-if="importStep === 2">
        <el-alert :type="parseProblems.length ? 'warning' : 'success'" :closable="false" show-icon
                  :title="parseProblems.length
                    ? t('misc10.previewProblem', { n: parseProblems.length })
                    : t('misc10.previewOk', { rows: parsedRows.length, cols: parsedHeaders.length })" />
        <div class="muted" style="font-size:12px;margin:8px 0">
          {{ t('misc10.previewHint') }}
        </div>
        <el-table :data="parsedRows.slice(0, 8)" size="small" border max-height="240">
          <el-table-column prop="line" :label="t('misc10.row')" width="60" />
          <el-table-column v-for="(h, i) in parsedHeaders.slice(0, 10)" :key="i"
                           :label="h || t('misc10.column', { n: i + 1 })" min-width="110"
                           show-overflow-tooltip>
            <template #default="{ row }">{{ (row.cells || [])[i] }}</template>
          </el-table-column>
        </el-table>
        <el-table v-if="parseProblems.length" :data="parseProblems" size="small" border
                  style="margin-top:8px" max-height="160">
          <el-table-column prop="line" :label="t('misc10.rowNo')" width="80" />
          <el-table-column prop="message" :label="t('misc10.problem')" />
        </el-table>
      </div>

      <div v-else>
        <el-alert :type="importResult && importResult.skipped ? 'warning' : 'success'"
                  :closable="false" show-icon
                  :title="importResult
                    ? t('misc10.resultSummary', { total: importResult.total, created: importResult.created, skipped: importResult.skipped })
                    : t('misc10.importDone')" />
        <div v-if="importResult" style="margin:10px 0;display:flex;gap:8px">
          <el-button size="small" :disabled="!importResult.errors || !importResult.errors.length"
                     @click="exportImportErrors">{{ t('misc10.exportErrors') }}</el-button>
          <span class="muted" style="font-size:12px">{{ t('misc10.retryHint') }}</span>
        </div>
        <el-table v-if="importResult && importResult.errors && importResult.errors.length"
                  :data="importResult.errors" size="small" border max-height="220">
          <el-table-column prop="line" :label="t('misc10.rowNo')" width="80" />
          <el-table-column prop="message" :label="t('misc10.reason')" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="importVisible = false">{{ t('misc10.close') }}</el-button>
        <el-button v-if="importStep > 1" @click="importStep = 1">{{ t('misc10.reselect') }}</el-button>
        <el-button v-if="importStep === 3" @click="load">{{ t('misc10.refreshList') }}</el-button>
        <el-button v-if="importStep === 2" type="primary" :loading="saving"
                   :disabled="!importFile || !!parseProblems.length" @click="doImport">
          {{ t('misc10.startImport') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 宿舍床位管理 -->
    <el-dialog v-model="bedVisible" :title="t('misc10.bedTitle')" width="720px">
      <el-form label-width="90px">
        <el-form-item :label="t('misc10.room')">
          <el-tree-select v-model="bedRoomId" :data="spaceTree" check-strictly
                          :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                          filterable :placeholder="t('misc10.roomHint')" style="width:100%"
                          @change="loadBeds" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item :label="t('misc10.count')">
            <el-input v-model="bedCount" type="number" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item :label="t('misc10.bedRent')">
            <el-input v-model="bedRent" type="number" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item :label="t('misc10.bedArea')">
            <el-input v-model="bedArea" type="number" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <div style="margin:8px 0 12px">
        <el-button type="primary" :loading="saving" :disabled="!bedRoomId"
                   @click="doCreateBeds">{{ t('misc10.createBeds') }}</el-button>
        <span class="muted" style="font-size:12px;margin-left:8px">
          {{ t('misc10.bedHint') }}
        </span>
      </div>
      <el-table :data="bedRows" size="small" border max-height="320" v-loading="bedLoading">
        <el-table-column prop="bedCode" :label="t('misc10.bedCode')" width="150" />
        <el-table-column prop="bedName" :label="t('misc10.bedName')" min-width="150" />
        <el-table-column prop="houseStatus" :label="t('misc10.houseStatus')" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.occupied ? 'success' : 'info'">
              {{ row.occupied ? t('misc10.occupied') : (row.houseStatus === 'VACANT' ? t('misc10.vacant') : row.houseStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="occupant" :label="t('misc10.occupant')" width="110">
          <template #default="{ row }">{{ row.occupant || '—' }}</template>
        </el-table-column>
        <el-table-column prop="leaseEnd" :label="t('misc10.leaseEnd')" width="120">
          <template #default="{ row }">{{ row.leaseEnd || '—' }}</template>
        </el-table-column>
        <el-table-column prop="rentStandard" :label="t('misc10.monthlyRent')" width="100" />
        <el-table-column :label="t('misc10.actions')" width="120">
          <template #default="{ row }">
            <el-button v-if="row.occupied" link type="primary"
                       @click="openSwapBed(row)">{{ t('misc10.swapBed') }}</el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="bedVisible = false">{{ t('misc10.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 床位调换 -->
    <el-dialog v-model="swapVisible" :title="t('misc10.swapTitle')" width="480px">
      <el-alert type="info" :closable="false" show-icon
                :title="t('misc10.swapHint')" />
      <el-form :model="swapForm" label-width="90px" style="margin-top:12px">
        <el-form-item :label="t('misc10.currentBed')">
          <span>{{ swapForm.fromBed }}（{{ swapForm.occupant }}）</span>
        </el-form-item>
        <el-form-item :label="t('misc10.targetBed')" required>
          <el-select v-model="swapForm.targetHouseId" style="width:100%"
                     :placeholder="t('misc10.targetHint')">
            <el-option v-for="b in freeBeds" :key="b.houseId"
                       :label="b.bedName + '（月租 ' + (b.rentStandard || 0) + '）'"
                       :value="b.houseId" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('misc10.swapReason')">
          <el-input v-model="swapForm.reason" :placeholder="t('misc10.swapReasonHint')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="swapVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doSwapBed">{{ t('house.confirmSwap') }}</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { computed, ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { houseApi } from '@/api/modules'
import req from '@/api/request'
import { useAuthStore } from '@/store/auth'
import { enumLabel } from '@/constants/enums'
import DetailView from '@/components/DetailView.vue'

const { t } = useI18n()
const statuses = ['VACANT', 'PENDING_ALLOC', 'ALLOCATED', 'OCCUPIED', 'LOCKED',
  'REPAIR', 'OFFLINE']
const loading = ref(false)
const saving = ref(false)
const auth = useAuthStore()
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const houseStatus = ref('')
const houseTypeFilter = ref('')
/** 多业态房源类型（宿舍/公寓/酒店民宿 与保障房并行） */
const houseTypes = [
  { value: 'PUBLIC_RENTAL', label: enumLabel('houseType', 'PUBLIC_RENTAL') },
  { value: 'AFFORDABLE_RENTAL', label: enumLabel('houseType', 'AFFORDABLE_RENTAL') },
  { value: 'TALENT', label: enumLabel('houseType', 'TALENT') },
  { value: 'APARTMENT', label: enumLabel('houseType', 'APARTMENT') },
  { value: 'DORMITORY', label: enumLabel('houseType', 'DORMITORY') },
  { value: 'RENTAL', label: enumLabel('houseType', 'RENTAL') },
  { value: 'HOTEL', label: enumLabel('houseType', 'HOTEL') }
]
const occVisible = ref(false)
const occ = ref(null)

async function openOccupancy(row) {
  occ.value = null
  occVisible.value = true
  try {
    occ.value = await req.get('/houses/' + row.id + '/occupancy')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '查询入住信息失败')
  }
}

const show = ref(false)
const detail = ref(null)
const createVisible = ref(false)
const f = reactive({ spaceId: null, houseCode: '', houseName: '',
  houseType: 'PUBLIC_RENTAL', structType: 'MULTI', useType: 'CIVIL',
  unitLayout: '', floorNo: 1, orientation: 'SOUTH', area: null, innerArea: null,
  decorateLevel: 'SIMPLE', rentStandard: null, rentUnit: 'AREA_MONTH', meterMode: 'INDEPENDENT',
  maxCapacity: 2 })

function statusType(s) {
  return s === 'OCCUPIED' || s === 'ALLOCATED' ? 'success'
    : (s === 'VACANT' ? 'info' : (s === 'REPAIR' ? 'warning' : 'danger'))
}

const orgFilter = ref(null)

async function loadOrgFilterOptions() {
  if (orgOptions.value.length) return
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    orgOptions.value = d.rows || d || []
  } catch (e) { /* 忽略 */ }
}

async function load() {
  loading.value = true
  try {
    const d = await houseApi.page({
      pageNum: pageNum.value, pageSize: pageSize.value,
      orgId: orgFilter.value || undefined,
      keyword: keyword.value || undefined,
      houseStatus: houseStatus.value || undefined,
      houseType: houseTypeFilter.value || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function openCreate() {
  // 先确定组织：优先当前用户组织，否则取组织列表第一个；再加载该组织的空间树
  let orgId = f.orgId || auth.user?.orgId
  if (!orgOptions.value.length) {
    try {
      const od = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
      orgOptions.value = od.rows || od || []
    } catch (e) { /* 忽略 */ }
  }
  if (!orgId) {
    const first = orgOptions.value[0]
    orgId = first && first.id
  }
  if (orgId) {
    f.orgId = orgId
    await onOrgChange(orgId)
  }
  createVisible.value = true
}
async function doCreate() {
  if (!f.spaceId || !f.houseCode || !f.houseName || !f.area) {
    ElMessage.warning('空间节点、编号、名称、面积为必填'); return
  }
  saving.value = true
  try {
    await houseApi.create({ ...f })
    ElMessage.success('房源已创建')
    createVisible.value = false; reload()
  } finally { saving.value = false }
}

function changeStatus(row) {
  statusRow.value = row
  statusValue.value = row.houseStatus || 'VACANT'
  statusVisible.value = true
}

async function doChangeStatus() {
  saving.value = true
  try {
    await houseApi.setStatus(statusRow.value.id, { status: statusValue.value })
    ElMessage.success(t('common.success'))
    statusVisible.value = false
    load()
  } finally { saving.value = false }
}

function resetQuery() {
  orgFilter.value = null
  houseStatus.value = ''
  houseTypeFilter.value = ''
  keyword.value = ''
  pageNum.value = 1
  reload()
}


/** 批量导入房源（CSV） */
const importVisible = ref(false)
const importFiles = ref([])
const importResult = ref(null)
const importStep = ref(1)
const parsedRows = ref([])
const parsedHeaders = ref([])
const parseProblems = ref([])

/** 简单 CSV 解析：支持引号包裹、CRLF、BOM */
function parseCsv(text) {
  const clean = text.replace(/^\ufeff/, '')
  const rows = []
  let cur = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < clean.length; i++) {
    const ch = clean[i]
    if (quoted) {
      if (ch === '"' && clean[i + 1] === '"') { cell += '"'; i++ }
      else if (ch === '"') { quoted = false }
      else { cell += ch }
    } else if (ch === '"') { quoted = true }
    else if (ch === ',') { cur.push(cell); cell = '' }
    else if (ch === '\n') { cur.push(cell); rows.push(cur); cur = []; cell = '' }
    else if (ch === '\r') { /* 忽略 */ }
    else { cell += ch }
  }
  if (cell !== '' || cur.length) { cur.push(cell); rows.push(cur) }
  return rows.filter((r) => r.some((x) => (x || '').trim() !== ''))
}

/** 选文件后解析并进入预览 */
function onImportFile(file) {
  importFile = file.raw
  importFiles.value = [file]
  importResult.value = null
  parsedRows.value = []
  parsedHeaders.value = []
  parseProblems.value = []
  const reader = new FileReader()
  reader.onload = (e) => {
    const all = parseCsv(String(e.target.result || ''))
    if (!all.length) {
      parseProblems.value = [{ line: 0, message: '文件为空' }]
      importStep.value = 2
      return
    }
    let body = all
    const first = (all[0] || []).join(',')
    if (/房源编号|houseCode/i.test(first)) {
      parsedHeaders.value = all[0].map((x) => (x || '').trim())
      body = all.slice(1)
    } else {
      parsedHeaders.value = ['组织编码', '空间编码', '房源编号', '房源名称', '房源类型',
        '用途', '建筑面积', '租金标准', '计价单位', '房源状态']
    }
    const seen = new Set()
    const problems = []
    parsedRows.value = body.map((cells, idx) => {
      const line = idx + (all.length - body.length) + 1
      if (cells.length < 10) {
        problems.push({ line, message: '列数不足（' + cells.length + ' 列，应为 10 列）' })
      }
      const code = (cells[2] || '').trim()
      if (!code) problems.push({ line, message: '房源编号为空' })
      else if (seen.has(code)) problems.push({ line, message: '文件内房源编号重复：' + code })
      else seen.add(code)
      if (!(cells[3] || '').trim()) problems.push({ line, message: '房源名称为空' })
      if (!(cells[6] || '').trim()) problems.push({ line, message: '建筑面积为空' })
      return { line, cells }
    })
    parseProblems.value = problems
    importStep.value = 2
  }
  reader.readAsText(file.raw, 'utf-8')
}

/** 导出失败行 */
function exportImportErrors() {
  const errs = (importResult.value && importResult.value.errors) || []
  const csv = '\ufeff行号,原因\n' + errs.map((x) => x.line + ',' + String(x.message).replace(/,/g, '，')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '房源导入失败行.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

function resetImport() {
  importStep.value = 1
  parsedRows.value = []
  parsedHeaders.value = []
  parseProblems.value = []
  importResult.value = null
  importFiles.value = []
  importFile = null
}
let importFile = null



function downloadTemplate() {
  // 表头与示例值都用中文，业务人员可直接填；后端同时兼容英文码
  const header = '组织编码,空间编码,房源编号,房源名称,房源类型,用途,建筑面积(㎡),'
    + '租金标准,计价单位,房源状态\n'
  const note = '# 可选值：房源类型=公租房/保障性租赁住房/人才公寓/公寓/宿舍/酒店民宿/出租房；'
    + '用途=民用/商用；计价单位=元/㎡·月/元/套·月/元/床·月/元/套·夜/元/床·夜；'
    + '房源状态=空置/可租/待配租/已配租/已出租/维修中/锁定（本行可保留，导入时自动忽略）'
  const rows = [
    'DEMO-P1,P1-R1,HOUSE-001,示例房源1,公租房,民用,55,15,元/㎡·月,空置',
    'DEMO-P1,P1-R2,HOUSE-002,示例房源2,保障性租赁住房,民用,48.5,18.5,元/套·月,空置',
    'DEMO-P1,P1-R3,HOUSE-003,示例房源3,人才公寓,民用,32,1200,元/套·夜,待配租'
  ].join('\n')
  const blob = new Blob(['\ufeff' + header + '\n' + note + '\n' + rows + '\n'],
    { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '房源导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

async function doImport() {
  if (!importFile) { ElMessage.warning('请选择 CSV 文件'); return }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile)
    const r = await req.post('/houses/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    importResult.value = r || {}
    importStep.value = 3
    ElMessage.success(`导入完成：成功 ${r?.created || 0}，跳过 ${r?.skipped || 0}`)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  } finally { saving.value = false }
}


/** 宿舍床位管理 */
const bedVisible = ref(false)
const bedRoomId = ref('')
const bedRows = ref([])
const bedLoading = ref(false)
const bedCount = ref(4)
const bedRent = ref(300)
const bedArea = ref(8)
const spaceTree = ref([])

/** 朝向：与后端枚举一致（EnumLabels 已配中文） */
const ORIENTATIONS = [
  { value: 'SOUTH', label: enumLabel('orientation', 'SOUTH') },
  { value: 'NORTH', label: enumLabel('orientation', 'NORTH') },
  { value: 'EAST', label: enumLabel('orientation', 'EAST') },
  { value: 'WEST', label: enumLabel('orientation', 'WEST') },
  { value: 'SOUTHEAST', label: enumLabel('orientation', 'SOUTHEAST') },
  { value: 'SOUTHWEST', label: enumLabel('orientation', 'SOUTHWEST') },
  { value: 'NORTHEAST', label: enumLabel('orientation', 'NORTHEAST') },
  { value: 'NORTHWEST', label: enumLabel('orientation', 'NORTHWEST') },
  { value: 'NORTH_SOUTH', label: enumLabel('orientation', 'NORTH_SOUTH') }
]

async function openBeds() {
  bedVisible.value = true
  bedRows.value = []
  bedRoomId.value = ''
  await ensureSpaceTree()
}

/**
 * 确保空间树可用。
 * 后端 /spaces/tree 必须带 orgId；账号无 orgId 时回退到第一个可选组织，
 * 否则房间下拉会是空白（本次修复点）。
 */
const orgOptions = ref([])

/** 组织变化时重新加载空间树 */
async function onOrgChange(orgId) {
  spaceTree.value = []
  if (!orgId) return
  try {
    const tree = await req.get('/spaces/tree', { params: { orgId } })
    spaceTree.value = tree || []
    if (!spaceTree.value.length) {
      ElMessage.warning('该组织下暂无空间节点，请先在「空间管理」创建楼栋/单元/房间')
    }
  } catch (e) {
    ElMessage.error('空间树加载失败：' + (e?.response?.data?.message || e?.message || e))
  }
}

async function ensureSpaceTree() {
  if (spaceTree.value.length) return spaceTree.value
  let orgId = auth.user?.orgId
  if (!orgId) {
    try {
      const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
      const list = d.rows || d || []
      const first = list[0]
      orgId = first && first.id
    } catch (e) { /* 忽略 */ }
  }
  if (!orgId) return []
  try {
    if (!orgOptions.value.length) {
      const od = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
      orgOptions.value = od.rows || od || []
    }
    if (!f.orgId) f.orgId = orgId
    const tree = await req.get('/spaces/tree', { params: { orgId } })
    spaceTree.value = tree || []
  } catch (e) {
    ElMessage.error('空间树加载失败：' + (e?.response?.data?.message || e?.message || e))
  }
  return spaceTree.value
}

/** 选中房间后自动带出组织/房号，减少手填 */
function onSpacePicked(id) {
  const hit = findNode(spaceTree.value, id)
  if (!hit) return
  if (!f.houseName) f.houseName = hit.spaceName
  if (!f.houseCode) f.houseCode = hit.spaceCode
  if (!f.orgId && hit.orgId) f.orgId = hit.orgId
  if (!f.area && hit.area) f.area = Number(hit.area)
}

function findNode(nodes, id) {
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const sub = findNode(n.children, id)
    if (sub) return sub
  }
  return null
}

async function loadBeds() {
  if (!bedRoomId.value) { bedRows.value = []; return }
  bedLoading.value = true
  try {
    bedRows.value = (await req.get('/houses/beds', {
      params: { roomSpaceId: bedRoomId.value } })) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载床位失败')
  } finally { bedLoading.value = false }
}

async function doCreateBeds() {
  if (!bedRoomId.value) { ElMessage.warning('请选择房间'); return }
  saving.value = true
  try {
    const n = await req.post('/houses/beds/batch-create', {
      roomSpaceId: bedRoomId.value, count: Number(bedCount.value) || 1,
      rentStandard: Number(bedRent.value) || 0, areaPerBed: Number(bedArea.value) || 0
    })
    ElMessage.success(`已生成 ${n} 张床位`)
    await loadBeds()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '生成失败')
  } finally { saving.value = false }
}


/** 床位调换 */
const statusVisible = ref(false)
const statusRow = ref(null)
const statusValue = ref('VACANT')
const swapVisible = ref(false)
const swapForm = reactive({ contractId: '', fromBed: '', occupant: '',
  targetHouseId: '', reason: '' })
const freeBeds = computed(() =>
  bedRows.value.filter((b) => !b.occupied && b.houseId))

function openSwapBed(row) {
  if (!row.contractNo) {
    ElMessage.warning('该床位缺少合同信息，无法调换')
    return
  }
  Object.assign(swapForm, { contractId: '', fromBed: row.bedName,
    occupant: row.occupant || '', targetHouseId: '', reason: '' })
  // 用合同号反查合同 ID 由后端承担；此处通过合同列表接口拿 ID
  req.get('/contracts', { params: { pageNum: 1, pageSize: 50, keyword: row.contractNo } })
    .then((res) => {
      const list = (res && res.rows) || []
      const hit = list.find((c) => c.contractNo === row.contractNo)
      if (!hit) { ElMessage.warning('未找到对应合同'); return }
      swapForm.contractId = hit.id
      swapVisible.value = true
    })
    .catch(() => ElMessage.error('查询合同失败'))
}

async function doSwapBed() {
  if (!swapForm.targetHouseId) { ElMessage.warning('请选择目标床位'); return }
  saving.value = true
  try {
    await req.post(`/contracts/${swapForm.contractId}/swap-bed`, {
      targetHouseId: swapForm.targetHouseId, reason: swapForm.reason
    })
    ElMessage.success('床位已调换')
    swapVisible.value = false
    await loadBeds()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '调换失败')
  } finally { saving.value = false }
}

onMounted(() => { load(); loadOrgFilterOptions() })
</script>
