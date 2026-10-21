# -*- coding: utf-8 -*-
"""补全三个页面：合同变更审批 / 轮候入队 / 用户与权限（完整 CRUD）"""
import io
import os

V = r'D:\Work\业务平台开发\frontend\src\views'

# ==================== ① 合同变更（审批/驳回）====================
CHANGES = '''<template>
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
          <el-tag size="small" :type="row.changeStatus === 'APPROVED' ? 'success'
            : (row.changeStatus === 'REJECTED' ? 'danger' : 'warning')">
            {{ row.changeStatusLabel || enumLabel('changeStatus', row.changeStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" :disabled="row.changeStatus === 'APPROVED'"
                     @click="approve(row)">批准</el-button>
          <el-button link type="danger" :disabled="row.changeStatus === 'REJECTED'"
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
      params: { ...query, changeStatus: query.changeStatus || undefined }
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

onMounted(load)
</script>
'''
io.open(os.path.join(V, 'ContractChanges.vue'), 'w', encoding='utf-8').write(CHANGES)
print('  ✓ ContractChanges.vue：加批准/驳回')

# ==================== ② 轮候（入队/重算）====================
WAITLIST = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">轮候管理</h3>
      <el-tag size="small" type="info">总分 = 优先附加分 + 轮候天数 × 0.1</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:150px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
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
          <el-input v-model.number="ef.personId" /></el-form-item>
        <el-form-item label="申请单ID">
          <el-input v-model.number="ef.applicationId"
                    placeholder="已通过的申请单，可为空" /></el-form-item>
        <el-form-item label="组织ID" required>
          <el-input v-model.number="ef.orgId" /></el-form-item>
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

onMounted(load)
</script>
'''
io.open(os.path.join(V, 'Waitlist.vue'), 'w', encoding='utf-8').write(WAITLIST)
print('  ✓ Waitlist.vue：加入队/重算')
