<template>
  <div class="profit-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyProfit.noProject')" />
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">{{ t('propertyProfit.title') }}</div>
        <el-date-picker v-model="month" type="month" value-format="YYYY-MM"
                        :clearable="false" @change="load" />
        <div class="spacer" />
        <el-button type="primary" @click="openExpense">{{ t('propertyProfit.addExpense') }}</el-button>
      </div>
      <div class="kpis">
        <div class="kpi"><div class="label">{{ t('propertyProfit.income') }}</div><div class="value">{{ overview.income || 0 }}</div></div>
        <div class="kpi"><div class="label">{{ t('propertyProfit.receivable') }}</div><div class="value">{{ overview.receivable || 0 }}</div></div>
        <div class="kpi"><div class="label">{{ t('propertyProfit.expense') }}</div><div class="value">{{ overview.expense || 0 }}</div></div>
        <div class="kpi"><div class="label">{{ t('propertyProfit.profit') }}</div><div class="value">{{ overview.profit || 0 }}</div></div>
        <div class="kpi"><div class="label">{{ t('propertyProfit.collectionRate') }}</div><div class="value">{{ overview.collectionRate || 0 }}%</div></div>
      </div>
    </el-card>

    <el-row :gutter="12">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>{{ t('propertyProfit.incomeBreakdown') }}</template>
          <el-table :data="overview.incomeRows || []" border size="small">
            <el-table-column prop="incomeCategory" :label="t('propertyProfit.category')" />
            <el-table-column prop="amount" :label="t('propertyProfit.amount')" width="140" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>{{ t('propertyProfit.expenseBreakdown') }}</template>
          <el-table :data="overview.expenseRows || []" border size="small">
            <el-table-column prop="categoryName" :label="t('propertyProfit.category')" />
            <el-table-column prop="amount" :label="t('propertyProfit.amount')" width="140" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>{{ t('propertyProfit.expenses') }}</template>
      <el-table :data="expenses" border size="small">
        <el-table-column prop="expenseMonth" :label="t('propertyProfit.month')" width="120" />
        <el-table-column prop="categoryName" :label="t('propertyProfit.category')" width="160" />
        <el-table-column prop="supplier" :label="t('propertyProfit.supplier')" min-width="160" />
        <el-table-column prop="amount" :label="t('propertyProfit.amount')" width="120" />
        <el-table-column prop="remark" :label="t('propertyProfit.remark')" />
      </el-table>
    </el-card>

    <el-dialog v-model="visible" :title="t('propertyProfit.addExpense')" width="520px">
      <el-form :model="form" label-width="110px">
        <el-form-item :label="t('propertyProfit.month')">
          <el-date-picker v-model="form.expenseMonth" type="month" value-format="YYYY-MM" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('propertyProfit.category')" required>
          <el-select v-model="form.categoryCode" style="width:100%">
            <el-option v-for="c in categoryOptions" :key="c.categoryCode" :label="c.categoryName" :value="c.categoryCode" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyProfit.amount')" required>
          <el-input-number v-model="form.amount" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item :label="t('propertyProfit.supplier')">
          <el-input v-model="form.supplier" />
        </el-form-item>
        <el-form-item :label="t('propertyProfit.remark')">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">{{ t('propertyProfit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveExpense">{{ t('propertyProfit.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { usePropertyStore } from '@/store/property'

const { t } = useI18n()
const store = usePropertyStore()
const projectId = computed(() => store.projectId)
const month = ref(new Date().toISOString().slice(0, 7))
const overview = ref({})
const expenses = ref([])
const categories = ref([])
const visible = ref(false)
const saving = ref(false)
const form = reactive({ expenseMonth: month.value, categoryCode: '', amount: 0, supplier: '', remark: '' })

const categoryOptions = computed(() => categories.value.filter((c) => c.categoryLevel === 2))

onMounted(async () => {
  await store.loadProjects()
  await load()
})
watch(projectId, load)

async function load() {
  if (!projectId.value) return
  try {
    const [o, e, c] = await Promise.all([
      req.get('/property/reports/overview', { params: { projectId: projectId.value, month: month.value } }),
      req.get('/property/expenses', { params: { projectId: projectId.value, month: month.value } }),
      req.get('/property/expense-categories')
    ])
    overview.value = o || {}
    expenses.value = e || []
    categories.value = c || []
  } catch (err) {
    ElMessage.error(t('propertyProfit.loadFailed'))
  }
}

function openExpense() {
  Object.assign(form, { expenseMonth: month.value, categoryCode: '', amount: 0, supplier: '', remark: '' })
  visible.value = true
}

async function saveExpense() {
  if (!form.categoryCode || !form.amount) {
    ElMessage.warning(t('propertyProfit.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/expenses', form, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyProfit.saved'))
    visible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyProfit.saveFailed'))
  } finally { saving.value = false }
}
</script>

<style scoped>
.profit-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.spacer { flex: 1; }
.kpis { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.kpi { background: #f5f8ff; border-radius: 6px; padding: 10px 12px; }
.kpi .label { font-size: 12px; color: #64748b; }
.kpi .value { font-size: 22px; font-weight: 600; margin-top: 4px; color: #1f2d3d; }
</style>
