<template>
  <div class="property-dashboard">
    <el-alert type="info" :closable="false" show-icon :title="t('property.phaseBanner')" />
    <div class="cards">
      <div v-for="c in cards" :key="c.title" class="card" @click="open(c)">
        <div class="card-title">{{ c.title }}</div>
        <div class="card-desc">{{ c.desc }}</div>
        <div class="card-link">{{ c.link }}</div>
      </div>
    </div>
    <el-card shadow="never" class="note">
      <template #header>{{ t('property.firstPhase') }}</template>
      <ul>
        <li>{{ t('property.scopeProject') }}</li>
        <li>{{ t('property.scopeCategory') }}</li>
        <li>{{ t('property.scopeNext') }}</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t } = useI18n()

const cards = [
  { title: t('property.incomeCategory'), desc: t('property.incomeCategoryDesc'), link: t('property.open'), path: '/property/categories?tab=income' },
  { title: t('property.expenseCategory'), desc: t('property.expenseCategoryDesc'), link: t('property.open'), path: '/property/categories?tab=expense' }
]

function open(c) {
  router.push(c.path)
}
</script>

<style scoped>
.property-dashboard { display: flex; flex-direction: column; gap: 14px; }
.cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.card { background: #fff; border: 1px solid #e6edf7; border-radius: 8px; padding: 18px; cursor: pointer; transition: .2s; }
.card:hover { border-color: #7db3ff; box-shadow: 0 6px 20px rgba(47,124,246,.12); }
.card-title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.card-desc { font-size: 13px; color: #64748b; margin-top: 8px; line-height: 1.6; }
.card-link { color: #2f7cf6; font-size: 13px; margin-top: 14px; }
.note { font-size: 13px; color: #475569; }
.note ul { margin: 0; padding-left: 18px; line-height: 2; }
</style>
