<template>
  <div class="invoice-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyInvoice.noProject')" />
    <el-card shadow="never">
      <div class="toolbar">
        <div class="title">{{ t('propertyInvoice.title') }}</div>
        <div class="spacer" />
        <el-button type="primary" @click="openRequest">{{ t('propertyInvoice.request') }}</el-button>
      </div>
      <el-table :data="rows" border size="small" v-loading="loading">
        <el-table-column prop="receiptNo" :label="t('propertyInvoice.receiptNo')" width="190" />
        <el-table-column prop="invoiceTitle" :label="t('propertyInvoice.invoiceTitle')" min-width="180" />
        <el-table-column prop="taxNo" :label="t('propertyInvoice.taxNo')" width="180" />
        <el-table-column prop="amount" :label="t('propertyInvoice.amount')" width="110" />
        <el-table-column prop="invoiceStatus" :label="t('propertyInvoice.status')" width="110" />
        <el-table-column prop="invoiceNo" :label="t('propertyInvoice.invoiceNo')" width="190" />
        <el-table-column :label="t('propertyInvoice.actions')" width="100">
          <template #default="{ row }">
            <el-button v-if="row.invoiceStatus === 'PENDING'" link type="primary" @click="issue(row)">
              {{ t('propertyInvoice.issue') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="visible" :title="t('propertyInvoice.request')" width="500px">
      <el-form :model="form" label-width="110px">
        <el-form-item :label="t('propertyInvoice.receipt')" required>
          <el-select v-model="form.receiptId" style="width:100%">
            <el-option v-for="r in receipts" :key="r.id" :label="r.receiptNo + ' · ' + r.amount" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyInvoice.invoiceTitle')" required>
          <el-input v-model="form.invoiceTitle" />
        </el-form-item>
        <el-form-item :label="t('propertyInvoice.taxNo')">
          <el-input v-model="form.taxNo" />
        </el-form-item>
        <el-form-item :label="t('propertyInvoice.email')">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">{{ t('propertyInvoice.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ t('propertyInvoice.save') }}</el-button>
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
const rows = ref([])
const receipts = ref([])
const loading = ref(false)
const saving = ref(false)
const visible = ref(false)
const form = reactive({ receiptId: null, invoiceTitle: '', taxNo: '', email: '' })

onMounted(async () => { await store.loadProjects(); await load() })
watch(projectId, load)

async function load() {
  if (!projectId.value) return
  loading.value = true
  try {
    const [i, r] = await Promise.all([
      req.get('/property/invoices', { params: { projectId: projectId.value } }),
      req.get('/property/receipts', { params: { projectId: projectId.value } })
    ])
    rows.value = i || []
    receipts.value = r || []
  } catch (e) { ElMessage.error(t('propertyInvoice.loadFailed')) } finally { loading.value = false }
}

function openRequest() {
  Object.assign(form, { receiptId: receipts.value[0]?.id || null, invoiceTitle: '', taxNo: '', email: '' })
  visible.value = true
}

async function save() {
  if (!form.receiptId || !form.invoiceTitle.trim()) {
    ElMessage.warning(t('propertyInvoice.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/invoices', form, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyInvoice.saved'))
    visible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyInvoice.saveFailed'))
  } finally { saving.value = false }
}

async function issue(row) {
  try {
    const r = await req.post(`/property/invoices/${row.id}/issue`)
    ElMessage.success(t('propertyInvoice.issued', { no: r.invoiceNo }))
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyInvoice.issueFailed'))
  }
}
</script>

<style scoped>
.invoice-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.spacer { flex: 1; }
</style>
