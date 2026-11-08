<template>
  <div class="parking-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyParking.noProject')" />

    <el-card shadow="never">
      <div class="toolbar">
        <div>
          <div class="title">{{ t('propertyParking.spaces') }}</div>
          <div class="sub">{{ t('propertyParking.spaceHint') }}</div>
        </div>
        <div class="spacer" />
        <el-button @click="rateVisible = true">{{ t('propertyParking.rates') }}</el-button>
        <el-button type="primary" @click="openSpace">{{ t('propertyParking.addSpace') }}</el-button>
      </div>

      <el-table :data="spaces" border size="small" v-loading="loading">
        <el-table-column prop="garageName" :label="t('propertyParking.garage')" width="130" />
        <el-table-column prop="spaceNo" :label="t('propertyParking.spaceNo')" width="130" />
        <el-table-column prop="spaceType" :label="t('propertyParking.spaceType')" width="120" />
        <el-table-column prop="area" :label="t('propertyParking.area')" width="90" />
        <el-table-column :label="t('propertyParking.plan')" min-width="200">
          <template #default="{ row }">
            <span v-if="row.planId">
              {{ row.billingCycle }} · {{ row.unitPrice }} {{ t('propertyParking.yuan') }}
              <span class="muted">{{ row.startDate }} ~ {{ row.endDate }}</span>
            </span>
            <span v-else class="muted">{{ t('propertyParking.noPlan') }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('propertyParking.bill')" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.billStatus" size="small"
                    :type="row.billStatus === 'PAID' ? 'success' : 'warning'">
              {{ row.billStatus }}
            </el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('propertyParking.actions')" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openPlan(row)">
              {{ row.planId ? t('propertyParking.renew') : t('propertyParking.planAction') }}
            </el-button>
            <el-button v-if="row.planId" link type="danger" @click="openTerminate(row)">
              {{ t('propertyParking.terminate') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="spaceVisible" :title="t('propertyParking.addSpace')" width="480px">
      <el-form :model="spaceForm" label-width="100px">
        <el-form-item :label="t('propertyParking.garage')">
          <el-input v-model="spaceForm.garageName" />
        </el-form-item>
        <el-form-item :label="t('propertyParking.spaceNo')" required>
          <el-input v-model="spaceForm.spaceNo" />
        </el-form-item>
        <el-form-item :label="t('propertyParking.spaceType')">
          <el-select v-model="spaceForm.spaceType" style="width:100%">
            <el-option label="STANDARD" value="STANDARD" />
            <el-option label="SUB" value="SUB" />
            <el-option label="EV" value="EV" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyParking.area')">
          <el-input-number v-model="spaceForm.area" :min="0" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="spaceVisible = false">{{ t('propertyParking.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveSpace">{{ t('propertyParking.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="planVisible" :title="t('propertyParking.planAction')" width="520px">
      <el-form :model="planForm" label-width="110px">
        <el-form-item :label="t('propertyParking.space')">
          <el-input :model-value="planForm.spaceNo" disabled />
        </el-form-item>
        <el-form-item :label="t('propertyParking.feeType')">
          <el-select v-model="planForm.feeType" style="width:100%">
            <el-option label="MANAGEMENT" value="MANAGEMENT" />
            <el-option label="RENT" value="RENT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyParking.cycle')">
          <el-select v-model="planForm.billingCycle" style="width:100%">
            <el-option label="MONTH" value="MONTH" />
            <el-option label="QUARTER" value="QUARTER" />
            <el-option label="HALF_YEAR" value="HALF_YEAR" />
            <el-option label="YEAR" value="YEAR" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyParking.startDate')">
          <el-date-picker v-model="planForm.startDate" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item :label="t('propertyParking.price')">
          <b>{{ planPrice || '-' }} {{ t('propertyParking.yuan') }}</b>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planVisible = false">{{ t('propertyParking.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="savePlan">{{ t('propertyParking.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="terminateVisible" :title="t('propertyParking.terminate')" width="460px">
      <el-alert type="warning" :closable="false" show-icon
                :title="t('propertyParking.terminateHint')" style="margin-bottom:12px" />
      <el-form label-width="110px">
        <el-form-item :label="t('propertyParking.terminateDate')">
          <el-date-picker v-model="terminateDate" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="terminateVisible = false">{{ t('propertyParking.cancel') }}</el-button>
        <el-button type="danger" :loading="saving" @click="terminate">{{ t('propertyParking.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="rateVisible" :title="t('propertyParking.rates')" width="720px">
      <el-table :data="rates" border size="small" max-height="260">
        <el-table-column prop="garageName" :label="t('propertyParking.garage')" width="120" />
        <el-table-column prop="spaceType" :label="t('propertyParking.spaceType')" width="100" />
        <el-table-column prop="feeType" :label="t('propertyParking.feeType')" width="120" />
        <el-table-column prop="billingCycle" :label="t('propertyParking.cycle')" width="100" />
        <el-table-column prop="price" :label="t('propertyParking.price')" width="100" />
        <el-table-column prop="effectiveFrom" :label="t('propertyParking.effectiveFrom')" width="120" />
      </el-table>
      <el-divider />
      <el-form :model="rateForm" inline label-width="80px">
        <el-form-item :label="t('propertyParking.cycle')">
          <el-select v-model="rateForm.billingCycle" style="width:110px">
            <el-option label="MONTH" value="MONTH" />
            <el-option label="YEAR" value="YEAR" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyParking.price')">
          <el-input-number v-model="rateForm.price" :min="0" :precision="2" style="width:130px" />
        </el-form-item>
        <el-button type="primary" :loading="saving" @click="saveRate">{{ t('propertyParking.saveRate') }}</el-button>
      </el-form>
      <template #footer>
        <el-button @click="rateVisible = false">{{ t('propertyParking.close') }}</el-button>
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
const spaces = ref([])
const rates = ref([])
const loading = ref(false)
const saving = ref(false)
const spaceVisible = ref(false)
const planVisible = ref(false)
const renewing = ref(false)
const terminateVisible = ref(false)
const rateVisible = ref(false)
const terminateDate = ref(new Date().toISOString().slice(0, 10))
const terminatePlanId = ref(null)
const spaceForm = reactive({ garageName: t('propertyParking.defaultGarage'), spaceNo: '', spaceType: 'STANDARD', area: 12 })
const planForm = reactive({ planId: null, spaceId: null, spaceNo: '', feeType: 'MANAGEMENT', billingCycle: 'YEAR', startDate: new Date().toISOString().slice(0, 10) })
const rateForm = reactive({ billingCycle: 'YEAR', price: 960 })

const planPrice = computed(() => {
  const r = rates.value.find((x) => x.feeType === planForm.feeType && x.billingCycle === planForm.billingCycle)
  return r ? r.price : ''
})

onMounted(async () => {
  await store.loadProjects()
  await loadAll()
})
watch(projectId, loadAll)

async function loadAll() {
  if (!projectId.value) return
  loading.value = true
  try {
    [spaces.value, rates.value] = await Promise.all([
      req.get('/property/parking/spaces', { params: { projectId: projectId.value } }),
      req.get('/property/parking/rates', { params: { projectId: projectId.value } })
    ])
  } catch (e) {
    ElMessage.error(t('propertyParking.loadFailed'))
  } finally { loading.value = false }
}

function openSpace() {
  Object.assign(spaceForm, { garageName: t('propertyParking.defaultGarage'), spaceNo: '', spaceType: 'STANDARD', area: 12 })
  spaceVisible.value = true
}

async function saveSpace() {
  if (!spaceForm.spaceNo.trim()) {
    ElMessage.warning(t('propertyParking.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/parking/spaces', spaceForm, { params: { projectId: projectId.value } })
    spaceVisible.value = false
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyParking.saveFailed'))
  } finally { saving.value = false }
}

function openPlan(row) {
  renewing.value = !!row.planId
  planForm.planId = row.planId || null
  planForm.spaceId = row.id
  planForm.spaceNo = row.spaceNo
  planForm.feeType = 'MANAGEMENT'
  planForm.billingCycle = row.billingCycle || 'YEAR'
  planForm.startDate = row.endDate ? addDay(row.endDate) : new Date().toISOString().slice(0, 10)
  planVisible.value = true
}

function addDay(date) {
  const d = new Date(date + 'T00:00:00')
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

async function savePlan() {
  saving.value = true
  try {
    const r = renewing.value
      ? await req.post(`/property/parking/plans/${planForm.planId}/renew`, {
        billingCycle: planForm.billingCycle, startDate: planForm.startDate
      })
      : await req.post('/property/parking/plans', {
        projectId: projectId.value, parkingSpaceId: planForm.spaceId,
        feeType: planForm.feeType, billingCycle: planForm.billingCycle, startDate: planForm.startDate
      })
    ElMessage.success(t('propertyParking.planDone', { amount: r.amount }))
    planVisible.value = false
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyParking.saveFailed'))
  } finally { saving.value = false }
}

function openTerminate(row) {
  terminatePlanId.value = row.planId
  terminateDate.value = new Date().toISOString().slice(0, 10)
  terminateVisible.value = true
}

async function terminate() {
  saving.value = true
  try {
    const r = await req.post(`/property/parking/plans/${terminatePlanId.value}/terminate`, {
      terminationDate: terminateDate.value
    })
    ElMessage.success(t('propertyParking.refundDone', { amount: r.refundAmount }))
    terminateVisible.value = false
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyParking.saveFailed'))
  } finally { saving.value = false }
}

async function saveRate() {
  saving.value = true
  try {
    await req.post('/property/parking/rates', {
      garageName: t('propertyParking.defaultGarage'), spaceType: 'STANDARD', feeType: 'MANAGEMENT',
      billingCycle: rateForm.billingCycle, price: rateForm.price,
      effectiveFrom: new Date().toISOString().slice(0, 10)
    }, { params: { projectId: projectId.value } })
    await loadAll()
    ElMessage.success(t('propertyParking.saved'))
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyParking.saveFailed'))
  } finally { saving.value = false }
}
</script>

<style scoped>
.parking-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.sub { font-size: 12px; color: #8492a6; margin-top: 3px; }
.spacer { flex: 1; }
.muted { color: #94a3b8; font-size: 12px; margin-left: 6px; }
</style>
