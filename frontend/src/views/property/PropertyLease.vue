<template>
  <div class="lease-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyLease.noProject')" />
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">{{ t('propertyLease.title') }}</div>
        <div class="spacer" />
        <el-button type="primary" @click="openCreate">{{ t('propertyLease.create') }}</el-button>
      </div>
      <el-table :data="rows" border size="small" v-loading="loading">
        <el-table-column prop="contractNo" :label="t('propertyLease.contractNo')" width="190" />
        <el-table-column prop="assetType" :label="t('propertyLease.assetType')" width="120" />
        <el-table-column prop="assetName" :label="t('propertyLease.assetName')" min-width="170" />
        <el-table-column prop="lesseeName" :label="t('propertyLease.lessee')" width="130" />
        <el-table-column prop="rentAmount" :label="t('propertyLease.rent')" width="110" />
        <el-table-column prop="billingCycle" :label="t('propertyLease.cycle')" width="100" />
        <el-table-column prop="startDate" :label="t('propertyLease.start')" width="120" />
        <el-table-column prop="endDate" :label="t('propertyLease.end')" width="120" />
        <el-table-column prop="status" :label="t('propertyLease.status')" width="100" />
        <el-table-column :label="t('propertyLease.actions')" width="190">
          <template #default="{ row }">
            <el-button link type="primary" @click="openGenerate(row)">{{ t('propertyLease.generate') }}</el-button>
            <el-button link type="danger" @click="end(row)">{{ t('propertyLease.endAction') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="createVisible" :title="t('propertyLease.create')" width="520px">
      <el-form :model="form" label-width="100px">
        <el-form-item :label="t('propertyLease.assetType')">
          <el-select v-model="form.assetType" style="width:100%">
            <el-option label="SHOP" value="SHOP" />
            <el-option label="PUBLIC_HOUSE" value="PUBLIC_HOUSE" />
            <el-option label="PARKING" value="PARKING" />
            <el-option label="SITE" value="SITE" />
            <el-option label="AD_SPACE" value="AD_SPACE" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyLease.assetName')" required>
          <el-input v-model="form.assetName" />
        </el-form-item>
        <el-form-item :label="t('propertyLease.lessee')" required>
          <el-input v-model="form.lesseeName" />
        </el-form-item>
        <el-form-item :label="t('propertyLease.phone')">
          <el-input v-model="form.lesseePhone" />
        </el-form-item>
        <el-form-item :label="t('propertyLease.period')" required>
          <el-date-picker v-model="form.period" type="daterange" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('propertyLease.rent')" required>
          <el-input-number v-model="form.rentAmount" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item :label="t('propertyLease.cycle')">
          <el-select v-model="form.billingCycle" style="width:100%">
            <el-option label="MONTH" value="MONTH" />
            <el-option label="QUARTER" value="QUARTER" />
            <el-option label="HALF_YEAR" value="HALF_YEAR" />
            <el-option label="YEAR" value="YEAR" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('propertyLease.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ t('propertyLease.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="generateVisible" :title="t('propertyLease.generate')" width="440px">
      <el-form label-width="100px">
        <el-form-item :label="t('propertyLease.period')">
          <el-date-picker v-model="generatePeriod" type="daterange" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateVisible = false">{{ t('propertyLease.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="generate">{{ t('propertyLease.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { usePropertyStore } from '@/store/property'

const { t } = useI18n()
const store = usePropertyStore()
const projectId = computed(() => store.projectId)
const rows = ref([])
const loading = ref(false)
const saving = ref(false)
const createVisible = ref(false)
const generateVisible = ref(false)
const generatePeriod = ref([])
const generateId = ref(null)
const form = reactive({ assetType: 'SHOP', assetName: '', lesseeName: '', lesseePhone: '', period: [], rentAmount: 0, billingCycle: 'MONTH' })

onMounted(async () => { await store.loadProjects(); await load() })
watch(projectId, load)

async function load() {
  if (!projectId.value) return
  loading.value = true
  try { rows.value = await req.get('/property/leases', { params: { projectId: projectId.value } }) || [] }
  catch (e) { ElMessage.error(t('propertyLease.loadFailed')) } finally { loading.value = false }
}

function openCreate() {
  Object.assign(form, { assetType: 'SHOP', assetName: '', lesseeName: '', lesseePhone: '', period: [], rentAmount: 0, billingCycle: 'MONTH' })
  createVisible.value = true
}

async function save() {
  if (!form.assetName.trim() || !form.lesseeName.trim() || !form.rentAmount || form.period?.length !== 2) {
    ElMessage.warning(t('propertyLease.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/leases', {
      assetType: form.assetType, assetName: form.assetName, lesseeName: form.lesseeName,
      lesseePhone: form.lesseePhone, startDate: form.period[0], endDate: form.period[1],
      rentAmount: form.rentAmount, billingCycle: form.billingCycle
    }, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyLease.saved'))
    createVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyLease.failed'))
  } finally { saving.value = false }
}

function openGenerate(row) {
  generateId.value = row.id
  generatePeriod.value = []
  generateVisible.value = true
}

async function generate() {
  saving.value = true
  try {
    const body = generatePeriod.value?.length === 2
      ? { periodStart: generatePeriod.value[0], periodEnd: generatePeriod.value[1] } : {}
    const r = await req.post(`/property/leases/${generateId.value}/generate`, body, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyLease.generated', { amount: r.amount }))
    generateVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyLease.failed'))
  } finally { saving.value = false }
}

async function end(row) {
  await ElMessageBox.confirm(t('propertyLease.endConfirm'), t('propertyLease.endAction'), { type: 'warning' })
  try {
    await req.post(`/property/leases/${row.id}/end`, {}, { params: { projectId: projectId.value } })
    await load()
  } catch (e) { ElMessage.error(t('propertyLease.failed')) }
}
</script>

<style scoped>
.lease-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.spacer { flex: 1; }
</style>
