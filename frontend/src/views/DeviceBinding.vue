<template>
  <div class="binding-page">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('binding.pageTitle') }}</h3>
      <el-select v-model="orgId" filterable clearable :placeholder="t('binding.org')"
                 style="width:200px" @change="onOrgChange">
        <el-option v-for="o in orgs" :key="o.id" :label="o.orgName" :value="String(o.id)" />
      </el-select>
      <el-input v-model="houseKeyword" :placeholder="t('binding.searchHouse')" clearable
                style="width:220px" @keyup.enter="searchHouse" />
      <el-button @click="searchHouse">{{ t('binding.search') }}</el-button>
      <div class="spacer" />
      <el-button type="success" plain @click="openImport">{{ t('bindingX.importFile') }}</el-button>
      <el-button @click="reloadTargets">{{ t('binding.refresh') }}</el-button>
    </div>

    <el-row :gutter="12">
      <el-col :span="8">
        <el-card shadow="never" body-style="padding:0">
          <div class="panel-head">
            {{ t('binding.spaceTree') }}
            <span class="muted">{{ t('bindingX.spaceOnly') }}</span>
          </div>
          <div v-if="houseHits.length" class="house-hits">
            <div v-for="h in houseHits" :key="h.id" class="hit" @click="pickHouse(h)">
              <b>{{ h.houseName }}</b>
              <span class="muted">{{ h.houseCode }}</span>
            </div>
          </div>
          <el-tree ref="treeRef" :data="tree" node-key="id" default-expand-all
                   highlight-current :props="{ label: 'spaceName', children: 'children' }"
                   :empty-text="t('bindingX.pickOrg')" @node-click="selectSpace">
            <template #default="{ data }">
              <span class="tree-node">
                <span>{{ data.spaceName }}</span>
                <el-tag size="small" type="info">{{ enumLabel('spaceType', data.spaceType) }}</el-tag>
                <el-tag v-if="data.houseCount" size="small" type="success">{{ data.houseCount }}</el-tag>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never">
          <div class="panel-head">
            <span v-if="space">{{ space.spaceName }} · {{ spacePathText }}</span>
            <span v-else class="muted">{{ t('bindingX.pickSpace') }}</span>
            <div class="spacer" />
            <el-button v-if="space" size="small" @click="loadSpaceDevices">{{ t('binding.refresh') }}</el-button>
          </div>

          <el-descriptions v-if="space" :column="3" border size="small" style="margin-bottom:10px">
            <el-descriptions-item :label="t('binding.spaceType')">
              {{ enumLabel('spaceType', space.spaceType) }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('binding.house')">
              {{ house ? house.houseName : t('binding.noHouse') }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('binding.affectedHouses')">
              {{ affectedHouses }}
            </el-descriptions-item>
          </el-descriptions>

          <el-alert v-if="houseWarning" type="warning" :closable="false" show-icon
                    :title="houseWarning" style="margin-bottom:10px" />

          <el-tabs v-model="tab" @tab-change="loadSpaceDevices">
            <el-tab-pane :label="t('binding.ownTab') + ' (' + boundRows.length + ')'" name="own" />
            <el-tab-pane :label="t('binding.inheritTab') + ' (' + inheritedRows.length + ')'" name="inherit" />
            <el-tab-pane :label="t('binding.unboundTab') + ' (' + filteredUnbound.length + ')'" name="unbound" />
          </el-tabs>

          <template v-if="tab === 'unbound'">
            <div class="toolbar" style="margin-bottom:8px">
              <el-input v-model="deviceKeyword" :placeholder="t('binding.searchDevice')" clearable
                        style="width:220px" />
              <el-select v-model="deviceType" clearable :placeholder="t('binding.category')"
                         style="width:140px">
                <el-option v-for="x in deviceTypes" :key="x" :label="enumLabel('deviceType', x)" :value="x" />
              </el-select>
              <el-button type="primary" :loading="binding" :disabled="!selectedUnbound.length"
                         @click="bindSelected">
                {{ t('bindingX.bindSelected', { n: selectedUnbound.length }) }}
              </el-button>
            </div>
            <el-table :data="filteredUnbound" border size="small" max-height="430"
                      @selection-change="(v) => (selectedUnbound = v)">
              <el-table-column type="selection" width="46" />
              <el-table-column prop="deviceName" :label="t('binding.deviceName')" min-width="160" />
              <el-table-column prop="deviceId" :label="t('binding.deviceId')" width="180" />
              <el-table-column prop="deviceType" :label="t('binding.category')" width="110">
                <template #default="{ row }">{{ enumLabel('deviceType', row.deviceType) }}</template>
              </el-table-column>
              <el-table-column prop="onlineStatus" :label="t('binding.online')" width="80">
                <template #default="{ row }">{{ row.onlineStatus === 1 ? t('bindingX.online') : t('bindingX.offline') }}</template>
              </el-table-column>
            </el-table>
          </template>

          <template v-else>
            <el-table :data="tab === 'own' ? boundRows : inheritedRows" border size="small" max-height="430"
                      :empty-text="t('bindingX.noDevices')">
              <el-table-column prop="deviceName" :label="t('binding.deviceName')" min-width="160" />
              <el-table-column prop="deviceId" :label="t('binding.deviceId')" width="180" />
              <el-table-column prop="deviceType" :label="t('binding.category')" width="110">
                <template #default="{ row }">{{ enumLabel('deviceType', row.deviceType) }}</template>
              </el-table-column>
              <el-table-column prop="spaceName" :label="t('binding.space')" width="140" />
              <el-table-column prop="onlineStatus" :label="t('binding.online')" width="80">
                <template #default="{ row }">{{ row.onlineStatus === 1 ? t('bindingX.online') : t('bindingX.offline') }}</template>
              </el-table-column>
              <el-table-column v-if="tab === 'own'" :label="t('binding.actions')" width="90" fixed="right">
                <template #default="{ row }">
                  <el-button link type="danger" @click="unbind(row)">{{ t('binding.unbind') }}</el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="importVisible" :title="t('bindingX.importTitle')" width="640px">
      <el-alert type="info" :closable="false" show-icon :title="t('bindingX.importHint')"
                style="margin-bottom:10px" />
      <div class="toolbar" style="margin-bottom:10px">
        <el-button size="small" @click="downloadTemplate">{{ t('bindingX.downloadTemplate') }}</el-button>
        <span class="muted">{{ t('bindingX.importTemplateHint') }}</span>
      </div>
      <el-upload :auto-upload="false" :limit="1" accept=".csv" :on-change="onImportFile"
                 :file-list="importFiles">
        <el-button type="primary" plain>{{ t('bindingX.chooseCsv') }}</el-button>
      </el-upload>
      <div v-if="importResult" style="margin-top:12px">
        <el-alert :type="importResult.failed ? 'warning' : 'success'" :closable="false" show-icon
                  :title="t('bindingX.importResult', {
                    total: importResult.total, spaces: importResult.spacesCreated,
                    houses: importResult.housesCreated, devices: importResult.devicesCreated,
                    failed: importResult.failed
                  })" />
        <el-table v-if="importResult.errors && importResult.errors.length" :data="importResult.errors"
                  border size="small" max-height="220" style="margin-top:8px">
          <el-table-column prop="line" :label="t('bindingX.rowNo')" width="70" />
          <el-table-column prop="message" :label="t('bindingX.issue')" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">{{ t('binding.close') }}</el-button>
        <el-button type="primary" :loading="importing" :disabled="!importFile"
                   @click="doImport">{{ t('bindingX.startImport') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const { t } = useI18n()
const orgs = ref([])
const orgId = ref('')
const tree = ref([])
const treeRef = ref(null)
const space = ref(null)
const spacePathText = ref('')
const house = ref(null)
const affectedHouses = ref(0)
const houseWarning = ref('')
const tab = ref('own')
const boundRows = ref([])
const inheritedRows = ref([])
const unbound = ref([])
const selectedUnbound = ref([])
const houseKeyword = ref('')
const houseHits = ref([])
const deviceKeyword = ref('')
const deviceType = ref('')
const binding = ref(false)
const importVisible = ref(false)
const importing = ref(false)
const importFiles = ref([])
const importFile = ref(null)
const importResult = ref(null)

const deviceTypes = ['LOCK', 'ACCESS', 'BARRIER', 'ELEVATOR', 'WATER_METER', 'ELEC_METER',
  'GAS_METER', 'HEAT_METER', 'CAMERA', 'SENSOR', 'CAR_LOCK', 'CONTROLLER', 'OTHER']

const filteredUnbound = computed(() => {
  const k = deviceKeyword.value.trim().toLowerCase()
  return unbound.value.filter((d) => {
    if (deviceType.value && d.deviceType !== deviceType.value) return false
    if (!k) return true
    return String(d.deviceName || '').toLowerCase().includes(k)
      || String(d.deviceId || '').toLowerCase().includes(k)
  })
})

function nodeById(nodes, id) {
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const hit = nodeById(n.children, id)
    if (hit) return hit
  }
  return null
}

async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 100 } })
    orgs.value = d.rows || []
    if (!orgId.value && orgs.value.length) orgId.value = String(orgs.value[0].id)
    if (orgId.value) await loadTree()
  } catch (e) { orgs.value = [] }
}

async function loadTree() {
  if (!orgId.value) { tree.value = []; return }
  try {
    tree.value = await req.get('/spaces/tree', { params: { orgId: orgId.value } }) || []
  } catch (e) { tree.value = [] }
}


async function onOrgChange() {
  space.value = null
  house.value = null
  houseWarning.value = ''
  boundRows.value = []
  inheritedRows.value = []
  unbound.value = []
  houseHits.value = []
  tab.value = 'own'
  await loadTree()
}

async function selectSpace(data) {
  space.value = data
  spacePathText.value = data.fullName || data.spaceName || ''
  house.value = null
  houseWarning.value = ''
  houseHits.value = []
  tab.value = 'own'
  await loadSpaceInfo()
  await loadSpaceDevices()
}

async function pickHouse(h) {
  const node = nodeById(tree.value, h.spaceId)
  houseHits.value = []
  if (node) {
    if (treeRef.value?.getNode) treeRef.value.getNode(node.id)?.expand?.()
    space.value = node
    spacePathText.value = node.fullName || node.spaceName || ''
    house.value = h
    tab.value = 'own'
    await loadSpaceDevices()
  }
}

async function searchHouse() {
  const k = houseKeyword.value.trim()
  if (!k) { houseHits.value = []; return }
  try {
    const d = await req.get('/houses', { params: { pageNum: 1, pageSize: 10, keyword: k } })
    houseHits.value = d.rows || []
  } catch (e) { houseHits.value = [] }
}

async function loadSpaceInfo() {
  if (!space.value) return
  try {
    const exact = await req.get('/houses', {
      params: { pageNum: 1, pageSize: 5, spaceId: space.value.id }
    })
    const rows = exact.rows || []
    house.value = rows[0] || null
    if (rows.length > 1) {
      houseWarning.value = t('bindingX.multiHouseWarning', { n: rows.length })
    }
    const affected = await req.get('/houses', {
      params: { pageNum: 1, pageSize: 1, spaceId: space.value.id, includeChildren: true }
    })
    affectedHouses.value = Number(affected.total || 0)
  } catch (e) {
    house.value = null
    affectedHouses.value = 0
  }
}

async function loadSpaceDevices() {
  if (!space.value) return
  const id = space.value.id
  try {
    const d = await req.get('/devices', { params: { pageNum: 1, pageSize: 300, spaceId: id } })
    boundRows.value = d.rows || []
    unbound.value = await req.get('/devices/unbound') || []
    inheritedRows.value = await loadInherited(id)
  } catch (e) {
    ElMessage.error(t('bindingX.loadFailed'))
  }
}

async function loadInherited(id) {
  const node = nodeById(tree.value, id)
  const path = (node?.spacePath || '').split('/').filter(Boolean)
  const out = []
  for (const pid of path) {
    try {
      const d = await req.get('/devices', { params: { pageNum: 1, pageSize: 200, spaceId: pid } })
      for (const x of d.rows || []) out.push({ ...x, spaceName: x.spaceName || pid })
    } catch (e) { /* ignore one ancestor */ }
  }
  return out
}

async function bindSelected() {
  if (!space.value || !selectedUnbound.value.length) return
  binding.value = true
  let ok = 0
  try {
    for (const d of selectedUnbound.value) {
      await req.post(`/devices/${d.id}/bind`, { spaceId: space.value.id })
      ok++
    }
    ElMessage.success(t('bindingX.bindDone', { n: ok }))
    selectedUnbound.value = []
    await loadSpaceDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('bindingX.bindFailed'))
  } finally { binding.value = false }
}

async function unbind(row) {
  await ElMessageBox.confirm(t('bindingX.unbindConfirm'), t('binding.unbind'), { type: 'warning' })
  try {
    await req.post(`/devices/${row.id}/bind`, { spaceId: null })
    ElMessage.success(t('bindingX.unbound'))
    await loadSpaceDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('bindingX.unbindFailed'))
  }
}

function reloadTargets() {
  if (orgId.value) loadTree()
  if (space.value) loadSpaceDevices()
}

function openImport() {
  importVisible.value = true
  importResult.value = null
  importFiles.value = []
  importFile.value = null
}

function onImportFile(file) {
  importFile.value = file.raw
  importFiles.value = [file]
  importResult.value = null
}

function downloadTemplate() {
  const head = t('bindingX.templateHeader')
  const sample = t('bindingX.templateSample')
  const blob = new Blob(['\ufeff' + head + '\n' + sample + '\n'], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = t('bindingX.templateFileName')
  a.click()
  URL.revokeObjectURL(a.href)
}

async function doImport() {
  if (!importFile.value) return
  importing.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile.value)
    importResult.value = await req.post('/houses/import-batch', fd)
    ElMessage.success(t('bindingX.importDone'))
    if (orgId.value) await loadTree()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('bindingX.importFailed'))
  } finally { importing.value = false }
}

onMounted(loadOrgs)
</script>

<style scoped>
.binding-page { min-height: 70vh; }
.panel-head { display: flex; gap: 8px; align-items: center; padding: 8px 12px; font-weight: 600; }
.tree-node { display: flex; gap: 6px; align-items: center; width: 100%; }
.house-hits { border-bottom: 1px solid var(--el-border-color-lighter); max-height: 150px; overflow: auto; }
.hit { padding: 6px 10px; cursor: pointer; display: flex; gap: 8px; }
.hit:hover { background: var(--el-fill-color-light); }
</style>
