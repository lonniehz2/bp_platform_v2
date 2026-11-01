<template>
  <div>
    <div class="navbar">{{ t('h5.appsTitle') }}</div>

    <el-steps v-if="current" :active="stepOf(current)" simple style="margin:12px">
      <el-step :title="t('h5.stepSubmit')" />
      <el-step :title="t('h5.stepAccept')" />
      <el-step :title="t('h5.stepReview')" />
      <el-step :title="t('h5.stepResult')" />
    </el-steps>

    <div v-for="a in rows" :key="a.id" class="card">
      <div class="row">
        <b>{{ a.applicationNo }}</b>
        <div class="spacer" />
        <el-tag size="small" :type="tagOf(a.applicationStatus)">
          {{ a.applicationStatusLabel || a.applicationStatus }}
        </el-tag>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ t('h5.familyIncome', { type: a.securityType, size: a.familySize, income: a.incomePerCapita }) }}
      </div>
      <div class="muted" style="margin-top:4px">{{ t('h5.currentNode', { node: a.currentNode || '-' }) }}</div>
      <div v-if="a.rejectReason" style="margin-top:6px;color:#f53f3f;font-size:12px">
        {{ t('h5.rejectReason', { reason: a.rejectReason }) }}
      </div>
      <div v-if="a.supplementDemand" style="margin-top:6px;color:#ff7d00;font-size:12px">
        {{ t('h5.supplement', { demand: a.supplementDemand }) }}
      </div>
      <div class="muted" style="margin-top:6px">{{ t('h5.applyTime', { time: a.applyTime }) }}</div>
    </div>

    <div v-if="!rows.length" class="empty">{{ t('h5.noApps') }}</div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import { ref, computed, onMounted } from 'vue'
import { applicationApi } from '@/api/modules'

const rows = ref([])
const personId = localStorage.getItem('bp_person_id') || ''
const current = computed(() => rows.value[0])

function stepOf(a) {
  const s = a.applicationStatus
  if (['APPROVED', 'REJECTED'].includes(s)) return 4
  if (['REVIEWING', 'SUPPLEMENT'].includes(s)) return 3
  if (s === 'ACCEPTED') return 2
  return 1
}
function tagOf(s) {
  return ({ APPROVED: 'success', REJECTED: 'danger',
    SUPPLEMENT: 'warning' })[s] || 'info'
}

onMounted(async () => {
  const data = await applicationApi.page({
    pageNum: 1, pageSize: 20, personId: personId || undefined
  })
  rows.value = data.rows || []
})
</script>
