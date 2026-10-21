<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">运维操作台</h3>
      <el-tag size="small" type="info">人员/房源状态 · 工单全流程</el-tag>
      <div class="spacer" />
      <el-button @click="loadAll">刷新</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              title="状态变更会同步影响门禁授权与业务校验，请谨慎操作"
              style="margin-bottom:12px" />

    <el-tabs v-model="tab">
      <!-- 人员 -->
      <el-tab-pane label="人员状态" name="person">
        <div class="toolbar" style="margin-bottom:10px">
          <el-input v-model="pid" placeholder="人员ID" style="width:200px" />
          <el-select v-model="pStatus" style="width:160px">
            <el-option label="正常 NORMAL" value="NORMAL" />
            <el-option label="冻结 FROZEN" value="FROZEN" />
            <el-option label="注销 CANCELLED" value="CANCELLED" />
          </el-select>
          <el-button type="primary" :loading="saving" @click="setPersonStatus">
            变更人员状态
          </el-button>
        </div>
                <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="filters.person" placeholder="姓名 / 证件号 / 手机" clearable style="width:200px"
                    data-testid="oc-person" @keyup.enter="loadAll" />
          <el-button type="primary" @click="loadAll">查询</el-button>
          <el-button @click="resetFilter('person')">清空</el-button>
        </div>
<el-table :data="persons" border size="small" max-height="380">
          <el-table-column prop="id" label="ID" width="180" />
          <el-table-column prop="personName" label="姓名" width="120" />
          <el-table-column prop="phone" label="手机" width="140" />
          <el-table-column prop="personStatus" label="状态" width="120">
            <template #default="{ row }">{{ row.personStatusLabel || enumLabel('personStatus', row.personStatus) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="pid = row.id; pStatus =
                row.personStatus || 'NORMAL'">选中</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 房源 -->
      <el-tab-pane label="房源状态" name="house">
        <div class="toolbar" style="margin-bottom:10px">
          <el-input v-model="hid" placeholder="房源ID" style="width:200px" />
          <el-select v-model="hStatus" style="width:170px">
            <el-option label="空置 VACANT" value="VACANT" />
            <el-option label="已租 OCCUPIED" value="OCCUPIED" />
            <el-option label="锁定 LOCKED" value="LOCKED" />
            <el-option label="维修 REPAIR" value="REPAIR" />
            <el-option label="停用 OFFLINE" value="OFFLINE" />
          </el-select>
          <el-button type="primary" :loading="saving" @click="setHouseStatus">
            变更房源状态
          </el-button>
        </div>
                <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="filters.house" placeholder="房源编号 / 名称" clearable style="width:200px"
                    data-testid="oc-house" @keyup.enter="loadAll" />
          <el-button type="primary" @click="loadAll">查询</el-button>
          <el-button @click="resetFilter('house')">清空</el-button>
        </div>
<el-table :data="houses" border size="small" max-height="380">
          <el-table-column prop="houseCode" label="编号" width="160" />
          <el-table-column prop="houseName" label="名称" min-width="140" />
          <el-table-column prop="houseStatus" label="状态" width="120">
            <template #default="{ row }">{{ row.houseStatusLabel || enumLabel('houseStatus', row.houseStatus) }}</template>
          </el-table-column>
          <el-table-column prop="area" label="面积" width="90" />
          <el-table-column label="操作" width="110">
            <template #default="{ row }">
              <el-button link type="primary" @click="hid = row.id; hStatus =
                row.houseStatus || 'VACANT'">选中</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 工单 -->
      <el-tab-pane label="工单流程" name="order">
                <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="filters.order" placeholder="工单号 / 标题" clearable style="width:200px"
                    data-testid="oc-order" @keyup.enter="loadAll" />
          <el-button type="primary" @click="loadAll">查询</el-button>
          <el-button @click="resetFilter('order')">清空</el-button>
        </div>
<el-table :data="orders" border size="small" max-height="440">
          <el-table-column prop="workorderNo" label="工单号" width="170" />
          <el-table-column prop="orderType" label="类型" width="120">
            <template #default="{ row }">{{ row.workOrderTypeLabel || enumLabel('orderType', row.orderType) }}</template>
          </el-table-column>
          <el-table-column prop="orderStatus" label="状态" width="120">
            <template #default="{ row }">{{ row.workOrderStatusLabel || enumLabel('orderStatus', row.orderStatus) }}</template>
          </el-table-column>
          <el-table-column prop="orderTitle" label="标题" min-width="150" />
          <el-table-column label="流程操作" width="380" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="assign(row)">派单</el-button>
              <el-button link @click="orderAct(row, 'accept', '接单')">接单</el-button>
              <el-button link @click="orderAct(row, 'start', '开始')">开始</el-button>
              <el-button link @click="orderAct(row, 'finish', '完成')">完成</el-button>
              <el-button link type="success" @click="orderAct(row, 'close', '关单')">
                关单</el-button>
              <el-button link type="danger" @click="orderAct(row, 'cancel', '取消')">
                取消</el-button>
              <el-button link type="warning" @click="orderAct(row, 'reject', '退回')">
                退回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const TABS = ['person', 'house', 'order']
const route = useRoute()
const router = useRouter()
const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : 'person')
const filters = reactive({ person: '', house: '', order: '' })
function resetFilter(k) {
  filters[k] = ''
  loadAll()
}
watch(() => route.params.tab, (v) => {
  const t = TABS.includes(v) ? v : 'person'
  if (t !== tab.value) tab.value = t
})
watch(tab, (v) => {
  if (route.params.tab !== v) router.replace('/ops-center/' + v)
})
const saving = ref(false)
const pid = ref(null)
const hid = ref(null)
const pStatus = ref('NORMAL')
const hStatus = ref('VACANT')
const persons = ref([])
const houses = ref([])
const orders = ref([])

async function loadAll() {
  try {
    const p = await req.get('/persons', { params: { pageNum: 1, pageSize: 20, keyword: filters.person || undefined } })
    persons.value = p.rows || []
  } catch (e) { persons.value = [] }
  try {
    const h = await req.get('/houses', { params: { pageNum: 1, pageSize: 20, keyword: filters.house || undefined } })
    houses.value = h.rows || []
  } catch (e) { houses.value = [] }
  try {
    const o = await req.get('/workorders', { params: { pageNum: 1, pageSize: 20, keyword: filters.order || undefined } })
    orders.value = o.rows || []
  } catch (e) { orders.value = [] }
}

async function setPersonStatus() {
  if (!pid.value) { ElMessage.warning('请选择或填写人员ID'); return }
  saving.value = true
  try {
    await req.post(`/persons/${pid.value}/status`, { status: pStatus.value })
    ElMessage.success('人员状态已更新'); loadAll()
  } finally { saving.value = false }
}

async function setHouseStatus() {
  if (!hid.value) { ElMessage.warning('请选择或填写房源ID'); return }
  saving.value = true
  try {
    await req.post(`/houses/${hid.value}/status`, { status: hStatus.value })
    ElMessage.success('房源状态已更新'); loadAll()
  } finally { saving.value = false }
}

// AssignCmd{assignUserId, assignUserName, assignUserPhone, content}
async function assign(row) {
  const { value } = await ElMessageBox.prompt('请输入处理人工号（用户ID）', '派单',
    { inputValue: '1' })
  await req.post(`/workorders/${row.id}/assign`, {
    assignUserId: String(value).trim(), assignUserName: '维修员', assignUserPhone: '',
    content: '派单处理'
  })
  ElMessage.success('已派单'); loadAll()
}

// ActionCmd{operatorId, operatorName, content, handleResult}
async function orderAct(row, path, label) {
  const { value } = await ElMessageBox.prompt('处理说明（可空）', label,
    { inputValue: '' })
  await req.post(`/workorders/${row.id}/${path}`, {
    operatorId: 1, operatorName: '管理员', content: value || label,
    handleResult: label
  })
  ElMessage.success(label + '成功'); loadAll()
}

onMounted(loadAll)
</script>
