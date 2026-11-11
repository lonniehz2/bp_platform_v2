<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { sceneRoot } from '../scene'
import { api } from '../api'
import DataTable from '../components/DataTable.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'

const project = ref(null)
const houses = ref([])
const status = ref('')
const page = ref(1)
const route = useRoute()
const { t } = useI18n()
const houseQuery = ref('')
const error = ref('')
const editing = ref(null)
const detailHouse = ref(null)
const editForm = reactive({ area: 0, innerArea: 0, houseStatus: 'VACANT', assetTypeCode: '', layoutType: '', orientation: '', floorNo: 1, totalFloors: 1 })
const filtered = computed(() => {
  let rows = status.value ? houses.value.filter(h => h.houseStatus === status.value) : houses.value
  const q = houseQuery.value.trim().toLowerCase()
  if (q) rows = rows.filter(h => (String(h.houseCode) + ' ' + String(h.houseName || '')).toLowerCase().includes(q))
  return rows
})
const rowClass = (row) => String(row.id) === String(route.query.id) ? 'highlight-row' : ''
const houseColumns = [
  { key: 'houseCode', title: t('houses.title') + ' Code', width: '150px' },
  { key: 'houseName', title: t('houses.house') },
  { key: 'layoutType', title: t('houses.layout'), width: '100px' },
  { key: 'orientation', title: t('houses.orientation'), width: '70px' },
  { key: 'floor', title: t('houses.floorValue'), width: '80px' },
  { key: 'area', title: t('houses.area'), width: '90px' },
  { key: 'innerArea', title: t('houses.innerArea'), width: '90px' },
  { key: 'houseStatus', title: t('houses.status'), width: '90px' },
  { key: 'actions', title: t('common.action'), width: '70px' }
]
const paged = computed(() => filtered.value.slice((page.value - 1) * 10, page.value * 10))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) houses.value = await api.houses(project.value.id)
  } catch (e) { error.value = e.message }
}

function openEdit(h) {
  editing.value = h
  editForm.area = h.area || 0; editForm.innerArea = h.innerArea || 0
  editForm.houseStatus = h.houseStatus || 'VACANT'; editForm.assetTypeCode = h.assetTypeCode || ''
  editForm.layoutType = h.layoutType || ''; editForm.orientation = h.orientation || ''
  editForm.floorNo = h.floorNo || 1; editForm.totalFloors = h.totalFloors || 1
}

async function saveEdit() {
  try {
    if (Number(editForm.area) < 0 || Number(editForm.innerArea) < 0) throw new Error(t('houses.areaNegative'))
    if (Number(editForm.floorNo) < 1 || Number(editForm.totalFloors) < 1 || Number(editForm.floorNo) > Number(editForm.totalFloors)) throw new Error(t('houses.floorInvalid'))
    await api.updateHouse(project.value.id, editing.value.id, { ...editForm })
    editing.value = null
    await load()
  } catch (e) { error.value = e.message }
}

onMounted(async () => {
  await load()
  const id = String(route.query.id || '')
  const found = houses.value.find(h => String(h.id) === id)
  if (found) houseQuery.value = found.houseName || found.houseCode || ''
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('houses.title') }}</h2><p>{{ project?.orgName || t('houses.noProject') }} · {{ t('houses.subtitle') }}</p></div>
        <div class="row"><span class="badge blue">{{ houses.length }} {{ t('houses.count') }}</span><RouterLink :to="sceneRoot() + '/spaces'">{{ t('houses.spaces') }}</RouterLink></div>
      </div>
      <div class="row">
        <div class="field"><label>{{ t('houses.status') }}</label><select v-model="status" @change="page = 1"><option value="">{{ t('houses.all') }}</option><option value="VACANT">{{ t('houses.vacant') }}</option><option value="ALLOCATED">{{ t('houses.allocated') }}</option><option value="OCCUPIED">{{ t('houses.occupied') }}</option></select></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('houses.list') }}</h2><span class="small muted">{{ t('houses.listHint') }}</span></div>
      <div class="row" style="margin-bottom:8px">
        <input v-model="houseQuery" :placeholder="t('houses.search')" style="max-width:280px" @input="page = 1" />
      </div>
      <DataTable :rows="paged" :columns="houseColumns" :row-class="rowClass" :page="page" :page-size="10" :total="filtered.length" :empty-text="t('houses.empty')" @update:page="page = $event">
        <template #cell-floor="{ row }">{{ row.floorNo || '-' }}/{{ row.totalFloors || '-' }}</template>

        <template #cell-area="{ row }">{{ row.area || '-' }}</template>
        <template #cell-innerArea="{ row }">{{ row.innerArea || '-' }}</template>
        <template #cell-houseStatus="{ row }"><span class="badge" :class="row.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ enumLabel(row.houseStatus) }}</span></template>
        <template #cell-actions="{ row }"><button class="sm" @click="openEdit(row)">{{ t('houses.edit') }}</button><RouterLink class="sm" :to="`${sceneRoot()}/detail/HOUSE/${row.id}`">{{ t('houses.detail') }}</RouterLink></template>
      </DataTable>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('houses.editTitle') }}</h2><button class="sm" @click="editing = null">{{ t('houses.close') }}</button></div>
        <div class="field"><label>{{ t('houses.house') }}</label><div class="mono">{{ editing.houseCode }} · {{ editing.houseName }}</div></div>
        <div class="row">
          <div class="field"><label>{{ t('houses.area') }}</label><input v-model.number="editForm.area" type="number" /></div>
          <div class="field"><label>{{ t('houses.innerArea') }}</label><input v-model.number="editForm.innerArea" type="number" /></div>
          <div class="field"><label>{{ t('houses.status') }}</label><select v-model="editForm.houseStatus"><option value="VACANT">{{ t('houses.vacant') }}</option><option value="ALLOCATED">{{ t('houses.allocated') }}</option><option value="OCCUPIED">{{ t('houses.occupied') }}</option><option value="FROZEN">{{ t('houses.frozen') }}</option></select></div>
          <div class="field"><label>{{ t('houses.assetType') }}</label><input v-model="editForm.assetTypeCode" /></div>
          <div class="field"><label>{{ t('houses.layout') }}</label><input v-model="editForm.layoutType" :placeholder="t('houses.layoutPlaceholder')" /></div>
          <div class="field"><label>{{ t('houses.orientation') }}</label><select v-model="editForm.orientation"><option value="">{{ t('houses.unspecified') }}</option><option value="SOUTH">{{ t('houses.south') }}</option><option value="NORTH">{{ t('houses.north') }}</option><option value="EAST">{{ t('houses.east') }}</option><option value="WEST">{{ t('houses.west') }}</option><option value="SOUTHEAST">{{ t('houses.southeast') }}</option><option value="SOUTHWEST">{{ t('houses.southwest') }}</option></select></div>
          <div class="field"><label>{{ t('houses.floor') }}</label><input v-model.number="editForm.floorNo" type="number" min="1" /></div>
          <div class="field"><label>{{ t('houses.totalFloors') }}</label><input v-model.number="editForm.totalFloors" type="number" min="1" /></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" @click="saveEdit">{{ t('houses.save') }}</button></div>
      </div>
    </div>

    <div v-if="detailHouse" class="modal-mask" @click.self="detailHouse = null">
      <div class="modal" style="max-width:760px">
        <div class="panel-head"><div><h2>{{ detailHouse.houseCode }} · {{ detailHouse.houseName }}</h2><p class="small muted">{{ t('houses.relation') }}</p></div><button class="sm" @click="detailHouse = null">{{ t('houses.close') }}</button></div>
        <EntityDetailTabs type="HOUSE" :entity-id="detailHouse.id" />
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(tr.highlight-row) { background:var(--brand-soft); }
</style>
