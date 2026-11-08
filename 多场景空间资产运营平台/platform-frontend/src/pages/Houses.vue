<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import Pager from '../components/Pager.vue'

const project = ref(null)
const houses = ref([])
const status = ref('')
const page = ref(1)
const error = ref('')
const editing = ref(null)
const editForm = reactive({ area: 0, innerArea: 0, houseStatus: 'VACANT', assetTypeCode: '', layoutType: '', orientation: '', floorNo: 1, totalFloors: 1 })
const filtered = computed(() => status.value ? houses.value.filter(h => h.houseStatus === status.value) : houses.value)
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

onMounted(load)
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
      <div v-if="!filtered.length" class="empty">暂无房源</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>房源编码</th><th>名称</th><th>户型</th><th>朝向</th><th>楼层</th><th>建筑面积</th><th>套内面积</th><th>房态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="h in paged" :key="h.id">
              <td class="mono">{{ h.houseCode }}</td><td>{{ h.houseName }}</td>
              <td>{{ h.layoutType || '-' }}</td><td>{{ h.orientation || '-' }}</td><td>{{ h.floorNo || '-' }}/{{ h.totalFloors || '-' }}</td><td>{{ h.area || '-' }}</td><td>{{ h.innerArea || '-' }}</td>
              <td><span class="badge" :class="h.houseStatus === 'VACANT' ? 'green' : 'orange'">{{ h.houseStatus }}</span></td>
              <td><button class="sm" @click="openEdit(h)">编辑</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pager :total="filtered.length" :page="page" @update:page="page = $event" />
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
  </div>
</template>
