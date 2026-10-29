<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">监管报送</h3>
      <el-tag size="small" type="info">对接房管局/公安</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字/ID" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openCreate">发起报送</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="'报送任务按周期自动生成；失败可在任务详情重试'" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="taskNo" label="任务号" width="170" />
      <el-table-column prop="targetSystem" label="目标系统" width="150" />
      <el-table-column prop="reportType" label="类型" width="110">
        <template #default="{ row }">{{ row.reportTypeLabel || enumLabel('reportType', row.reportType) }}</template>
      </el-table-column>
      <el-table-column prop="taskStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.taskStatusLabel || enumLabel('taskStatus', row.taskStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" :width="ROWACTIONS ? 210 : 110" fixed="right">
        <template #default="{ row }">
          <el-button link type="warning" @click="retry(row)">补报</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <!-- 写操作表单（字段按后端 Cmd 定义配置） -->
    <el-dialog v-model="formVisible" :title="formTitle" width="560px">
      <el-form :model="model" label-width="120px">
        <el-form-item v-for="f in fields" :key="f.key" :label="f.label">
          <el-input v-if="f.type === 'text'" v-model="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'textarea'" type="textarea" :rows="3"
                    v-model="model[f.key]" :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'number'" v-model.number="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-date-picker v-else-if="f.type === 'date'" v-model="model[f.key]"
                          type="date" value-format="YYYY-MM-DD" style="width:100%" />
          <el-select v-else-if="f.type === 'select'" v-model="model[f.key]"
                     style="width:100%">
            <el-option v-for="o in f.options" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
          <el-switch v-else-if="f.type === 'bool'" v-model="model[f.key]" />
        </el-form-item>
      </el-form>
      <el-alert v-if="formNote" :closable="false" show-icon type="warning"
                :title="formNote" style="margin-top:8px" />
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { govApi } from '@/api/modules'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const detailVisible = ref(false)
const detail = ref(null)

const formVisible = ref(false)
const formTitle = ref('')
const formNote = ref('')
const fields = [
  { key: 'targetSystem', label: '目标系统', type: 'select', options: [{ value: 'PUBLIC_HOUSING', label: '公租房系统' }, { value: 'POLICE', label: '公安' }, { value: 'HOUSING', label: '住建' }, { value: 'REAL_ESTATE', label: '不动产' }] },
  { key: 'reportType', label: '报送类型', type: 'select', options: [{ value: 'HOUSE', label: '房源' }, { value: 'TENANT', label: '租户' }, { value: 'CONTRACT', label: '合同' }] },
  { key: 'dateFrom', label: '数据范围起', type: 'date' },
  { key: 'dateTo', label: '数据范围止', type: 'date' }
]
const model = reactive({})

// 必填字段（取自后端 Cmd 的 @NotNull）
const REQUIRED = ['targetSystem', 'reportType']
let submitFn = null


async function load() {
  loading.value = true
  try {
    const data = await govApi.tasks({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

function reload() { pageNum.value = 1; load() }
function openDetail(row) { detail.value = row; detailVisible.value = true }

function openForm(title, fieldDefs, fn, preset = {}, note = '') {
  formTitle.value = title
  formNote.value = note
  Object.keys(model).forEach((k) => delete model[k])
  fieldDefs.forEach((f) => { model[f.key] = preset[f.key] ?? f.default ?? '' })
  submitFn = fn
  formVisible.value = true
}

/** 必填校验（字段级，依赖后端 Cmd 的 @NotNull 语义）。 */
function validateForm() {
  const missing = fields.filter((f) => REQUIRED.includes(f.key)
    && (model[f.key] === '' || model[f.key] === null || model[f.key] === undefined))
  if (missing.length) {
    ElMessage.warning('请填写：' + missing.map((f) => f.label).join('、'))
    return false
  }
  // 数字类基本合法性
  for (const f of fields) {
    if (f.type === 'number' && model[f.key] !== '' && model[f.key] !== null
        && Number.isNaN(Number(model[f.key]))) {
      ElMessage.warning(f.label + '必须是数字')
      return false
    }
  }
  return true
}

async function submit() {
  if (!validateForm()) return
  saving.value = true
  try {
    await submitFn({ ...model })
    ElMessage.success('操作成功')
    formVisible.value = false
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

function openCreate() {
  openForm('发起监管报送', fields, (m) => govApi.submit(m),
    { targetSystem: 'PUBLIC_HOUSING', reportType: 'HOUSE' },
    '未配置适配器时任务会失败并提示，不会阻断业务')
}
async function retry(row) {
  const n = await govApi.retry(row.id)
  ElMessage.success(`补报完成：成功 ${n} 条`)
  load()
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
