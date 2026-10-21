<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">轮候管理</h3>
      <el-tag size="small" type="info">总分 = 优先附加分 + 轮候天数 × 0.1</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:150px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openEnqueue">入队登记</el-button>
      <el-button @click="recalc">重算总分</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="摇号按总分降序、入队时间升序取前 N 名；优先附加分用于优抚对象加分"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="personId" label="人员" width="200">
        <template #default="{ row }">{{ row.personName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="priorityScore" label="优先分" width="100" />
      <el-table-column prop="waitDays" label="轮候天数" width="110" />
      <el-table-column prop="totalScore" label="总分" width="100">
        <template #default="{ row }">
          <strong>{{ row.totalScore }}</strong>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag size="small" :type="row.queueStatus === 'WAITING' ? 'success'
            : (row.queueStatus === 'EXITED' ? 'info' : 'warning')">
            {{ row.queueStatusLabel || enumLabel('queueStatus', row.queueStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="enterTime" label="入队时间" width="170" />
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="{ row }">
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <el-dialog v-model="enqueueVisible" title="轮候入队" width="560px">
      <el-form :model="ef" label-width="130px">
        <el-form-item label="人员ID" required>
          <el-input v-model="ef.personId" /></el-form-item>
        <el-form-item label="申请单ID">
          <el-input v-model="ef.applicationId"
                    placeholder="已通过的申请单，可为空" /></el-form-item>
        <el-form-item label="组织ID" required>
          <el-input v-model="ef.orgId" /></el-form-item>
        <el-form-item label="保障类型" required>
          <el-select v-model="ef.securityType" style="width:100%">
            <el-option label="公租房" value="PUBLIC" />
            <el-option label="保租房" value="AFFORDABLE" />
            <el-option label="人才房" value="TALENT" />
            <el-option label="廉租房" value="LOW_RENT" />
          </el-select></el-form-item>
        <el-form-item label="优先附加分">
          <el-input-number v-model="ef.priorityScore" :min="0" :precision="1"
                           style="width:100%" />
        </el-form-item>
        <el-form-item label="优先原因">
          <el-input v-model="ef.priorityReason"
                    placeholder="如 退役军人 / 残疾人 / 计生特殊家庭" /></el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="入队后系统按「优先分 + 轮候天数×0.1」计算总分，摇号时实时排序" />
      <template #footer>
        <el-button @click="enqueueVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doEnqueue">确认入队</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="轮候详情" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'
import DetailView from '@/components/DetailView.vue'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const enqueueVisible = ref(false)
const query = reactive({ pageNum: 1, pageSize: 20 })
const ef = reactive({ personId: null, applicationId: null, orgId: null,
  securityType: 'PUBLIC', priorityScore: 0, priorityReason: '' })

async function load() {
  loading.value = true
  try {
    const d = await req.get('/allocation/waiting', {
      params: { ...query, keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { query.pageNum = 1; load() }

function openEnqueue() { enqueueVisible.value = true }

async function doEnqueue() {
  if (!ef.personId || !ef.orgId) {
    ElMessage.warning('人员与组织为必填'); return
  }
  saving.value = true
  try {
    await req.post('/allocation/waiting', { ...ef })
    ElMessage.success('已入队')
    enqueueVisible.value = false; reload()
  } finally { saving.value = false }
}

async function recalc() {
  const r = await req.post('/allocation/waiting/recalc', null,
    { params: { orgId: ef.orgId || undefined } })
  ElMessage.success('重算完成：更新 ' + (r?.count ?? r ?? '全部') + ' 条')
  load()
}

function resetQuery() {
  keyword.value = ''
  reload()
}

onMounted(load)
</script>
