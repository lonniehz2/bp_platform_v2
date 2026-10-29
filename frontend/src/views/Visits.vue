<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">入户走访</h3>
      <el-tag size="small" type="info"></el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字/ID" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openCreate">走访登记</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="'用于定期入户核查房屋使用情况：是否居住、实际人数、是否转租/空置/违规使用'" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small" empty-text="暂无数据，可调整筛选条件或点击右上角新建">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="visitNo" label="来访号" width="170" />
      <el-table-column prop="visitUserName" label="走访人" width="120">
            <template #default="{ row }">{{ row.visitUserName || row.visitUserId || '未指派' }}</template>
          </el-table-column>
      <el-table-column prop="personIdName" label="被访人" width="120">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="visitStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.visitStatusLabel || enumLabel('visitStatus', row.visitStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="210" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="report(row)">登记报告</el-button>
          <el-button link type="warning" @click="toWorkOrder(row)">转工单</el-button>
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
import { visitApi } from '@/api/modules'
import req from '@/api/request'

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
  { key: 'visitType', label: '来访类型', type: 'text' },
  { key: 'orgId', label: '组织ID', type: 'number' },
  { key: 'houseId', label: '房源ID', type: 'number' }
]
const model = reactive({})

// 必填字段（取自后端 Cmd 的 @NotNull）
const REQUIRED = ['visitType']
let submitFn = null


async function load() {
  loading.value = true
  try {
    const data = await visitApi.page({
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
  openForm('走访登记', fields, (m) => visitApi.create(m))
}
async function report(row) {
  const defs = [
    { key: 'visitStatus', label: '走访状态', type: 'select', default: 'DONE',
      options: [{ label: '完成', value: 'DONE' }, { label: '拒访', value: 'REFUSED' },
        { label: '不在家', value: 'ABSENT' }, { label: '取消', value: 'CANCELLED' }] },
    { key: 'actualDate', label: '实际日期', type: 'date' },
    { key: 'isOccupied', label: '是否在家', type: 'select', default: 1,
      options: [{ label: '在家', value: 1 }, { label: '不在', value: 0 }] },
    { key: 'actualResidents', label: '实际居住人数', type: 'number' },
    { key: 'matchResult', label: '人房匹配', type: 'select', default: 'MATCH',
      options: [{ label: '匹配', value: 'MATCH' }, { label: '不匹配', value: 'MISMATCH' },
        { label: '未知', value: 'UNKNOWN' }] },
    { key: 'findings', label: '发现问题', type: 'textarea',
      ph: '如：转租、空置、违规使用，无则留空' },
    { key: 'nextAction', label: '后续动作', type: 'textarea', ph: '如：转工单整改' }
  ]
  openForm('登记走访报告 · ' + (row.houseName || row.houseId), defs,
    (m) => visitApi.report(row.id, m),
    { actualDate: new Date().toISOString().slice(0, 10) })
}

function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}

onMounted(load)
/** 走访发现问题 → 转工单处理（如违规使用整改、维修） */
async function toWorkOrder(row) {
  await ElMessageBox.confirm('确认把该走访转为工单？', '转工单', { type: 'warning' })
  await req.post(`/visits/${row.id}/to-workorder`,
    { operatorId: 1, operatorName: '管理员' })
  ElMessage.success('已转工单')
  load()
}
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
