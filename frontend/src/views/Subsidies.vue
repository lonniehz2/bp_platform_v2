<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">补贴管理</h3>
      <el-tag size="small" type="info">4 种方式 · 月度封顶 · 抵扣租金</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="batchVisible = true">批量发放</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="补贴：FIXED 定额 / BY_AREA 按面积 / BY_PERSON 按人 / RATIO 按租金比例；封顶与抵扣规则由标准配置"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="recordNo" label="补贴单号" width="170" />
      <el-table-column prop="personId" label="人员" width="110">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="subsidyMode" label="方式" width="110">
        <template #default="{ row }">{{ row.subsidyModeLabel || enumLabel('subsidyMode', row.subsidyMode) }}</template>
      </el-table-column>
      <el-table-column prop="subsidyPeriod" label="周期" width="100" />
      <el-table-column prop="subsidyAmount" label="金额" width="100" />
      <el-table-column prop="recordStatus" label="状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.recordStatus === 'PAID' ? 'success'
            : (row.recordStatus === 'FAILED' ? 'danger' : 'warning')">
            {{ row.recordStatusLabel || enumLabel('recordStatus', row.recordStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" :disabled="row.recordStatus !== 'PENDING'"
                     @click="confirm(row)">确认发放</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="batchVisible" title="批量发放补贴" width="480px">
      <el-form :model="bf" label-width="110px">
        <el-form-item label="补贴周期">
          <el-input v-model="bf.subsidyPeriod" placeholder="2026-10" /></el-form-item>
        <el-form-item label="组织ID"><el-input v-model="bf.orgId" /></el-form-item>
        <el-form-item label="发放方式">
          <el-select v-model="bf.payMode" style="width:100%">
            <el-option label="银行代发" value="BANK" />
            <el-option label="抵扣租金" value="OFFSET" />
          </el-select></el-form-item>
        <el-form-item label="试算（不落库）">
          <el-switch v-model="bf.dryRun" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doBatch">确认发放</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { subsidyApi } from '@/api/modules'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const batchVisible = ref(false)
const bf = reactive({ subsidyPeriod: '', orgId: 1, payMode: 'BANK', dryRun: false })

async function load() {
  loading.value = true
  try {
    const d = await subsidyApi.records({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doBatch() {
  if (!bf.subsidyPeriod) { ElMessage.warning('请填写补贴周期'); return }
  saving.value = true
  try {
    const r = await subsidyApi.batchGrant({ ...bf })
    ElMessage.success('发放完成：' + (r?.count ?? r ?? '已执行'))
    batchVisible.value = false; load()
  } finally { saving.value = false }
}

async function confirm(row) {
  await subsidyApi.confirm(row.id)
  ElMessage.success('已确认发放'); load()
}

function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}

onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
