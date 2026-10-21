<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">设备管理</h3>
      <el-tag size="small" type="info">
        在线 {{ stats.online ?? 0 }} / 共 {{ stats.total ?? 0 }}
        （{{ stats.onlineRate ?? 0 }}%）
      </el-tag>
      <div class="spacer" />
      <el-input v-model="query.spaceId" placeholder="空间ID" clearable
                style="width:210px" @keyup.enter="load" />
      <el-select v-model="query.onlineStatus" placeholder="在线状态" clearable
                 style="width:130px" @change="load">
        <el-option label="在线" :value="1" />
        <el-option label="离线" :value="0" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="设备表按空间关联（无 houseId/lockId 列）；门锁与房源关系由绑定记录推导"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="deviceId" label="设备ID" width="200">
        <template #default="{ row }">{{ row.deviceIdName || row.deviceId }}</template>
      </el-table-column>
      <el-table-column prop="deviceName" label="设备名称" min-width="150" />
      <el-table-column prop="deviceType" label="类型" width="120">
        <template #default="{ row }">{{ row.deviceTypeLabel || enumLabel('deviceType', row.deviceType) }}</template>
      </el-table-column>
      <el-table-column prop="deviceMac" label="MAC" width="160" />
      <el-table-column prop="spaceId" label="空间" width="140">
        <template #default="{ row }">{{ row.spaceIdName || row.spaceId }}</template>
      </el-table-column>
      <el-table-column prop="onlineStatus" label="在线" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.onlineStatus === 1 ? 'success' : 'info'">
            {{ row.onlineStatus === 1 ? '在线' : '离线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="battery" label="电量" width="90">
        <template #default="{ row }">
          <span v-if="row.battery != null && row.battery < 20"
                style="color:#f56c6c">{{ row.battery }}%</span>
          <span v-else>{{ row.battery ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="deviceStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.deviceStatusLabel || enumLabel('deviceStatus', row.deviceStatus) }}</template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />
  </div>
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { devApi } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const stats = ref({})
const query = reactive({ pageNum: 1, pageSize: 20, spaceId: '', onlineStatus: '' })

async function load() {
  loading.value = true
  try {
    const data = await devApi.devices({
      pageNum: query.pageNum, pageSize: query.pageSize,
      spaceId: query.spaceId || undefined,
      onlineStatus: query.onlineStatus === '' ? undefined : query.onlineStatus
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
    stats.value = await devApi.deviceStats()
  } catch (e) { rows.value = [] } finally { loading.value = false }
}

const query0 = JSON.parse(JSON.stringify(query))
function resetQuery() {
  Object.assign(query, query0)
  load()
}

onMounted(load)
</script>
