<template>
  <div>
    <div class="navbar">{{ t('h5.billsTitle') }}</div>
    <div class="card">
      <div class="row"><b>{{ t('h5.billsTotal') }}</b><div class="spacer" />
        <span class="amount" style="font-size:18px">¥ {{ totalUnpaid }}</span></div>
    </div>

    <div v-for="b in rows" :key="b.id" class="card">
      <div class="row">
        <b>{{ t('h5.billPeriod', { period: b.billPeriod }) }}</b>
        <div class="spacer" />
        <el-tag size="small" :type="b.billStatus === 'PAID' ? 'success'
          : (b.overdueNow ? 'danger' : 'warning')">
          {{ b.billStatusLabel || b.billStatus }}
        </el-tag>
      </div>
      <div class="row" style="margin-top:8px">
        <span class="muted">{{ b.billNo }}</span>
        <div class="spacer" />
        <span class="amount" :class="{ ok: b.billStatus === 'PAID' }">
          ¥ {{ b.payableAmount }}
        </span>
      </div>
      <div class="muted" style="margin-top:6px">
        {{ t('h5.billLine', { amount: b.billAmount, paid: b.paidAmount, due: b.dueDate }) }}
        <span v-if="b.overdueDays > 0" style="color:#f53f3f"> {{ t('h5.overdue', { n: b.overdueDays }) }}</span>
      </div>
    </div>

    <div v-if="!rows.length" class="empty">{{ t('h5.noBills') }}</div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import { ref, computed, onMounted } from 'vue'
import { financeApi } from '@/api/modules'

const rows = ref([])
const personId = localStorage.getItem('bp_person_id') || ''

const totalUnpaid = computed(() => rows.value
  .filter((b) => ['UNPAID', 'PARTIAL', 'OVERDUE'].includes(b.billStatus))
  .reduce((s, b) => s + Number(b.payableAmount || 0), 0).toFixed(2))

onMounted(async () => {
  const data = await financeApi.bills({
    pageNum: 1, pageSize: 50, personId: personId || undefined
  })
  rows.value = data.rows || []
})
</script>
