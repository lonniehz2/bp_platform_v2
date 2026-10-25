<template>
  <div>
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索房源编号 / 名称" clearable
                style="width:240px" @keyup.enter="loadHouses" />
      <el-button type="primary" @click="loadHouses">搜索房源</el-button>
      <span class="muted" style="font-size:12px">
        设备只绑定空间；房源通过「房源 → 空间」定位，床位/房间继承上级设备
      </span>
    </div>

    <el-row :gutter="12">
      <!-- 左：房源 -->
      <el-col :span="8">
        <el-card shadow="never" body-style="padding:0">
          <div style="padding:8px 12px;font-weight:600;border-bottom:1px solid #eee">
            房源（{{ houses.length }}）
          </div>
          <el-table :data="houses" height="520" size="small" highlight-current-row
                    @current-change="pickHouse">
            <el-table-column prop="houseCode" label="编号" width="140" />
            <el-table-column prop="houseName" label="名称" min-width="120" />
            <el-table-column prop="houseStatus" label="状态" width="90">
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
              {{ current ? current.houseName + '（' + current.houseCode + '）' : '请选择房源' }}
              的设备
            </span>
            <div class="spacer" />
            <el-button v-if="current" type="primary" plain size="small"
                       @click="openBind">绑定设备</el-button>
            <el-button v-if="current" size="small" @click="loadDevices">刷新</el-button>
          </div>

          <el-tabs v-model="tab" @tab-change="loadDevices">
            <el-tab-pane label="本房源设备" name="own" />
            <el-tab-pane label="继承设备（上级空间）" name="inherit" />
          </el-tabs>

          <el-table :data="rows" v-loading="loading" size="small" border max-height="430">
            <el-table-column prop="deviceName" label="设备名称" min-width="160" />
            <el-table-column prop="deviceId" label="设备编号" width="170" />
            <el-table-column prop="deviceType" label="分类" width="110">
              <template #default="{ row }">{{ typeLabel(row.deviceType) }}</template>
            </el-table-column>
            <el-table-column prop="spaceId" label="绑定空间" width="150">
              <template #default="{ row }">
                {{ row.spaceName || row.spaceIdName || row.spaceId || '—' }}
              </template>
            </el-table-column>
            <el-table-column v-if="tab === 'inherit'" prop="scope" label="来源" width="100">
              <template #default="{ row }">{{ row.scope || '继承' }}</template>
            </el-table-column>
            <el-table-column prop="onlineStatus" label="在线" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.onlineStatus === 1 ? 'success' : 'info'">
                  {{ row.onlineStatus === 1 ? '在线' : '离线' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column v-if="tab === 'own'" label="操作" width="90" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" @click="unbind(row)">解绑</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 绑定设备 -->
    <el-dialog v-model="bindVisible" title="绑定设备到该房源空间" width="680px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="只显示尚未绑定空间的设备；绑定后住户可通过继承链获得该设备使用权限" />
      <el-table :data="unbound" v-loading="bindLoading" size="small" border max-height="330"
                @selection-change="(v) => (picked = v)">
        <el-table-column type="selection" width="46" />
        <el-table-column prop="deviceName" label="设备名称" min-width="160" />
        <el-table-column prop="deviceId" label="设备编号" width="180" />
        <el-table-column prop="deviceType" label="分类" width="110">
          <template #default="{ row }">{{ typeLabel(row.deviceType) }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="bindVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" :disabled="!picked.length"
                   @click="doBind">绑定选中（{{ picked.length }}）</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
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

const keyword = ref('')
const houses = ref([])
const current = ref(null)
const rows = ref([])
const loading = ref(false)
const tab = ref('own')
const devTypes = ref([])

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

onMounted(loadHouses)
</script>
