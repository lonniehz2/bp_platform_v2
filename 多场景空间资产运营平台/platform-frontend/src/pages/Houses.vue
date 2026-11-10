<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import DataTable from '../components/DataTable.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'

const project = ref(null)
const houses = ref([])
const status = ref('')
const page = ref(1)
const route = useRoute()
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
  { key: 'houseCode', title: '房源编码', width: '150px' },
  { key: 'houseName', title: '名称' },
  { key: 'layoutType', title: '户型', width: '100px' },
  { key: 'orientation', title: '朝向', width: '70px' },
  { key: 'floor', title: '楼层', width: '80px' },
  { key: 'area', title: '建筑面积', width: '90px' },
  { key: 'innerArea', title: '套内面积', width: '90px' },
  { key: 'houseStatus', title: '房态', width: '90px' },
  { key: 'actions', title: '操作', width: '70px' }
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
    if (Number(editForm.area) < 0 || Number(editForm.innerArea) < 0) throw new Error('面积不能为负数')
    if (Number(editForm.floorNo) < 1 || Number(editForm.totalFloors) < 1 || Number(editForm.floorNo) > Number(editForm.totalFloors)) throw new Error('楼层需满足 1 ≤ 所在楼层 ≤ 总楼层')
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
      <div class="panel-head"><div><h2>房源台账</h2><p>{{ project?.orgName || '未选择项目' }} · 可出租房源和房态</p></div>
        <div class="row"><span class="badge blue">{{ houses.length }} 套</span><RouterLink to="/spaces">空间层级</RouterLink></div>
      </div>
      <div class="row">
        <div class="field"><label>房态</label><select v-model="status" @change="page = 1"><option value="">全部</option><option value="VACANT">空置</option><option value="ALLOCATED">已配租</option><option value="OCCUPIED">已入住</option></select></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>房源列表</h2><span class="small muted">房源由可出租空间生成</span></div>
      <div class="row" style="margin-bottom:8px">
        <input v-model="houseQuery" placeholder="搜索房源编码/名称" style="max-width:280px" @input="page = 1" />
      </div>
      <DataTable :rows="paged" :columns="houseColumns" :row-class="rowClass" :page="page" :page-size="10" :total="filtered.length" empty-text="暂无房源" @update:page="page = $event">
        <template #cell-floor="{ row }">{{ row.floorNo || '-' }}/{{ row.totalFloors || '-' }}</template>

        <template #cell-area="{ row }">{{ row.area || '-' }}</template>
        <template #cell-innerArea="{ row }">{{ row.innerArea || '-' }}</template>
        <template #cell-houseStatus="{ row }"><span class="badge" :class="row.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ row.houseStatus }}</span></template>
        <template #cell-actions="{ row }"><button class="sm" @click="openEdit(row)">编辑</button><button class="sm" @click="detailHouse = row">关联</button></template>
      </DataTable>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>编辑房源</h2><button class="sm" @click="editing = null">关闭</button></div>
        <div class="field"><label>房源</label><div class="mono">{{ editing.houseCode }} · {{ editing.houseName }}</div></div>
        <div class="row">
          <div class="field"><label>建筑面积</label><input v-model.number="editForm.area" type="number" /></div>
          <div class="field"><label>套内面积</label><input v-model.number="editForm.innerArea" type="number" /></div>
          <div class="field"><label>房态</label><select v-model="editForm.houseStatus"><option value="VACANT">空置</option><option value="ALLOCATED">已配租</option><option value="OCCUPIED">已入住</option><option value="FROZEN">冻结</option></select></div>
          <div class="field"><label>资产类型</label><input v-model="editForm.assetTypeCode" /></div>
          <div class="field"><label>户型</label><input v-model="editForm.layoutType" placeholder="如 二室一厅" /></div>
          <div class="field"><label>朝向</label><select v-model="editForm.orientation"><option value="">未填写</option><option value="SOUTH">南</option><option value="NORTH">北</option><option value="EAST">东</option><option value="WEST">西</option><option value="SOUTHEAST">东南</option><option value="SOUTHWEST">西南</option></select></div>
          <div class="field"><label>所在楼层</label><input v-model.number="editForm.floorNo" type="number" min="1" /></div>
          <div class="field"><label>总楼层</label><input v-model.number="editForm.totalFloors" type="number" min="1" /></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" @click="saveEdit">保存</button></div>
      </div>
    </div>

    <div v-if="detailHouse" class="modal-mask" @click.self="detailHouse = null">
      <div class="modal" style="max-width:760px">
        <div class="panel-head"><div><h2>{{ detailHouse.houseCode }} · {{ detailHouse.houseName }}</h2><p class="small muted">房源关联信息</p></div><button class="sm" @click="detailHouse = null">关闭</button></div>
        <EntityDetailTabs type="HOUSE" :entity-id="detailHouse.id" />
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(tr.highlight-row) { background:var(--brand-soft); }
</style>
