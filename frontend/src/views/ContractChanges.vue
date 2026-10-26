<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">合同变更</h3>
      <el-tag size="small" type="info">调租 / 租期 / 承租人变更，批准后写回合同</el-tag>
      <div class="spacer" />
      <el-select v-model="query.changeStatus" placeholder="状态" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="changeNo" label="变更号" width="170" />
      <el-table-column prop="contractId" label="合同" width="200">
        <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
      </el-table-column>
      <el-table-column label="变更类型" width="130">
        <template #default="{ row }">
          {{ row.changeTypeLabel || enumLabel('changeType', row.changeType) }}
        </template>
      </el-table-column>
      <el-table-column prop="effectiveDate" label="生效日" width="120" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.approveStatus === 'APPROVED' ? 'success'
            : (row.approveStatus === 'REJECTED' ? 'danger' : 'warning')">
            {{ row.approveStatusLabel || enumLabel('changeStatus', row.approveStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" :disabled="row.approveStatus === 'APPROVED'"
                     @click="approve(row)">批准</el-button>
          <el-button link type="danger" :disabled="row.approveStatus === 'REJECTED'"
                     @click="reject(row)">驳回</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <el-drawer v-model="show" title="变更详情" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
    <el-dialog v-model="createVisible" title="从合同发起变更" width="520px">
      <el-form :model="cf" label-width="120px">
        <el-form-item label="合同ID" required>
          <el-input v-model.number="cf.contractId" />
        </el-form-item>
        <el-form-item label="变更类型" required>
          <el-select v-model="cf.changeType" style="width:100%">
            <el-option label="调租" value="RENT_ADJUST" />
            <el-option label="续租" value="RENEW" />
            <el-option label="租期调整" value="PERIOD" />
            <el-option label="变更承租人" value="LESSEE" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="cf.changeType === 'RENT_ADJUST' || cf.changeType === 'RENEW'"
                      label="新月租金">
          <el-input v-model.number="cf.newMonthlyRent" />
        </el-form-item>
        <el-form-item v-if="cf.changeType === 'PERIOD' || cf.changeType === 'RENEW'"
                      label="新止租日">
          <el-date-picker v-model="cf.newLeaseEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="变更原因">
          <el-input v-model="cf.changeReason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="doCreateChange">创建</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'
import DetailView from '@/components/DetailView.vue'

const statuses = ['PENDING', 'APPROVED', 'REJECTED', 'CANCELLED']
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const show = ref(false)
const detail = ref(null)
const query = reactive({ pageNum: 1, pageSize: 20, changeStatus: '' })

async function load() {
  loading.value = true
  try {
    const d = await req.get('/contract-changes', {
      params: { ...query, status: query.changeStatus || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { query.pageNum = 1; load() }

async function approve(row) {
  await ElMessageBox.confirm(
    `确认批准变更「${row.changeNo}」？批准后会写回合同并即时生效。`, '批准确认',
    { type: 'warning' })
  await req.post(`/contract-changes/${row.id}/approve`)
  ElMessage.success('已批准'); load()
}

async function reject(row) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '驳回变更',
    { inputValue: '' })
  await req.post(`/contract-changes/${row.id}/reject`, { reason: value })
  ElMessage.success('已驳回'); load()
}

const query0 = JSON.parse(JSON.stringify(query))
function resetQuery() {
  Object.assign(query, query0)
  reload()
}

onMounted(load)
const createVisible = ref(false)
const cf = reactive({ contractId: null, changeType: 'RENT_ADJUST',
  newMonthlyRent: null, newLeaseEnd: '', changeReason: '' })

function openCreate() {
  Object.assign(cf, { contractId: null, changeType: 'RENT_ADJUST',
    newMonthlyRent: null, newLeaseEnd: '', changeReason: '' })
  createVisible.value = true
}

/** 从合同发起变更（统一走 /contracts/{id}/changes） */
async function doCreateChange() {
  if (!cf.contractId) { ElMessage.warning('请填写合同ID'); return }
  if (cf.changeType === 'RENT_ADJUST' && !cf.newMonthlyRent) {
    ElMessage.warning('调租请填写新租金'); return
  }
  await req.post(`/contracts/${cf.contractId}/changes`, {
    changeType: cf.changeType,
    changeReason: cf.changeReason,
    newMonthlyRent: cf.newMonthlyRent || null,
    newLeaseEnd: cf.newLeaseEnd || null
  })
  ElMessage.success('变更单已创建，待审批')
  createVisible.value = false
  load()
}
</script>
