<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const loading = ref(true)
const error = ref('')
const result = ref(null)

onMounted(async () => {
  try {
    const res = await fetch(`/api/v1/public/receipts/verify/${encodeURIComponent(route.params.token || '')}`, { headers: { 'X-Tenant-Id': '350600' } })
    const json = await res.json().catch(() => ({}))
    if (!res.ok || json.code !== 'BP00000') throw new Error(json.message || t('receiptVerify.failed'))
    result.value = json.data
  } catch (e) { error.value = e.message } finally { loading.value = false }
})
</script>

<template>
  <main class="verify-page">
    <div class="verify-card">
      <div class="brand-mark">MS</div>
      <h1>{{ t('receiptVerify.title') }}</h1>
      <p class="muted">{{ t('receiptVerify.subtitle') }}</p>
      <div v-if="loading" class="empty">{{ t('receiptVerify.loading') }}</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="result?.valid" class="valid">
        <div class="valid-mark">✓</div>
        <h2>{{ t('receiptVerify.valid') }}</h2>
        <dl>
          <dt>{{ t('receiptVerify.receiptNo') }}</dt><dd>{{ result.receiptNo }}</dd>
          <dt>{{ t('receiptVerify.paymentNo') }}</dt><dd>{{ result.paymentNo }}</dd>
          <dt>{{ t('receiptVerify.amount') }}</dt><dd>¥{{ Number(result.amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) }}</dd>
          <dt>{{ t('receiptVerify.issuedTime') }}</dt><dd>{{ result.issuedTime }}</dd>
          <dt>{{ t('receiptVerify.verifyCode') }}</dt><dd class="mono">{{ result.verifyCode }}</dd>
        </dl>
      </div>
      <div v-else class="invalid">
        <div class="invalid-mark">!</div>
        <h2>{{ t('receiptVerify.invalid') }}</h2>
        <p v-if="result?.status === 'REFUNDED'">{{ t('receiptVerify.refunded') }}</p>
        <p v-else-if="result?.status === 'VOID'">{{ t('receiptVerify.voided') }}</p>
        <p v-else>{{ t('receiptVerify.invalidHint') }}</p>
      </div>
      <p class="small muted">{{ t('receiptVerify.footer') }}</p>
    </div>
  </main>
</template>

<style scoped>
.verify-page { min-height:100vh; display:grid; place-items:center; background:#f4f6f8; padding:24px; }
.verify-card { width:min(560px,100%); background:#fff; border:1px solid #e3e8ef; border-radius:14px; padding:32px; box-shadow:0 8px 30px rgba(20,40,70,.08); }
.brand-mark { width:42px; height:42px; display:grid; place-items:center; border-radius:10px; background:#1f6feb; color:#fff; font-weight:700; margin-bottom:16px; }
h1 { margin:0 0 6px; } h2 { margin:8px 0; } .muted { color:#667085; } .small { font-size:12px; }
.valid-mark,.invalid-mark { width:48px; height:48px; border-radius:50%; display:grid; place-items:center; font-size:24px; font-weight:700; }
.valid-mark { background:#e8f7ee; color:#1a7f37; } .invalid-mark { background:#fdecec; color:#c62828; }
dl { display:grid; grid-template-columns:140px 1fr; gap:10px 12px; margin-top:20px; } dt { color:#667085; } dd { margin:0; font-weight:600; }
.mono { font-family:ui-monospace,Consolas,monospace; }
</style>
