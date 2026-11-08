<template>
  <div class="units-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyUnit.noProject')" />
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">{{ t('propertyUnit.title') }}</div>
        <el-select v-model="buildingId" clearable :placeholder="t('propertyUnit.allBuildings')"
                   style="width:220px" @change="loadUnits">
          <el-option v-for="b in buildings" :key="b.id" :label="b.buildingName" :value="b.id" />
        </el-select>
        <el-button @click="loadUnits">{{ t('propertyUnit.refresh') }}</el-button>
        <div class="spacer" />
        <span class="muted">{{ t('propertyUnit.count', { n: units.length }) }}</span>
        <el-button @click="openBuilding">{{ t('propertyUnit.addBuilding') }}</el-button>
        <el-button type="primary" @click="openRoom">{{ t('propertyUnit.addRoom') }}</el-button>
      </div>
      <el-table :data="units" border size="small" v-loading="loading">
        <el-table-column prop="houseCode" :label="t('propertyUnit.code')" width="150" />
        <el-table-column prop="houseName" :label="t('propertyUnit.house')" min-width="190" />
        <el-table-column prop="spaceName" :label="t('propertyUnit.room')" width="120" />
        <el-table-column prop="area" :label="t('propertyUnit.area')" width="100" />
        <el-table-column prop="houseStatus" :label="t('propertyUnit.status')" width="120" />
        <el-table-column prop="ownerName" :label="t('propertyUnit.owner')" min-width="150">
          <template #default="{ row }">
            <span v-if="row.ownerName">{{ row.ownerName }}</span>
            <span v-else class="muted">{{ t('propertyUnit.noOwner') }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('propertyUnit.actions')" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openOwners(row)">{{ t('propertyUnit.owners') }}</el-button>
            <el-button link type="success" @click="openAssign(row)">{{ t('propertyUnit.assign') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="buildingVisible" :title="t('propertyUnit.addBuilding')" width="440px">
      <el-form :model="buildingForm" label-width="100px">
        <el-form-item :label="t('propertyUnit.buildingName')" required>
          <el-input v-model="buildingForm.buildingName" />
        </el-form-item>
        <el-form-item :label="t('propertyUnit.area')">
          <el-input-number v-model="buildingForm.area" :min="0" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="buildingVisible = false">{{ t('propertyUnit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveBuilding">{{ t('propertyUnit.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="roomVisible" :title="t('propertyUnit.addRoom')" width="440px">
      <el-form :model="roomForm" label-width="100px">
        <el-form-item :label="t('propertyUnit.building')" required>
          <el-select v-model="roomForm.buildingId" style="width:100%">
            <el-option v-for="b in buildings" :key="b.id" :label="b.buildingName" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyUnit.roomName')" required>
          <el-input v-model="roomForm.roomName" />
        </el-form-item>
        <el-form-item :label="t('propertyUnit.area')" required>
          <el-input-number v-model="roomForm.area" :min="1" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roomVisible = false">{{ t('propertyUnit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveRoom">{{ t('propertyUnit.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="ownerVisible" :title="t('propertyUnit.owners')" width="600px">
      <div class="muted" style="margin-bottom:8px">{{ currentUnit?.houseName }}</div>
      <el-table :data="owners" border size="small" max-height="280">
        <el-table-column prop="personName" :label="t('propertyUnit.ownerName')" />
        <el-table-column prop="relationType" :label="t('propertyUnit.relation')" width="110" />
        <el-table-column prop="isPrimary" :label="t('propertyUnit.primary')" width="80">
          <template #default="{ row }">{{ row.isPrimary === 1 ? '✓' : '' }}</template>
        </el-table-column>
        <el-table-column :label="t('propertyUnit.actions')" width="100">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeOwner(row)">{{ t('propertyUnit.remove') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="ownerVisible = false">{{ t('propertyUnit.close') }}</el-button>
        <el-button type="primary" @click="openAssign(currentUnit)">{{ t('propertyUnit.assign') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="assignVisible" :title="t('propertyUnit.assign')" width="440px">
      <el-form :model="assignForm" label-width="100px">
        <el-form-item :label="t('propertyUnit.person')" required>
          <PersonPicker v-model="assignForm.personId" width="100%" />
        </el-form-item>
        <el-form-item :label="t('propertyUnit.relation')">
          <el-select v-model="assignForm.relationType" style="width:100%">
            <el-option label="OWNER" value="OWNER" />
            <el-option label="FAMILY" value="FAMILY" />
            <el-option label="TENANT" value="TENANT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyUnit.primary')">
          <el-switch v-model="assignForm.primary" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">{{ t('propertyUnit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="assign">{{ t('propertyUnit.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { usePropertyStore } from '@/store/property'
import PersonPicker from '@/components/PersonPicker.vue'

const { t } = useI18n()
const store = usePropertyStore()
const projectId = computed(() => store.projectId)
const buildings = ref([])
const buildingId = ref(null)
const units = ref([])
const owners = ref([])
const currentUnit = ref(null)
const loading = ref(false)
const saving = ref(false)
const ownerVisible = ref(false)
const assignVisible = ref(false)
const buildingVisible = ref(false)
const roomVisible = ref(false)
const assignForm = reactive({ personId: '', relationType: 'OWNER', primary: 1 })
const buildingForm = reactive({ buildingName: '', area: 0 })
const roomForm = reactive({ buildingId: null, roomName: '', area: 60 })

onMounted(async () => {
  await store.loadProjects()
  await loadBuildings()
  await loadUnits()
})
watch(projectId, async () => { buildingId.value = null; await loadBuildings(); await loadUnits() })

async function loadBuildings() {
  if (!projectId.value) return
  try { buildings.value = await req.get('/property/units/buildings', { params: { projectId: projectId.value } }) || [] }
  catch (e) { buildings.value = [] }
}

async function loadUnits() {
  if (!projectId.value) return
  loading.value = true
  try {
    units.value = await req.get('/property/units', {
      params: { projectId: projectId.value, buildingId: buildingId.value || undefined }
    }) || []
  } catch (e) { ElMessage.error(t('propertyUnit.loadFailed')) } finally { loading.value = false }
}

async function openOwners(row) {
  currentUnit.value = row
  ownerVisible.value = true
  owners.value = await req.get(`/property/units/${row.id}/owners`, {
    params: { projectId: projectId.value }
  }) || []
}

function openAssign(row) {
  if (!row) return
  currentUnit.value = row
  Object.assign(assignForm, { personId: '', relationType: 'OWNER', primary: 1 })
  assignVisible.value = true
}

function openBuilding() {
  Object.assign(buildingForm, { buildingName: '', area: 0 })
  buildingVisible.value = true
}

async function saveBuilding() {
  if (!buildingForm.buildingName.trim()) {
    ElMessage.warning(t('propertyUnit.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/units/buildings', buildingForm, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyUnit.saved'))
    buildingVisible.value = false
    await loadBuildings()
    await loadUnits()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyUnit.saveFailed'))
  } finally { saving.value = false }
}

function openRoom() {
  Object.assign(roomForm, { buildingId: buildingId.value || buildings.value[0]?.id || null, roomName: '', area: 60 })
  roomVisible.value = true
}

async function saveRoom() {
  if (!roomForm.buildingId || !roomForm.roomName.trim() || !roomForm.area) {
    ElMessage.warning(t('propertyUnit.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/units', roomForm, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyUnit.saved'))
    roomVisible.value = false
    await loadUnits()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyUnit.saveFailed'))
  } finally { saving.value = false }
}

async function assign() {
  if (!assignForm.personId) {
    ElMessage.warning(t('propertyUnit.personRequired'))
    return
  }
  saving.value = true
  try {
    await req.post(`/property/units/${currentUnit.value.id}/owners`, {
      personId: assignForm.personId, relationType: assignForm.relationType,
      isPrimary: assignForm.primary
    }, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyUnit.saved'))
    assignVisible.value = false
    await loadUnits()
    if (ownerVisible.value) await openOwners(currentUnit.value)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyUnit.saveFailed'))
  } finally { saving.value = false }
}

async function removeOwner(row) {
  await ElMessageBox.confirm(t('propertyUnit.removeConfirm'), t('propertyUnit.remove'), { type: 'warning' })
  try {
    await req.delete(`/property/units/owners/${row.id}`)
    await openOwners(currentUnit.value)
    await loadUnits()
  } catch (e) {
    ElMessage.error(t('propertyUnit.saveFailed'))
  }
}
</script>

<style scoped>
.units-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.spacer { flex: 1; }
.muted { color: #94a3b8; font-size: 12px; }
</style>
