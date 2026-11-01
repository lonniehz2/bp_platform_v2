<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('visit.title') }}</h3>
      <el-tag size="small" type="info"></el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" :placeholder="t('visit.keyword')" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">{{ t('visit.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('visit.reset') }}</el-button>
      <el-button type="success" @click="openCreate">{{ t('visit.register') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="t('miscPage.visitsTip')" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('misc.emptyDefault')">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="visitNo" :label="t('visit.no')" width="170" />
      <el-table-column prop="visitUserName" :label="t('visit.visitor')" width="120">
            <template #default="{ row }">{{ row.visitUserName || row.visitUserId || t('common.unassigned') }}</template>
          </el-table-column>
      <el-table-column prop="personIdName" :label="t('visit.person')" width="120">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="visitStatus" :label="t('visit.status')" width="110">
        <template #default="{ row }">{{ row.visitStatusLabel || enumLabel('visitStatus', row.visitStatus) }}</template>
      </el-table-column>
      <el-table-column :label="t('visit.actions')" width="210" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="report(row)">{{ t('visit.report') }}</el-button>
          <el-button link type="warning" @click="toWorkOrder(row)">{{ t('visit.toWorkOrder') }}</el-button>
          <el-button link @click="openDetail(row)">{{ t('visit.detail') }}</el-button>
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
        <el-button @click="formVisible = false">{{ t('visit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="submit">{{ t('visit.submit') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" :title="t('visit.drawer')" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { visitApi } from '@/api/modules'
import req from '@/api/request'

const { t } = useI18n()
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
  { key: 'visitType', label: t('visit.visitType'), type: 'text' },
  { key: 'orgId', label: t('visit.orgId'), type: 'number' },
  { key: 'houseId', label: t('visit.houseId'), type: 'number' }
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
    ElMessage.success(t('visit.success'))
    formVisible.value = false
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

function openCreate() {
  openForm(t('visit.register'), fields, (m) => visitApi.create(m))
}
async function report(row) {
  const defs = [
    { key: 'visitStatus', label: t('visit.visitStatus'), type: 'select', default: 'DONE',
      options: [{ label: t('visit.done'), value: 'DONE' }, { label: t('visit.refused'), value: 'REFUSED' },
        { label: t('visit.absent'), value: 'ABSENT' }, { label: t('visit.cancelled'), value: 'CANCELLED' }] },
    { key: 'actualDate', label: t('visit.actualDate'), type: 'date' },
    { key: 'isOccupied', label: t('visit.isOccupied'), type: 'select', default: 1,
      options: [{ label: t('visit.home'), value: 1 }, { label: t('visit.notHome'), value: 0 }] },
    { key: 'actualResidents', label: t('visit.actualResidents'), type: 'number' },
    { key: 'matchResult', label: t('visit.matchResult'), type: 'select', default: 'MATCH',
      options: [{ label: t('visit.match'), value: 'MATCH' }, { label: t('visit.mismatch'), value: 'MISMATCH' },
        { label: t('visit.unknown'), value: 'UNKNOWN' }] },
    { key: 'findings', label: t('visit.findings'), type: 'textarea',
      ph: t('visit.findingsHint') },
    { key: 'nextAction', label: t('visit.nextAction'), type: 'textarea', ph: t('visit.nextHint') }
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
