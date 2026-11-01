<template>
  <div>
    <div class="hero">
      <div class="title">{{ greeting }}，{{ auth.displayName }}</div>
      <div class="sub">{{ bound ? t('h5.homeBound', { id: personId }) : t('h5.homeUnbound') }}</div>
    </div>

    <div class="card">
      <div class="grid4">
        <div class="item" @click="$router.push('/h5/bills')">
          <div class="icon"><el-icon><Money /></el-icon></div>
          <div class="label">{{ t('h5.myBills') }}</div>
        </div>
        <div class="item" @click="$router.push('/h5/applications')">
          <div class="icon"><el-icon><Document /></el-icon></div>
          <div class="label">{{ t('h5.applications') }}</div>
        </div>
        <div class="item" @click="$router.push('/h5/access')">
          <div class="icon"><el-icon><Position /></el-icon></div>
          <div class="label">{{ t('h5.access') }}</div>
        </div>
        <div class="item" @click="$router.push('/h5/repairs')">
          <div class="icon"><el-icon><Tools /></el-icon></div>
          <div class="label">{{ t('h5.repairs') }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="row">
        <b>{{ t('h5.unpaidTotal') }}</b>
        <div class="spacer" />
        <span v-if="loading" class="muted">{{ t('h5.loading') }}</span>
      </div>
      <div class="amount" style="margin-top:8px">¥ {{ totalUnpaid }}</div>
      <div class="muted">{{ t('h5.unpaidCount', { n: unpaidCount }) }}</div>
    </div>

    <div class="card">
      <div class="row"><b>{{ t('h5.myContract') }}</b><div class="spacer" />
        <span class="muted">{{ contract ? contract.contractStatusLabel : t('h5.none') }}</span>
      </div>
      <div v-if="contract" style="margin-top:10px">
        <div>{{ contract.houseAddress }}</div>
        <div class="muted" style="margin-top:4px">
          {{ contract.contractNo }} · {{ contract.leaseStart }} ~ {{ contract.leaseEnd }}
        </div>
        <div class="muted" style="margin-top:4px">
          {{ t('h5.monthlyRent', { amount: contract.monthlyRent }) }}
          <span v-if="Number(contract.daysToExpire) <= 30" style="color:#ff7d00">
            {{ t('h5.daysToExpire', { n: contract.daysToExpire }) }}
          </span>
        </div>
      </div>
      <div v-else class="empty">{{ t('h5.noActiveContract') }}</div>
    </div>

    <div class="card">
      <div class="row"><b>{{ t('h5.myTodos') }}</b><div class="spacer" />
        <span class="muted">{{ t('h5.todoCount', { n: todos.length }) }}</span></div>
      <div v-for="t in todos.slice(0, 3)" :key="t.id" class="list-item">
        <div>{{ t.title }}</div>
        <div class="muted">{{ t.content }}</div>
      </div>
      <div v-if="!todos.length" class="empty">{{ t('h5.noTodos') }}</div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { financeApi, contractApi, msgApi } from '@/api/modules'

const auth = useAuthStore()
const loading = ref(false)
const bills = ref([])
const contract = ref(null)
const todos = ref([])

const personId = computed(() => localStorage.getItem('bp_person_id') || '')
const bound = computed(() => !!personId.value)
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 11 ? '早上好' : h < 14 ? '中午好' : h < 18 ? '下午好' : '晚上好'
})
const unpaid = computed(() => bills.value.filter(
  (b) => ['UNPAID', 'PARTIAL', 'OVERDUE'].includes(b.billStatus)))
const unpaidCount = computed(() => unpaid.value.length)
const totalUnpaid = computed(() =>
  unpaid.value.reduce((s, b) => s + Number(b.payableAmount || 0), 0).toFixed(2))

async function load() {
  loading.value = true
  try {
    const pid = personId.value
    const b = await financeApi.bills({ pageNum: 1, pageSize: 50, personId: pid || undefined })
    bills.value = b.rows || []
    const c = await contractApi.page({ pageNum: 1, pageSize: 10 })
    contract.value = (c.rows || [])[0] || null
    if (auth.user?.userId) {
      const t = await msgApi.todos({ pageNum: 1, pageSize: 10, userId: auth.user.userId })
      todos.value = t.rows || []
    }
  } catch (e) { /* 已提示 */ } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
