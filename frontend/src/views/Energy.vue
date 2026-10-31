<template>
  <div class="page-card">
    <div class="toolbar">
      <h2 style="margin:0">能耗分摊</h2>
      <span class="muted">房间表 → 人·天分摊；空床默认运营方承担；总表只做分析</span>
    </div>

    <el-tabs v-model="tab">
      <el-tab-pane label="月度分摊" name="alloc">
        <div class="toolbar">
          <el-input v-model="period" placeholder="2026-10" style="width:120px" />
          <el-select v-model="pointId" placeholder="表计" clearable style="width:220px">
            <el-option v-for="p in points" :key="p.id"
                       :label="(p.meterName || p.id) + '｜' + p.meterScope" :value="p.id" />
          </el-select>
          <el-button type="primary" :loading="loading" @click="preview">试算</el-button>
          <el-button type="success" :disabled="!previewData" @click="confirm">确认分摊并出账</el-button>
        </div>
        <el-alert v-if="previewData" type="info" :closable="false" show-icon
                  :title="`整表用量 ${previewData.totalUsage}，整表费用 ${previewData.totalAmount}，运营方承担 ${previewData.operatorBearAmount}`" />
        <el-table v-if="previewData" :data="previewData.shares" border size="small" style="margin-top:10px">
          <el-table-column prop="contractNo" label="合同" width="180" />
          <el-table-column prop="lesseeName" label="承租人" width="120" />
          <el-table-column prop="occupyDays" label="占用天数" width="100" />
          <el-table-column prop="personDays" label="人·天" width="100" />
          <el-table-column prop="shareRatio" label="比例" width="100" />
          <el-table-column prop="shareAmount" label="分摊金额" width="120" />
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="能耗分析" name="analysis">
        <div class="toolbar">
          <el-input v-model="period" placeholder="2026-10" style="width:120px" />
          <el-select v-model="analysisItem" placeholder="收费项目" clearable style="width:200px">
            <el-option v-for="f in feeItems" :key="f.id" :label="f.itemName" :value="String(f.id)" />
          </el-select>
          <el-button type="primary" @click="loadAnalysis">查询</el-button>
        </div>
        <el-descriptions v-if="stat" :column="3" border size="small">
          <el-descriptions-item label="总表用量">{{ stat.totalUsage }}</el-descriptions-item>
          <el-descriptions-item label="分表合计">{{ stat.submeterUsage }}</el-descriptions-item>
          <el-descriptions-item label="差异量">{{ stat.diffUsage }}</el-descriptions-item>
          <el-descriptions-item label="差异率">{{ (Number(stat.diffRate) * 100).toFixed(2) }}%</el-descriptions-item>
          <el-descriptions-item label="告警级别">
            <el-tag :type="stat.alertLevel === 'ALARM' ? 'danger'
              : (stat.alertLevel === 'WARN' ? 'warning' : 'success')">
              {{ stat.alertLevel }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-tab-pane>

      <el-tab-pane label="表计" name="points">
        <div class="toolbar">
          <el-button type="primary" @click="openPoint">新增表计</el-button>
        </div>
        <el-table :data="points" border size="small">
          <el-table-column prop="meterName" label="名称" width="160" />
          <el-table-column prop="spaceId" label="空间 ID" width="180" />
          <el-table-column prop="feeItemId" label="收费项目" width="180" />
          <el-table-column prop="meterScope" label="范围" width="100" />
          <el-table-column prop="allocationBasis" label="分摊基数" width="120" />
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRead(row)">人工抄表</el-button>
              <el-button link @click="readNow(row)">即时抄表</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="策略" name="policy">
        <el-form :model="policy" label-width="120px" style="max-width:520px">
          <el-form-item label="空床承担">
            <el-radio-group v-model="policy.vacancyBearer">
              <el-radio label="OPERATOR">运营方</el-radio>
              <el-radio label="OCCUPANTS">在住租户</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="警告阈值">
            <el-input v-model.number="policy.warnRate" />
          </el-form-item>
          <el-form-item label="告警阈值">
            <el-input v-model.number="policy.alarmRate" />
          </el-form-item>
          <el-button type="primary" @click="savePolicy">保存策略</el-button>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="pointVisible" title="新增表计" width="480px">
      <el-form :model="pf" label-width="100px">
        <el-form-item label="空间 ID" required><el-input v-model="pf.spaceId" /></el-form-item>
        <el-form-item label="收费项目" required>
          <el-select v-model="pf.feeItemId" filterable style="width:100%">
            <el-option v-for="f in feeItems" :key="f.id" :label="f.itemName" :value="String(f.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="床位容量">
          <el-input v-model.number="pf.bedCapacity" placeholder="房间床位数" />
        </el-form-item>
        <el-form-item label="名称"><el-input v-model="pf.meterName" /></el-form-item>
        <el-form-item label="范围">
          <el-select v-model="pf.meterScope" style="width:100%">
            <el-option label="房间表" value="ROOM" />
            <el-option label="楼栋总表" value="BUILDING" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pointVisible = false">取消</el-button>
        <el-button type="primary" @click="savePoint">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="readVisible" title="人工抄表" width="420px">
      <el-form label-width="90px">
        <el-form-item label="读数"><el-input v-model.number="rf.reading" /></el-form-item>
        <el-form-item label="抄表时间">
          <el-date-picker v-model="rf.readTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="rf.remark" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="readVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRead">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const tab = ref('alloc')
const period = ref(new Date().toISOString().slice(0, 7))
const points = ref([])
const pointId = ref('')
const previewData = ref(null)
const stat = ref(null)
const analysisItem = ref('')
const loading = ref(false)
const feeItems = ref([])
const pointVisible = ref(false)
const readVisible = ref(false)
const currentPoint = ref(null)
const policy = reactive({ vacancyBearer: 'OPERATOR', warnRate: 0.05, alarmRate: 0.1 })
const pf = reactive({ spaceId: '', feeItemId: '', bedCapacity: null, meterName: '', meterScope: 'ROOM' })
const rf = reactive({ reading: null, readTime: '', remark: '' })

async function loadPoints() {
  points.value = (await req.get('/fin/meter-points')) || []
}
async function loadFees() {
  const d = await req.get('/fin/fee-items', { params: { pageNum: 1, pageSize: 100 } })
  feeItems.value = (d && d.rows) || []
}
async function preview() {
  if (!period.value) return ElMessage.warning('请输入期间')
  loading.value = true
  try {
    previewData.value = await req.post('/fin/utility-allocations/preview', {
      period: period.value, meterPointId: pointId.value || undefined
    })
  } finally { loading.value = false }
}
async function confirm() {
  await ElMessageBox.confirm('确认后生成各合同账单，是否继续？', '确认分摊', { type: 'warning' })
  const r = await req.post('/fin/utility-allocations/confirm', {
    period: period.value, meterPointId: pointId.value || undefined
  })
  previewData.value = r
  ElMessage.success('已生成分摊账单')
}
async function loadAnalysis() {
  stat.value = await req.get('/fin/energy-analysis/monthly', { params: { period: period.value, feeItemId: analysisItem.value || undefined } })
}
function openPoint() {
  Object.assign(pf, { spaceId: '', feeItemId: '', bedCapacity: null, meterName: '', meterScope: 'ROOM' })
  pointVisible.value = true
}
async function savePoint() {
  await req.post('/fin/meter-points', { ...pf })
  pointVisible.value = false
  loadPoints()
}
function openRead(row) {
  currentPoint.value = row
  Object.assign(rf, { reading: null, readTime: '', remark: '' })
  readVisible.value = true
}
async function saveRead() {
  await req.post(`/fin/meter-points/${currentPoint.value.id}/readings`, { ...rf })
  readVisible.value = false
  ElMessage.success('已保存读数')
}
async function readNow(row) {
  try {
    await req.post(`/fin/meter-points/${row.id}/read-now`)
    ElMessage.success('设备抄表成功')
  } catch (e) {
    ElMessage.warning('设备抄表不可用，请使用人工抄表')
  }
}
async function loadPolicy() {
  const p = await req.get('/fin/energy-policy').catch(() => null)
  if (p) Object.assign(policy, p)
}
async function savePolicy() {
  await req.put('/fin/energy-policy', { ...policy })
  ElMessage.success('策略已保存')
}
onMounted(async () => {
  await Promise.all([loadPoints(), loadFees(), loadPolicy()])
})
</script>
