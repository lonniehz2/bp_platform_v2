<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const list = ref([])
const error = ref('')
const busy = ref(false)
const editingId = ref(null)
const preview = ref(false)
const form = reactive({ templateName: t('receiptTemplates.defaultName'), title: t('receiptTemplates.defaultTitle'), company: t('receiptTemplates.defaultCompany'), footer: t('receiptTemplates.defaultFooter') })

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('platformToken') || ''}` }
  const res = await fetch('/api/v1/platform' + path, { ...options, headers })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json.code !== 'BP00000') throw new Error(json.message || t('receiptTemplates.failed'))
  return json.data
}
async function load() { try { list.value = await request('/receipt-templates') } catch (e) { error.value = e.message } }
async function save() {
  busy.value = true; error.value = ''
  try {
    const body = JSON.stringify({ templateName: form.templateName, configJson: JSON.stringify({ title: form.title, company: form.company, footer: form.footer }) })
    if (editingId.value) await request(`/receipt-templates/${editingId.value}`, { method: 'POST', body })
    else await request('/receipt-templates', { method: 'POST', body })
    editingId.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
function edit(x) {
  editingId.value = x.id
  const c = JSON.parse(x.configJson || '{}')
  form.templateName = x.templateName
  form.title = c.title || ''
  form.company = c.company || ''
  form.footer = c.footer || ''
  preview.value = false
}
async function previewPdf(id) {
  const res = await fetch(`/api/v1/platform/receipt-templates/${id}/preview.pdf`, { headers: { Authorization: `Bearer ${localStorage.getItem('platformToken') || ''}` } })
  if (!res.ok) { error.value = t('receiptTemplates.failed'); return }
  const url = URL.createObjectURL(await res.blob())
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 60000)
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
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="save">{{ editingId ? t('receiptTemplates.save') : t('receiptTemplates.create') }}</button></div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>{{ t('receiptTemplates.list') }}</h2></div>
      <div v-if="!list.length" class="empty">{{ t('receiptTemplates.empty') }}</div>
      <table v-else><thead><tr><th>{{ t('receiptTemplates.name') }}</th><th>{{ t('receiptTemplates.version') }}</th><th>{{ t('receiptTemplates.status') }}</th><th>{{ t('receiptTemplates.action') }}</th></tr></thead><tbody>
        <tr v-for="x in list" :key="x.id"><td>{{ x.templateName }}</td><td>{{ x.version }}</td><td>{{ x.status }}</td><td><button class="sm" @click="previewPdf(x.id)">{{ t('receiptTemplates.previewPdf') }}</button><button class="sm" @click="edit(x)">{{ t('receiptTemplates.edit') }}</button><button v-if="x.status !== 'PUBLISHED'" class="sm" @click="publish(x.id)">{{ t('receiptTemplates.publish') }}</button></td></tr>
      </tbody></table>
    </div>
  </div>
</template>
