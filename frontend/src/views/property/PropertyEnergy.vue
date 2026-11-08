<template>
  <div class="energy-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyEnergy.noProject')" />
    <el-card shadow="never">
      <div class="toolbar">
        <div>
          <div class="title">{{ t('propertyEnergy.title') }}</div>
          <div class="sub">{{ t('propertyEnergy.hint') }}</div>
        </div>
        <div class="spacer" />
        <el-date-picker v-model="period" type="month" value-format="YYYY-MM"
                        :clearable="false" @change="load" />
        <el-button type="primary" @click="openAllocate">{{ t('propertyEnergy.allocate') }}</el-button>
      </div>
      <el-table :data="rows" border size="small" v-loading="loading">
        <el-table-column prop="houseName" :label="t('propertyEnergy.house')" min-width="180" />
        <el-table-column prop="area" :label="t('propertyEnergy.area')" width="110" />
        <el-table-column prop="totalAmount" :label="t('propertyEnergy.total')" width="120" />
        <el-table-column prop="amount" :label="t('propertyEnergy.amount')" width="120" />
        <el-table-column prop="period" :label="t('propertyEnergy.period')" width="100" />
        <el-table-column prop="billId" :label="t('propertyEnergy.bill')" min-width="170" />
      </el-table>
    </el-card>

    <el-dialog v-model="visible" :title="t('propertyEnergy.allocate')" width="480px">
      <el-form :model="form" label-width="100px">
        <el-form-item :label="t('propertyEnergy.period')" required>
          <el-date-picker v-model="form.period" type="month" value-format="YYYY-MM" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('propertyEnergy.total')" required>
          <el-input-number v-model="form.totalAmount" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item :label="t('propertyEnergy.feeItem')">
          <el-select v-model="form.feeItemId" style="width:100%">
            <el-option v-for="f in feeItems" :key="f.id" :label="f.feeItemName" :value="f.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">{{ t('propertyEnergy.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="allocate">{{ t('propertyEnergy.confirm') }}</el-button>
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
const period = ref(new Date().toISOString().slice(0, 7))
const rows = ref([])
const feeItems = ref([])
const loading = ref(false)
const saving = ref(false)
const visible = ref(false)
const form = reactive({ period: period.value, totalAmount: 0, feeItemId: null })

onMounted(async () => {
  await store.loadProjects()
  await loadFeeItems()
  await load()
})
watch(projectId, async () => { await loadFeeItems(); await load() })

async function loadFeeItems() {
  if (!projectId.value) return
  try {
    const list = await req.get('/property/fee-items', { params: { projectId: projectId.value } }) || []
    feeItems.value = list
    const energy = list.find((f) => f.feeItemCode === 'ENERGY_SHARED')
    if (energy && !form.feeItemId) form.feeItemId = energy.id
  } catch (e) { feeItems.value = [] }
}

async function load() {
  if (!projectId.value) return
  loading.value = true
  try {
    rows.value = await req.get('/property/energy/allocations', {
      params: { projectId: projectId.value, period: period.value }
    }) || []
  } catch (e) { ElMessage.error(t('propertyEnergy.loadFailed')) } finally { loading.value = false }
}

function openAllocate() {
  Object.assign(form, { period: period.value, totalAmount: 0, feeItemId: feeItems.value.find((f) => f.feeItemCode === 'ENERGY_SHARED')?.id || feeItems.value[0]?.id || null })
  visible.value = true
}

async function allocate() {
  if (!form.totalAmount || !form.feeItemId) {
    ElMessage.warning(t('propertyEnergy.required'))
    return
  }
  saving.value = true
  try {
    const r = await req.post('/property/energy/allocations', form, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyEnergy.done', { created: r.created, skipped: r.skipped }))
    visible.value = false
    period.value = form.period
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyEnergy.failed'))
  } finally { saving.value = false }
}
</script>

<style scoped>
.energy-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.sub { font-size: 12px; color: #8492a6; margin-top: 3px; }
.spacer { flex: 1; }
</style>
