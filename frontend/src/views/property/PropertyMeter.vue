<template>
  <div class="meter-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyMeter.noProject')" />
    <el-card shadow="never">
      <div class="toolbar">
        <div>
          <div class="title">{{ t('propertyMeter.title') }}</div>
          <div class="sub">{{ t('propertyMeter.hint') }}</div>
        </div>
        <div class="spacer" />
        <el-button @click="loadAll">{{ t('propertyMeter.refresh') }}</el-button>
        <el-button type="primary" @click="openMeter">{{ t('propertyMeter.addMeter') }}</el-button>
        <el-button type="success" @click="openReading">{{ t('propertyMeter.addReading') }}</el-button>
      </div>
      <el-table :data="meters" border size="small" v-loading="loading">
        <el-table-column prop="meterNo" :label="t('propertyMeter.meterNo')" width="150" />
        <el-table-column prop="meterType" :label="t('propertyMeter.meterType')" width="110" />
        <el-table-column prop="houseName" :label="t('propertyMeter.house')" min-width="170" />
        <el-table-column prop="lastReading" :label="t('propertyMeter.lastReading')" width="120" />
        <el-table-column prop="unitPrice" :label="t('propertyMeter.unitPrice')" width="110" />
        <el-table-column prop="multiplier" :label="t('propertyMeter.multiplier')" width="100" />
        <el-table-column prop="status" :label="t('propertyMeter.status')" width="100" />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>{{ t('propertyMeter.readings') }}</template>
      <el-table :data="readings" border size="small">
        <el-table-column prop="meterNo" :label="t('propertyMeter.meterNo')" width="140" />
        <el-table-column prop="period" :label="t('propertyMeter.period')" width="100" />
        <el-table-column prop="prevReading" :label="t('propertyMeter.prev')" width="100" />
        <el-table-column prop="currentReading" :label="t('propertyMeter.current')" width="100" />
        <el-table-column prop="usageAmount" :label="t('propertyMeter.usage')" width="100" />
        <el-table-column prop="amount" :label="t('propertyMeter.amount')" width="110" />
        <el-table-column prop="billId" :label="t('propertyMeter.bill')" min-width="170" />
      </el-table>
    </el-card>

    <el-dialog v-model="meterVisible" :title="t('propertyMeter.addMeter')" width="500px">
      <el-form :model="meterForm" label-width="100px">
        <el-form-item :label="t('propertyMeter.house')" required>
          <el-select v-model="meterForm.houseId" filterable style="width:100%">
            <el-option v-for="u in units" :key="u.id" :label="u.houseName" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyMeter.meterType')">
          <el-select v-model="meterForm.meterType" style="width:100%">
            <el-option label="WATER" value="WATER" />
            <el-option label="ELECTRICITY" value="ELECTRICITY" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyMeter.meterNo')" required>
          <el-input v-model="meterForm.meterNo" />
        </el-form-item>
        <el-form-item :label="t('propertyMeter.unitPrice')">
          <el-input-number v-model="meterForm.unitPrice" :min="0" :precision="4" />
        </el-form-item>
        <el-form-item :label="t('propertyMeter.initial')">
          <el-input-number v-model="meterForm.initialReading" :min="0" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="meterVisible = false">{{ t('propertyMeter.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveMeter">{{ t('propertyMeter.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="readingVisible" :title="t('propertyMeter.addReading')" width="500px">
      <el-form :model="readingForm" label-width="100px">
        <el-form-item :label="t('propertyMeter.meterNo')" required>
          <el-select v-model="readingForm.meterId" filterable style="width:100%">
            <el-option v-for="m in meters" :key="m.id" :label="m.meterNo + ' · ' + m.houseName" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyMeter.period')" required>
          <el-date-picker v-model="readingForm.period" type="month" value-format="YYYY-MM" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('propertyMeter.current')" required>
          <el-input-number v-model="readingForm.currentReading" :min="0" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="readingVisible = false">{{ t('propertyMeter.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveReading">{{ t('propertyMeter.save') }}</el-button>
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
const meters = ref([])
const units = ref([])
const readings = ref([])
const loading = ref(false)
const saving = ref(false)
const meterVisible = ref(false)
const readingVisible = ref(false)
const meterForm = reactive({ houseId: null, meterType: 'WATER', meterNo: '', unitPrice: 3.5, initialReading: 0 })
const readingForm = reactive({ meterId: null, period: new Date().toISOString().slice(0, 7), currentReading: 0 })

onMounted(async () => {
  await store.loadProjects()
  await loadAll()
})
watch(projectId, loadAll)

async function loadAll() {
  if (!projectId.value) return
  loading.value = true
  try {
    const [m, u] = await Promise.all([
      req.get('/property/meters', { params: { projectId: projectId.value } }),
      req.get('/property/units', { params: { projectId: projectId.value } })
    ])
    meters.value = m || []
    units.value = u || []
    readings.value = await req.get('/property/meters/readings', { params: { projectId: projectId.value } }) || []
  } catch (e) { ElMessage.error(t('propertyMeter.loadFailed')) } finally { loading.value = false }
}

function openMeter() {
  Object.assign(meterForm, { houseId: null, meterType: 'WATER', meterNo: '', unitPrice: 3.5, initialReading: 0 })
  meterVisible.value = true
}

async function saveMeter() {
  if (!meterForm.houseId || !meterForm.meterNo.trim()) {
    ElMessage.warning(t('propertyMeter.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/meters', meterForm, { params: { projectId: projectId.value } })
    meterVisible.value = false
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyMeter.saveFailed'))
  } finally { saving.value = false }
}

function openReading() {
  Object.assign(readingForm, { meterId: meters.value[0]?.id || null, period: new Date().toISOString().slice(0, 7), currentReading: 0 })
  readingVisible.value = true
}

async function saveReading() {
  if (!readingForm.meterId || !readingForm.currentReading) {
    ElMessage.warning(t('propertyMeter.required'))
    return
  }
  saving.value = true
  try {
    const r = await req.post('/property/meters/readings', readingForm, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyMeter.readingDone', { amount: r.amount }))
    readingVisible.value = false
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyMeter.saveFailed'))
  } finally { saving.value = false }
}
</script>

<style scoped>
.meter-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.sub { font-size: 12px; color: #8492a6; margin-top: 3px; }
.spacer { flex: 1; }
</style>
