<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const list = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ templateName: t('receiptTemplates.defaultName'), title: t('receiptTemplates.defaultTitle'), company: t('receiptTemplates.defaultCompany'), footer: t('receiptTemplates.defaultFooter') })

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('platformToken') || ''}` }
  const res = await fetch('/api/v1/platform' + path, { ...options, headers })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json.code !== 'BP00000') throw new Error(json.message || t('receiptTemplates.failed'))
  return json.data
}
async function load() { try { list.value = await request('/receipt-templates') } catch (e) { error.value = e.message } }
async function create() {
  busy.value = true; error.value = ''
  try {
    await request('/receipt-templates', { method: 'POST', body: JSON.stringify({ templateName: form.templateName, configJson: JSON.stringify({ title: form.title, company: form.company, footer: form.footer }) }) })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
async function publish(id) { try { await request(`/receipt-templates/${id}/publish`, { method: 'POST' }); await load() } catch (e) { error.value = e.message } }
onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('receiptTemplates.title') }}</h2><p>{{ t('receiptTemplates.subtitle') }}</p></div><span class="badge blue">{{ list.length }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('receiptTemplates.name') }}</label><input v-model="form.templateName" /></div>
        <div class="field"><label>{{ t('receiptTemplates.titleField') }}</label><input v-model="form.title" /></div>
        <div class="field"><label>{{ t('receiptTemplates.company') }}</label><input v-model="form.company" /></div>
        <div class="field" style="flex:2"><label>{{ t('receiptTemplates.footer') }}</label><input v-model="form.footer" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">{{ t('receiptTemplates.create') }}</button></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>{{ t('receiptTemplates.list') }}</h2></div>
      <div v-if="!list.length" class="empty">{{ t('receiptTemplates.empty') }}</div>
      <table v-else><thead><tr><th>{{ t('receiptTemplates.name') }}</th><th>{{ t('receiptTemplates.version') }}</th><th>{{ t('receiptTemplates.status') }}</th><th>{{ t('receiptTemplates.action') }}</th></tr></thead><tbody>
        <tr v-for="x in list" :key="x.id"><td>{{ x.templateName }}</td><td>{{ x.version }}</td><td>{{ x.status }}</td><td><button v-if="x.status !== 'PUBLISHED'" class="sm" @click="publish(x.id)">{{ t('receiptTemplates.publish') }}</button></td></tr>
      </tbody></table>
    </div>
  </div>
</template>
