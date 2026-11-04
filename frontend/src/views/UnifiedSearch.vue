<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('search.title') }}</h3>
      <el-tag size="small" type="info">{{ t('search.subtitle') }}</el-tag>
    </div>

    <el-form :model="form" label-width="100px" style="margin-top:12px">
      <el-row :gutter="12">
        <el-col :span="8">
          <el-form-item :label="t('search.idCard')">
            <div style="display:flex;gap:6px;width:100%">
              <el-input v-model="form.idCard" clearable :placeholder="t('search.idCardHint')"
                        @keyup.enter="doSearch" />
              <el-button @click="readIdCard">{{ t('search.readCard') }}</el-button>
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item :label="t('search.personName')">
            <el-input v-model="form.personName" clearable @keyup.enter="doSearch" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item :label="t('search.keyword')">
            <el-input v-model="form.keyword" clearable :placeholder="t('search.keywordHint')"
                      @keyup.enter="doSearch" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item :label="t('search.community')">
            <el-select v-model="form.orgId" clearable style="width:100%" @change="onOrgChange">
              <el-option v-for="c in communities" :key="c.id" :label="c.name" :value="String(c.id)" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item :label="t('search.building')">
            <el-select v-model="form.buildingId" clearable style="width:100%">
              <el-option v-for="b in buildings" :key="b.id" :label="b.name" :value="String(b.id)" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item :label="t('search.houseCode')">
            <el-input v-model="form.houseCode" clearable @keyup.enter="doSearch" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item :label="t('search.houseStatus')">
            <el-select v-model="form.houseStatus" clearable style="width:100%">
              <el-option v-for="s in statuses" :key="s" :label="enumLabel('houseStatus', s)" :value="s" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <div class="toolbar">
        <el-button type="primary" :loading="loading" @click="doSearch">{{ t('search.search') }}</el-button>
        <el-button @click="reset">{{ t('search.reset') }}</el-button>
        <span v-if="searched" class="muted">{{ t('search.total', { n: result.total || 0 }) }}</span>
      </div>
    </el-form>

    <el-tabs v-if="searched" v-model="tab" style="margin-top:8px">
      <el-tab-pane :label="t('search.persons', { n: result.persons?.length || 0 })" name="persons">
        <el-table :data="result.persons || []" border size="small" :empty-text="t('search.empty')">
          <el-table-column prop="personName" :label="t('search.personName')" width="140" />
          <el-table-column prop="phone" :label="t('search.phone')" width="140" />
          <el-table-column prop="idCardMask" :label="t('search.idCard')" min-width="180" />
          <el-table-column prop="personStatus" :label="t('search.status')" width="110" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane :label="t('search.contracts', { n: result.contracts?.length || 0 })" name="contracts">
        <el-table :data="result.contracts || []" border size="small" :empty-text="t('search.empty')">
          <el-table-column prop="contractNo" :label="t('search.contractNo')" width="190" />
          <el-table-column prop="lesseeName" :label="t('search.lessee')" width="130" />
          <el-table-column prop="contractStatus" :label="t('search.status')" width="110" />
          <el-table-column prop="leaseStart" :label="t('search.leaseStart')" width="120" />
          <el-table-column prop="leaseEnd" :label="t('search.leaseEnd')" width="120" />
          <el-table-column prop="monthlyRent" :label="t('search.monthlyRent')" width="110" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane :label="t('search.houses', { n: result.houses?.length || 0 })" name="houses">
        <el-table :data="result.houses || []" border size="small" :empty-text="t('search.empty')">
          <el-table-column prop="houseCode" :label="t('search.houseCode')" width="150" />
          <el-table-column prop="houseName" :label="t('search.houseName')" min-width="140" />
          <el-table-column prop="houseStatus" :label="t('search.houseStatus')" width="110">
            <template #default="{ row }">{{ enumLabel('houseStatus', row.houseStatus) }}</template>
          </el-table-column>
          <el-table-column prop="personName" :label="t('search.lessee')" width="130" />
          <el-table-column prop="area" :label="t('search.area')" width="90" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane :label="t('search.bills', { n: result.bills?.length || 0 })" name="bills">
        <el-table :data="result.bills || []" border size="small" :empty-text="t('search.empty')">
          <el-table-column prop="billNo" :label="t('search.billNo')" width="200" />
          <el-table-column prop="billPeriod" :label="t('search.billPeriod')" width="100" />
          <el-table-column prop="billAmount" :label="t('search.billAmount')" width="120" />
          <el-table-column prop="payableAmount" :label="t('search.payable')" width="120" />
          <el-table-column prop="billStatus" :label="t('search.status')" width="110" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const { t } = useI18n()
const loading = ref(false)
const searched = ref(false)
const tab = ref('persons')
const communities = ref([])
const buildings = ref([])
const result = ref({})
const statuses = ['PENDING_ALLOC', 'LOCKED', 'ALLOCATED', 'OCCUPIED', 'VACANT', 'MAINTENANCE', 'DISABLED']

const form = reactive({
  keyword: '', idCard: '', personName: '', orgId: '', buildingId: '',
  houseCode: '', houseStatus: ''
})

async function loadOptions() {
  try {
    const d = await req.get('/screen/overview')
    communities.value = d.communities || []
    buildings.value = d.buildings || []
  } catch (e) { /* keep manual input */ }
}

function onOrgChange() {
  form.buildingId = ''
}

/** ID card reader hook: call the hardware SDK here when available. */
async function readIdCard() {
  const reader = window.__ID_CARD_READER__ || window.idCardReader
  if (reader && typeof reader.read === 'function') {
    try {
      const v = await reader.read()
      form.idCard = typeof v === 'string' ? v : (v?.idCard || '')
      if (form.idCard) doSearch()
    } catch (e) {
      ElMessage.error(t('search.readerError'))
    }
    return
  }
  ElMessage.info(t('search.readerMissing'))
}

async function doSearch() {
  loading.value = true
  try {
    result.value = await req.get('/search/unified', {
      params: {
        keyword: form.keyword || undefined,
        idCard: form.idCard || undefined,
        personName: form.personName || undefined,
        orgId: form.orgId || undefined,
        buildingId: form.buildingId || undefined,
        houseCode: form.houseCode || undefined,
        houseStatus: form.houseStatus || undefined
      }
    })
    searched.value = true
  } finally { loading.value = false }
}

function reset() {
  Object.assign(form, { keyword: '', idCard: '', personName: '', orgId: '', buildingId: '', houseCode: '', houseStatus: '' })
  result.value = {}
  searched.value = false
}

onMounted(loadOptions)
</script>
