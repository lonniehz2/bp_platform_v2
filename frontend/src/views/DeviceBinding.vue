<template>
  <div>
    <div class="toolbar">
      <el-input v-model="keyword" :placeholder="t('binding.searchHint')" clearable
                style="width:240px" @keyup.enter="loadHouses" />
      <el-button type="primary" @click="loadHouses">{{ t('binding.search') }}</el-button>
      <el-button type="success" plain @click="openBatchBind" data-testid="device-batch-bind">{{ t('binding.batchBind') }}</el-button>
      <el-button type="primary" plain @click="openSpaceView" data-testid="device-space-bind">{{ t('bindingX.spaceView') }}</el-button>
      <span class="muted" style="font-size:12px">
        {{ t('bindingX.spaceOnly') }}
      </span>
    </div>

    <el-row :gutter="12">
      <!-- 左：房源 -->
      <el-col :span="8">
        <el-card shadow="never" body-style="padding:0">
          <div style="padding:8px 12px;font-weight:600;border-bottom:1px solid #eee">
            {{ t('bindingX.housesCount', { n: houses.length }) }}
          </div>
          <el-table :data="houses" height="520" size="small" highlight-current-row
                    @current-change="pickHouse">
            <el-table-column prop="houseCode" :label="t('binding.code')" width="140" />
            <el-table-column prop="houseName" :label="t('binding.name')" min-width="120" />
            <el-table-column prop="houseStatus" :label="t('binding.status')" width="90">
              <template #default="{ row }">
                {{ enumLabel('houseStatus', row.houseStatus) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右：设备 -->
      <el-col :span="16">
        <el-card shadow="never">
          <div class="toolbar" style="margin-bottom:8px">
            <span style="font-weight:600">
              {{ current ? current.houseName + ' (' + current.houseCode + ')' : t('bindingX.pickHouse') }} {{ t('bindingX.devicesOf') }}
            </span>
            <div class="spacer" />
            <el-button v-if="current" type="primary" plain size="small"
                       @click="openBind">{{ t('bindingX.bindDevice') }}</el-button>
            <el-button v-if="current" size="small" @click="loadDevices">{{ t('binding.refresh') }}</el-button>
          </div>

          <el-tabs v-model="tab" @tab-change="loadDevices">
            <el-tab-pane :label="t('binding.ownTab')" name="own" />
            <el-tab-pane :label="t('binding.inheritTab')" name="inherit" />
          </el-tabs>

          <el-table :data="rows" v-loading="loading" size="small" border max-height="430">
            <el-table-column prop="deviceName" :label="t('binding.deviceName')" min-width="160" />
            <el-table-column prop="deviceId" :label="t('binding.deviceId')" width="170" />
            <el-table-column prop="deviceType" :label="t('binding.category')" width="110">
              <template #default="{ row }">{{ typeLabel(row.deviceType) }}</template>
            </el-table-column>
            <el-table-column prop="spaceId" :label="t('binding.space')" width="150">
              <template #default="{ row }">
                {{ row.spaceName || row.spaceIdName || row.spaceId || '—' }}
              </template>
            </el-table-column>
            <el-table-column v-if="tab === 'inherit'" prop="scope" :label="t('binding.source')" width="100">
              <template #default="{ row }">{{ row.scope || t('bindingX.inherited') }}</template>
            </el-table-column>
            <el-table-column prop="onlineStatus" :label="t('binding.online')" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.onlineStatus === 1 ? 'success' : 'info'">
                  {{ row.onlineStatus === 1 ? t('bindingX.online') : t('bindingX.offline') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="tab === 'own'" :label="t('binding.actions')" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" @click="unbind(row)">{{ t('binding.unbind') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 绑定设备 -->
    <el-dialog v-model="bindVisible" :title="t('binding.bindTitle')" width="680px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                :title="t('binding.bindHint')" />
      <el-table :data="unbound" v-loading="bindLoading" size="small" border max-height="330"
                @selection-change="(v) => (picked = v)">
        <el-table-column type="selection" width="46" />
        <el-table-column prop="deviceName" :label="t('bindingX.devName')" min-width="160" />
        <el-table-column prop="deviceId" :label="t('bindingX.devId')" width="180" />
        <el-table-column prop="deviceType" :label="t('bindingX.category')" width="110">
          <template #default="{ row }">{{ typeLabel(row.deviceType) }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="bindVisible = false">{{ t('binding.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" :disabled="!picked.length"
                   @click="doBind">{{ t('bindingX.bindSelected', { n: picked.length }) }}</el-button>
      </template>
    </el-dialog>

    <!-- 设备批量绑定：选择 → 校验预览 → 结果 -->
    <el-dialog v-model="batchVisible" :title="t('binding.batchTitle')" width="820px" @close="resetBatch">
      <el-steps :active="batchStep" simple style="margin-bottom:14px">
        <el-step :title="t('bindingX.stepFile')" />
        <el-step :title="t('bindingX.stepPreview')" />
        <el-step :title="t('bindingX.stepResult')" />
      </el-steps>

      <div v-if="batchStep === 1">
        <el-alert type="info" :closable="false" show-icon
                  :title="t('bindingX.csvOrder')" />
        <div style="margin:12px 0;display:flex;gap:8px;align-items:center">
          <el-button size="small" @click="downloadBindTemplate">{{ t('bindingX.downloadTemplate') }}</el-button>
          <span class="muted" style="font-size:12px">{{ t('bindingX.bindConflict') }}</span>
        </div>
        <el-upload :auto-upload="false" :limit="1" accept=".csv"
                   :on-change="onBindFile" :file-list="bindFiles">
          <el-button type="primary" plain>{{ t('bindingX.chooseCsv') }}</el-button>
        </el-upload>
      </div>

      <div v-else-if="batchStep === 2">
        <el-alert :type="bindProblems.length ? 'warning' : 'success'" :closable="false" show-icon
                  :title="bindProblems.length
                    ? t('bindingX.previewProblem', { n: bindProblems.length })
                    : t('bindingX.readyBind', { n: bindRows.length })" />
        <el-table :data="bindRows" size="small" border max-height="280" style="margin-top:8px">
          <el-table-column prop="line" :label="t('bindingX.row')" width="60" />
          <el-table-column prop="houseCode" label="房源编号" width="170" />
          <el-table-column prop="deviceId" label="设备编号" width="190" />
        </el-table>
        <el-table v-if="bindProblems.length" :data="bindProblems" size="small" border
                  style="margin-top:8px" max-height="150">
          <el-table-column prop="line" :label="t('bindingX.rowNo')" width="80" />
          <el-table-column prop="message" :label="t('bindingX.issue')" />
        </el-table>
      </div>

      <div v-else>
        <el-alert :type="bindResult && bindResult.failed ? 'warning' : 'success'"
                  :closable="false" show-icon
                  :title="bindResult
                    ? ('共 ' + bindResult.total + ' 行，成功 ' + bindResult.success
                       + '，失败 ' + bindResult.failed)
                    : '绑定完成'" />
        <div v-if="bindResult" style="margin:10px 0">
          <el-button size="small" :disabled="!bindResult.failed" @click="exportBindErrors">
            导出失败行
          </el-button>
        </div>
        <el-table v-if="bindResult" :data="bindResult.rows" size="small" border max-height="260">
          <el-table-column prop="line" label="行" width="60" />
          <el-table-column prop="houseCode" label="房源编号" width="160" />
          <el-table-column prop="deviceId" label="设备编号" width="180" />
          <el-table-column label="结果" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="row.success ? 'success' : 'danger'">
                {{ row.success ? t('common.success') : t('common.failed') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="说明" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="batchVisible = false">{{ t('binding.close') }}</el-button>
        <el-button v-if="batchStep === 2" @click="batchStep = 1">{{ t('common.reselect') }}</el-button>
        <el-button v-if="batchStep === 2" type="primary" :loading="batchSaving"
                   :disabled="!bindRows.length || !!bindProblems.length" @click="doBatchBind">
          {{ t('binding.startBind') }}
        </el-button>
        <el-button v-if="batchStep === 3" @click="loadDevices">{{ t('binding.refreshDevices') }}</el-button>
      </template>
    </el-dialog>

    <!-- 空间视角：设备直接绑定到楼栋/单元/楼层/房间 -->
    <el-dialog v-model="spaceVisible" :title="t('bindingX.spaceTitle')" width="820px"
               @close="resetSpace">
      <el-alert type="info" :closable="false" show-icon
                :title="t('bindingX.spaceHint')" style="margin-bottom:10px" />
      <el-form inline>
        <el-form-item :label="t('bindingX.org')">
          <el-select v-model="spaceOrgId" filterable style="width:190px" @change="loadSpaceTree">
            <el-option v-for="o in orgs" :key="o.id" :label="o.orgName" :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('bindingX.spaceNode')">
          <el-tree-select v-model="spaceId" :data="spaceTree" check-strictly filterable
                          :render-after-expand="false"
                          :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                          style="width:300px" :placeholder="t('bindingX.spacePlaceholder')"
                          @change="loadSpaceDevices" />
        </el-form-item>
      </el-form>

      <template v-if="!spaceBindMode">
        <div class="toolbar" style="margin:8px 0">
          <span style="font-weight:600">
            {{ spaceName ? spaceName + ' ' + t('bindingX.spaceDevices') : t('bindingX.spacePlaceholder') }}
          </span>
          <div class="spacer" />
          <el-button v-if="spaceId" type="primary" plain size="small" @click="openSpaceBind">
            {{ t('bindingX.bindSpace') }}
          </el-button>
          <el-button v-if="spaceId" size="small" @click="loadSpaceDevices">{{ t('binding.refresh') }}</el-button>
        </div>
        <el-table :data="spaceDevices" v-loading="spaceLoading" border size="small" max-height="360"
                  :empty-text="t('bindingX.spaceEmpty')">
          <el-table-column prop="deviceName" :label="t('binding.deviceName')" min-width="170" />
          <el-table-column prop="deviceId" :label="t('binding.deviceId')" width="180" />
          <el-table-column prop="deviceType" :label="t('binding.category')" width="110">
            <template #default="{ row }">{{ typeLabel(row.deviceType) }}</template>
          </el-table-column>
          <el-table-column prop="onlineStatus" :label="t('binding.online')" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.onlineStatus === 1 ? 'success' : 'info'">
                {{ row.onlineStatus === 1 ? t('bindingX.online') : t('bindingX.offline') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('binding.actions')" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="danger" @click="unbindSpace(row)">{{ t('binding.unbind') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <template v-else>
        <div class="toolbar" style="margin:8px 0">
          <span style="font-weight:600">{{ t('bindingX.spaceBindTitle') }}</span>
          <div class="spacer" />
          <el-button size="small" @click="spaceBindMode = false">{{ t('bindingX.back') }}</el-button>
        </div>
        <el-table :data="spaceUnbound" v-loading="spaceBindLoading" border size="small" max-height="330"
                  @selection-change="(v) => (spacePicked = v)">
          <el-table-column type="selection" width="46" />
          <el-table-column prop="deviceName" :label="t('bindingX.devName')" min-width="160" />
          <el-table-column prop="deviceId" :label="t('bindingX.devId')" width="180" />
          <el-table-column prop="deviceType" :label="t('bindingX.category')" width="110">
            <template #default="{ row }">{{ typeLabel(row.deviceType) }}</template>
          </el-table-column>
        </el-table>
      </template>

      <template #footer>
        <el-button @click="spaceVisible = false">{{ t('binding.close') }}</el-button>
        <el-button v-if="spaceBindMode" type="primary" :loading="spaceSaving"
                   :disabled="!spacePicked.length" @click="doSpaceBind">
          {{ t('bindingX.bindSelected', { n: spacePicked.length }) }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * 空间（房源）与设备对应关系管理。
 *
 * 设备统一绑定到空间（space_id），房源通过 house.space_id 定位；
 * 床位/房间可继承上级空间设备。
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const { t } = useI18n()
const keyword = ref('')
const houses = ref([])
const current = ref(null)
const rows = ref([])
const loading = ref(false)
const tab = ref('own')
const devTypes = ref([])

const batchVisible = ref(false)
const batchStep = ref(1)
const batchSaving = ref(false)
const bindFiles = ref([])
const bindRows = ref([])
const bindProblems = ref([])
const bindResult = ref(null)
let bindFile = null

function openBatchBind() {
  resetBatch()
  batchVisible.value = true
}

function resetBatch() {
  batchStep.value = 1
  bindFiles.value = []
  bindRows.value = []
  bindProblems.value = []
  bindResult.value = null
  batchSaving.value = false
  bindFile = null
}

function downloadBindTemplate() {
  const csv = '\ufeff房源编号,设备编号\nZZ-H-00001,LK00000001\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备批量绑定模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

/** 选文件 → 解析 → 校验 → 进入预览 */
function onBindFile(file) {
  bindFile = file.raw
  bindFiles.value = [file]
  bindResult.value = null
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = String(e.target.result || '').replace(/^\ufeff/, '')
    const lines = text.split(/\r?\n/).filter((x) => x.trim() !== '')
    if (!lines.length) {
      bindProblems.value = [{ line: 0, message: '文件为空' }]
      batchStep.value = 2
      return
    }
    let body = lines
    if (/房源编号|houseCode/i.test(lines[0])) {
      body = lines.slice(1)
    }
    const seenDevice = new Set()
    const seenPair = new Set()
    const problems = []
    bindRows.value = body.map((l, i) => {
      const line = i + (lines.length - body.length) + 1
      const cells = l.split(',').map((x) => (x || '').trim())
      const houseCode = cells[0] || ''
      const deviceId = cells[1] || ''
      if (!houseCode) problems.push({ line, message: '房源编号为空' })
      if (!deviceId) problems.push({ line, message: '设备编号为空' })
      if (deviceId && seenDevice.has(deviceId)) {
        problems.push({ line, message: '同一设备在文件中重复：' + deviceId })
      }
      if (deviceId) seenDevice.add(deviceId)
      const pair = houseCode + '|' + deviceId
      if (houseCode && deviceId && seenPair.has(pair)) {
        problems.push({ line, message: '同一「房源+设备」重复' })
      }
      seenPair.add(pair)
      return { line, houseCode, deviceId }
    })
    bindProblems.value = problems
    batchStep.value = 2
  }
  reader.readAsText(file.raw, 'utf-8')
}

/** 提交批量绑定 */
async function doBatchBind() {
  if (!bindRows.value.length) { ElMessage.warning('没有可绑定的数据'); return }
  batchSaving.value = true
  try {
    const r = await req.post('/devices/bind-batch', bindRows.value)
    bindResult.value = r || {}
    batchStep.value = 3
    ElMessage.success('绑定完成：成功 ' + (r?.success || 0) + '，失败 ' + (r?.failed || 0))
    loadDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '批量绑定失败')
  } finally { batchSaving.value = false }
}

function exportBindErrors() {
  const rows = ((bindResult.value && bindResult.value.rows) || []).filter((x) => !x.success)
  const csv = '\ufeff行号,房源编号,设备编号,原因\n'
    + rows.map((x) => [x.line, x.houseCode, x.deviceId, String(x.message || '').replace(/,/g, '，')].join(','))
      .join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备绑定失败行.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

const bindVisible = ref(false)
const bindLoading = ref(false)
const saving = ref(false)
const unbound = ref([])
const picked = ref([])

const TYPE_LABEL = {
  LOCK: '门锁', ACCESS: '门禁', BARRIER: '道闸', ELEVATOR: '梯控',
  WATER_METER: '水表', ELEC_METER: '电表', GAS_METER: '燃气表', HEAT_METER: '热量表',
  CAMERA: '摄像头', SENSOR: '传感器', OTHER: '其他'
}
function typeLabel(code) { return TYPE_LABEL[code] || code || '—' }

async function loadHouses() {
  try {
    const r = await req.get('/houses', {
      params: { pageNum: 1, pageSize: 100, keyword: keyword.value || undefined }
    })
    houses.value = (r && r.rows) || []
  } catch (e) {
    ElMessage.error('加载房源失败')
  }
}

function pickHouse(row) {
  current.value = row
  loadDevices()
}

async function loadDevices() {
  if (!current.value) return
  loading.value = true
  try {
    if (tab.value === 'inherit') {
      const d = await req.get('/devices/inherited', {
        params: { houseId: current.value.id }
      })
      // 继承页签只显示上级空间设备，排除本房源自身的设备
      rows.value = ((d && d.devices) || []).filter((x) => x.scope === '继承')
    } else {
      const sid = current.value.spaceId
      if (!sid) {
        rows.value = []
        return
      }
      const d = await req.get('/devices', {
        params: { pageNum: 1, pageSize: 100, spaceId: sid }
      })
      rows.value = (d && d.rows) || []
    }
  } catch (e) {
    ElMessage.error('加载设备失败')
  } finally { loading.value = false }
}

async function openBind() {
  bindVisible.value = true
  bindLoading.value = true
  picked.value = []
  try {
    const list = await req.get('/devices/unbound')
    unbound.value = list || []
  } catch (e) {
    ElMessage.error('加载未绑定设备失败')
  } finally { bindLoading.value = false }
}

async function doBind() {
  if (!current.value || !current.value.spaceId) {
    ElMessage.warning('该房源未关联空间，无法绑定设备')
    return
  }
  saving.value = true
  try {
    for (const d of picked.value) {
      await req.post(`/devices/${d.id}/bind`, { spaceId: current.value.spaceId })
    }
    ElMessage.success(`已绑定 ${picked.value.length} 台设备`)
    bindVisible.value = false
    loadDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '绑定失败')
  } finally { saving.value = false }
}

async function unbind(row) {
  await ElMessageBox.confirm(`确认把「${row.deviceName}」从该房源解绑？`, '提示',
    { type: 'warning' })
  try {
    await req.post(`/devices/${row.id}/bind`, { spaceId: null })
    ElMessage.success('已解绑')
    loadDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '解绑失败')
  }
}

// ---------------- 空间视角 ----------------
const spaceVisible = ref(false)
const orgs = ref([])
const spaceOrgId = ref('')
const spaceTree = ref([])
const spaceId = ref('')
const spaceName = ref('')
const spaceDevices = ref([])
const spaceUnbound = ref([])
const spacePicked = ref([])
const spaceLoading = ref(false)
const spaceBindLoading = ref(false)
const spaceSaving = ref(false)
const spaceBindMode = ref(false)

async function openSpaceView() {
  spaceVisible.value = true
  spaceBindMode.value = false
  spaceId.value = ''
  spaceName.value = ''
  spaceDevices.value = []
  await loadOrgs()
  if (spaceOrgId.value) await loadSpaceTree()
}

async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 100 } })
    orgs.value = d.rows || []
    if (!spaceOrgId.value && orgs.value.length) spaceOrgId.value = String(orgs.value[0].id)
  } catch (e) { orgs.value = [] }
}

async function loadSpaceTree() {
  spaceId.value = ''
  spaceName.value = ''
  spaceTree.value = []
  spaceDevices.value = []
  if (!spaceOrgId.value) return
  try {
    spaceTree.value = await req.get('/spaces/tree', { params: { orgId: spaceOrgId.value } }) || []
  } catch (e) { spaceTree.value = [] }
}

function findSpace(nodes, id) {
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const hit = findSpace(n.children, id)
    if (hit) return hit
  }
  return null
}

async function loadSpaceDevices() {
  if (!spaceId.value) { spaceDevices.value = []; return }
  spaceName.value = findSpace(spaceTree.value, spaceId.value)?.spaceName || ''
  spaceLoading.value = true
  try {
    const d = await req.get('/devices', { params: { pageNum: 1, pageSize: 100, spaceId: spaceId.value } })
    spaceDevices.value = (d && d.rows) || []
  } catch (e) {
    ElMessage.error(t('bindingX.loadSpaceFailed'))
  } finally { spaceLoading.value = false }
}

async function openSpaceBind() {
  if (!spaceId.value) { ElMessage.warning(t('bindingX.spacePlaceholder')); return }
  spaceBindMode.value = true
  spaceBindLoading.value = true
  spacePicked.value = []
  try {
    spaceUnbound.value = await req.get('/devices/unbound') || []
  } catch (e) {
    ElMessage.error(t('bindingX.loadUnboundFailed'))
  } finally { spaceBindLoading.value = false }
}

async function doSpaceBind() {
  if (!spaceId.value || !spacePicked.value.length) return
  spaceSaving.value = true
  try {
    for (const d of spacePicked.value) {
      await req.post(`/devices/${d.id}/bind`, { spaceId: spaceId.value })
    }
    ElMessage.success(t('bindingX.spaceBound', { n: spacePicked.value.length }))
    spaceBindMode.value = false
    await loadSpaceDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('bindingX.spaceBindFailed'))
  } finally { spaceSaving.value = false }
}

async function unbindSpace(row) {
  await ElMessageBox.confirm(t('bindingX.spaceUnbindConfirm'), t('binding.unbind'),
    { type: 'warning' })
  try {
    await req.post(`/devices/${row.id}/bind`, { spaceId: null })
    ElMessage.success(t('bindingX.spaceUnbound'))
    await loadSpaceDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('bindingX.spaceUnbindFailed'))
  }
}

function resetSpace() {
  spaceBindMode.value = false
  spaceId.value = ''
  spaceName.value = ''
  spaceDevices.value = []
  spaceUnbound.value = []
  spacePicked.value = []
}

onMounted(loadHouses)
</script>
