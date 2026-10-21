# -*- coding: utf-8 -*-
"""P0 收尾：公示（含发布/结束）、配租（摇号/放弃/签约）、年审、补贴、催缴"""
import io
import os

V = r'D:\Work\业务平台开发\frontend\src\views'

# ==================== 公示 ====================
PUB = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">公示管理</h3>
      <div class="spacer" />
      <el-button @click="check">配租公示完成校验</el-button>
      <el-button type="success" @click="visible = true">发布公示</el-button>
    </div>
    <el-alert type="warning" :closable="false" show-icon
              title="配租公示必须 ≥7 自然日且已结束，才能办理签约（签约时后端硬校验）"
              style="margin-bottom:12px" />
    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="publicityNo" label="公示号" width="170" />
      <el-table-column prop="publicityType" label="类型" width="120" />
      <el-table-column prop="title" label="标题" min-width="180" />
      <el-table-column prop="startDate" label="开始" width="110" />
      <el-table-column prop="endDate" label="结束" width="110" />
      <el-table-column prop="publicityStatus" label="状态" width="110" />
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="publish(row)">发布</el-button>
          <el-button link type="warning" @click="close(row)">结束公示</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="q.pageSize" :current-page="q.pageNum"
                   @current-change="(p) => { q.pageNum = p; load() }" />

    <el-dialog v-model="visible" title="发布公示" width="520px">
      <el-form :model="f" label-width="110px">
        <el-form-item label="公示类型">
          <el-select v-model="f.publicityType" style="width:100%">
            <el-option label="配租公示" value="ALLOCATION" />
            <el-option label="资格公示" value="QUALIFY" />
            <el-option label="退出公示" value="EXIT" />
          </el-select></el-form-item>
        <el-form-item label="组织ID"><el-input v-model.number="f.orgId" /></el-form-item>
        <el-form-item label="标题"><el-input v-model="f.title" /></el-form-item>
        <el-form-item label="开始日">
          <el-date-picker v-model="f.startDate" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="结束日">
          <el-date-picker v-model="f.endDate" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { publicityApi } from '@/api/modules'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const q = reactive({ pageNum: 1, pageSize: 20 })
const visible = ref(false)
const f = reactive({ publicityType: 'ALLOCATION', orgId: 1, title: '',
  startDate: '', endDate: '' })

async function load() {
  loading.value = true
  try {
    const d = await publicityApi.page({ ...q })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}

async function save() {
  if (!f.startDate || !f.endDate) { ElMessage.warning('请填写公示起止日'); return }
  saving.value = true
  try {
    await publicityApi.create({ ...f })
    ElMessage.success('公示已创建')
    visible.value = false; load()
  } finally { saving.value = false }
}

async function publish(row) {
  await publicityApi.publish(row.id)
  ElMessage.success('已发布'); load()
}

async function close(row) {
  const { value } = await ElMessageBox.prompt('结束公示备注（可空）', '结束公示',
    { inputValue: '' })
  await publicityApi.close(row.id, value)
  ElMessage.success('公示已结束，可以签约'); load()
}

async function check() {
  const r = await publicityApi.allocationCheck(1)
  ElMessageBox.alert(String(r), '配租公示完成校验')
}

onMounted(load)
</script>
'''

# ==================== 配租（摇号/放弃/签约） ====================
ALLOC = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">配租与摇号</h3>
        <div class="spacer" />
        <el-input v-model="seed" placeholder="摇号种子（可复现）" style="width:190px" />
        <el-button type="success" @click="lotteryVisible = true">执行摇号</el-button>
        <el-button @click="release">释放超时锁定</el-button>
      </div>
      <el-table :data="batches" v-loading="loading" border size="small">
        <el-table-column prop="id" label="批次ID" width="150" />
        <el-table-column prop="batchNo" label="批次号" width="160" />
        <el-table-column prop="batchName" label="名称" min-width="160" />
        <el-table-column prop="batchStatus" label="状态" width="110" />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewResults(row)">摇号结果</el-button>
            <el-button link @click="setStatus(row)">改状态</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">配租单</h4>
      <el-table :data="allocations" border size="small">
        <el-table-column prop="allocationNo" label="配租单号" width="170" />
        <el-table-column prop="personId" label="人员" width="110" />
        <el-table-column prop="houseId" label="房源" width="110" />
        <el-table-column prop="allocationStatusLabel" label="状态" width="110" />
        <el-table-column prop="lockRemainHours" label="锁定剩余(h)" width="110" />
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="sign(row)">签约</el-button>
            <el-button link type="danger" @click="giveUp(row)">放弃</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 摇号 LotteryRunCmd -->
    <el-dialog v-model="lotteryVisible" title="执行摇号" width="460px">
      <el-form :model="l" label-width="110px">
        <el-form-item label="批次ID"><el-input v-model.number="l.batchId" /></el-form-item>
        <el-form-item label="随机种子"><el-input v-model="l.seed"
          placeholder="留空则服务端生成并落库" /></el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="中签数 = 房源数；之后 3 名递补；同种子可完全复现（可公证复核）" />
      <template #footer>
        <el-button @click="lotteryVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doLottery">开始摇号</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resultVisible" title="摇号结果" width="680px">
      <el-table :data="results" border size="small">
        <el-table-column prop="queueId" label="轮候ID" width="150" />
        <el-table-column prop="personId" label="人员" width="120" />
        <el-table-column prop="totalScore" label="总分" width="100" />
        <el-table-column prop="rankNo" label="名次" width="90" />
        <el-table-column prop="resultType" label="结果" width="110" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { allocationApi } from '@/api/modules'

const loading = ref(false)
const saving = ref(false)
const batches = ref([])
const allocations = ref([])
const results = ref([])
const seed = ref('20261020')
const lotteryVisible = ref(false)
const resultVisible = ref(false)
const l = reactive({ batchId: null, seed: '20261020' })

async function load() {
  loading.value = true
  try {
    const b = await allocationApi.batches({ pageNum: 1, pageSize: 50 })
    batches.value = b.rows || []
    const a = await allocationApi.allocations({ pageNum: 1, pageSize: 50 })
    allocations.value = a.rows || []
  } finally { loading.value = false }
}

async function doLottery() {
  if (!l.batchId) { ElMessage.warning('请填写批次ID'); return }
  saving.value = true
  try {
    const r = await allocationApi.lottery(l.batchId, l.seed || seed.value)
    ElMessage.success('摇号完成：' + (r?.winCount ?? r?.length ?? '已执行'))
    lotteryVisible.value = false; load()
  } finally { saving.value = false }
}

async function viewResults(row) {
  results.value = await allocationApi.results(row.id)
  resultVisible.value = true
}

async function setStatus(row) {
  const { value } = await ElMessageBox.prompt('输入新状态（如 PUBLISHED/CLOSED）',
    '变更批次状态', { inputValue: row.batchStatus })
  await allocationApi.setBatchStatus(row.id, value)
  ElMessage.success('已更新'); load()
}

async function sign(row) {
  await ElMessageBox.confirm(
    '签约会校验配租公示是否已完成（≥7 天且已结束），确认继续？', '签约确认',
    { type: 'warning' })
  await allocationApi.sign(row.id, {})
  ElMessage.success('签约成功'); load()
}

async function giveUp(row) {
  const { value } = await ElMessageBox.prompt('请输入放弃原因', '放弃配租')
  await allocationApi.giveUp(row.id, value)
  ElMessage.success('已放弃，房源释放'); load()
}

async function release() {
  const r = await allocationApi.releaseExpired()
  ElMessage.success('已释放超时锁定：' + (r?.count ?? '已执行')); load()
}

onMounted(load)
</script>
'''

io.open(os.path.join(V, 'Publicities.vue'), 'w', encoding='utf-8').write(PUB)
io.open(os.path.join(V, 'Allocations.vue'), 'w', encoding='utf-8').write(ALLOC)
print('  ✓ Publicities.vue（发布/结束/校验）+ Allocations.vue（摇号/状态/签约/放弃/释放）')
