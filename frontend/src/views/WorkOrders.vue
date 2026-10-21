<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">工单与维保</h3>
      <el-select v-model="query.orderStatus" placeholder="状态" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
      <div class="spacer" />
      <el-button type="primary" @click="reload">刷新</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="orderNo" label="工单号" width="170" />
      <el-table-column prop="orderType" label="类型" width="110">
        <template #default="{ row }">{{ row.orderTypeLabel || enumLabel('orderType', row.orderType) }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.priority === 'URGENT' ? 'danger' : 'info'">
            {{ row.priority }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="orderStatus" label="状态" width="120">
        <template #default="{ row }">{{ row.orderStatusLabel || enumLabel('orderStatus', row.orderStatus) }}</template>
      </el-table-column>
      <el-table-column prop="slaOverdue" label="SLA" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.slaOverdue" type="danger" size="small">超时</el-tag>
          <span v-else class="muted">正常</span>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="170" />
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="act(row, 'accept')">接单</el-button>
          <el-button link type="primary" @click="act(row, 'start')">开始</el-button>
          <el-button link type="success" @click="finish(row)">完成</el-button>
          <el-button link @click="logs(row)">日志</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <el-drawer v-model="logVisible" title="工单日志" size="460px">
      <el-timeline>
        <el-timeline-item v-for="l in logList" :key="l.id" :timestamp="l.createTime">
          {{ l.action }} — {{ l.operatorName }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!logList.length" description="暂无日志" />
    </el-drawer>
  </div>
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { workOrderApi } from '@/api/modules'

const statuses = ['PENDING', 'ASSIGNED', 'ACCEPTED', 'PROCESSING', 'FINISHED',
  'CLOSED', 'CANCELLED']
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, orderStatus: '' })
const logVisible = ref(false)
const logList = ref([])

async function load() {
  loading.value = true
  try {
    const data = await workOrderApi.page({
      pageNum: query.pageNum, pageSize: query.pageSize,
      orderStatus: query.orderStatus || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}
function reload() { query.pageNum = 1; load() }

async function act(row, action) {
  await workOrderApi[action](row.id)
  ElMessage.success('操作成功')
  load()
}
async function finish(row) {
  await workOrderApi.finish(row.id, { finishRemark: '现场处理完成' })
  ElMessage.success('工单已完成')
  load()
}
async function logs(row) {
  logList.value = await workOrderApi.logs(row.id)
  logVisible.value = true
}
onMounted(load)
</script>
