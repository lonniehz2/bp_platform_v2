<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">资金流水</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:170px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>

    </div>
    <el-alert v-if="'核销/退款/补贴都会自动记账，形成完整资金流水'" type="info" :closable="false" show-icon :title="'核销/退款/补贴都会自动记账，形成完整资金流水'"
              style="margin-bottom:12px" />
    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="flowNo" label="流水号" width="170" />
      <el-table-column prop="bizType" label="业务类型" width="130">
        <template #default="{ row }">{{ row.bizTypeLabel || enumLabel('bizType', row.bizType) }}</template>
      </el-table-column>
      <el-table-column prop="flowType" label="收支" width="100">
        <template #default="{ row }">{{ row.flowTypeLabel || enumLabel('flowType', row.flowType) }}</template>
      </el-table-column>
      <el-table-column prop="amount" label="金额" width="110" />
      <el-table-column prop="flowTime" label="时间" width="170" />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />
    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, onMounted } from 'vue'
import { financeApi } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)


async function load() {
  loading.value = true
  try {
    const data = await financeApi.cashflow({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }
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
