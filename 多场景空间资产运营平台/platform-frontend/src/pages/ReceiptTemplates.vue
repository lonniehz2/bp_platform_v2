<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

const { t } = useI18n()
const router = useRouter()
const list = ref([])
const error = ref('')
const busy = ref(false)
const editingId = ref(null)
const preview = ref(false)
const historyRows = ref([])
const showHistory = ref(false)
const dragging = ref(false)
let dragStart = null
const form = reactive({ templateName: t('receiptTemplates.defaultName'), title: t('receiptTemplates.defaultTitle'), company: t('receiptTemplates.defaultCompany'), footer: t('receiptTemplates.defaultFooter'), titleSize: 18, companySize: 11, titleAlign: 'center', sealImage: '', sealSize: 90, sealX: 330, sealY: 120 })

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
    const body = JSON.stringify({ templateName: form.templateName, configJson: JSON.stringify({ title: form.title, company: form.company, footer: form.footer, titleSize: form.titleSize, companySize: form.companySize, titleAlign: form.titleAlign, sealImage: form.sealImage, sealSize: form.sealSize, sealX: form.sealX, sealY: form.sealY }) })
    if (editingId.value) await request(`/receipt-templates/${editingId.value}`, { method: 'POST', body })
    else await request('/receipt-templates', { method: 'POST', body })
    editingId.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
function startDrag(e) {
  dragging.value = true
  dragStart = { x: e.clientX, y: e.clientY, sealX: Number(form.sealX), sealY: Number(form.sealY) }
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}
function onDrag(e) {
  if (!dragging.value || !dragStart) return
  form.sealX = Math.max(0, Math.round(dragStart.sealX + (e.clientX - dragStart.x)))
  form.sealY = Math.max(0, Math.round(dragStart.sealY - (e.clientY - dragStart.y)))
}
function stopDrag() {
  dragging.value = false
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

function onSeal(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => { form.sealImage = String(reader.result || '') }
  reader.readAsDataURL(file)
}

function edit(x) {
  editingId.value = x.id
  window.scrollTo({ top: 0, behavior: 'smooth' })
  const c = JSON.parse(x.configJson || '{}')
  form.templateName = x.templateName
  form.title = c.title || ''
  form.company = c.company || ''
  form.footer = c.footer || ''
  form.titleSize = c.titleSize || 18
  form.companySize = c.companySize || 11
  form.titleAlign = c.titleAlign || 'center'
  form.sealImage = c.sealImage || ''
  form.sealSize = c.sealSize || 90
  form.sealX = c.sealX || 330
  form.sealY = c.sealY || 120
  preview.value = true
}
async function loadHistory(id) {
  try { historyRows.value = await request(`/receipt-templates/${id}/history`); showHistory.value = true } catch (e) { error.value = e.message }
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
      <div class="panel-head"><h2>{{ t('receiptTemplates.layout') }}</h2><span class="small muted">{{ t('receiptTemplates.layoutHint') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('receiptTemplates.titleSize') }}</label><input v-model.number="form.titleSize" type="number" min="10" max="32" /></div>
        <div class="field"><label>{{ t('receiptTemplates.companySize') }}</label><input v-model.number="form.companySize" type="number" min="9" max="20" /></div>
        <div class="field"><label>{{ t('receiptTemplates.align') }}</label><select v-model="form.titleAlign"><option value="left">L</option><option value="center">C</option><option value="right">R</option></select></div>
        <div class="field"><label>{{ t('receiptTemplates.sealSize') }}</label><input v-model.number="form.sealSize" type="number" min="40" max="160" /></div>
        <div class="field"><label>Seal X</label><input v-model.number="form.sealX" type="number" /></div>
        <div class="field"><label>Seal Y</label><input v-model.number="form.sealY" type="number" /></div>
        <div class="field"><label>{{ t('receiptTemplates.seal') }}</label><input type="file" accept="image/*" @change="onSeal" /></div>
      </div>
      <div class="a4-preview">
        <div class="a4-page">
          <h2 :style="{ fontSize: form.titleSize + 'px', textAlign: form.titleAlign }">{{ form.title }}</h2>
          <div :style="{ fontSize: form.companySize + 'px' }">{{ form.company }}</div>
          <div class="a4-lines"><div>Receipt No: PREVIEW-001</div><div>Payment No: PAY-PREVIEW-001</div><div>Amount: CNY 100.00</div><div>Date: 2026-11-12</div></div>
          <img v-if="form.sealImage" :src="form.sealImage" class="a4-seal" :style="{ width: form.sealSize + 'px', left: form.sealX + 'px', bottom: form.sealY + 'px' }" @mousedown.prevent="startDrag" />
          <div class="a4-footer">{{ form.footer }}</div>
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>{{ t('receiptTemplates.list') }}</h2></div>
      <div v-if="!list.length" class="empty">{{ t('receiptTemplates.empty') }}</div>
      <table v-else><thead><tr><th>{{ t('receiptTemplates.name') }}</th><th>{{ t('receiptTemplates.version') }}</th><th>{{ t('receiptTemplates.status') }}</th><th>{{ t('receiptTemplates.action') }}</th></tr></thead><tbody>
        <tr v-for="x in list" :key="x.id"><td>{{ x.templateName }}</td><td>{{ x.version }}</td><td>{{ x.status }}</td><td><button class="sm" @click="previewPdf(x.id)">{{ t('receiptTemplates.previewPdf') }}</button><button class="sm" @click="loadHistory(x.id)">{{ t('receiptTemplates.history') }}</button><button class="sm" @click="router.push(`/guarantee/receipt-designer/${x.id}`)">{{ t('receiptDesigner.title') }}</button><button class="sm" @click="edit(x)">{{ t('receiptTemplates.edit') }}</button><button v-if="x.status !== 'PUBLISHED'" class="sm" @click="publish(x.id)">{{ t('receiptTemplates.publish') }}</button></td></tr>
      </tbody></table>
    </div>

    <div v-if="editingId" class="panel" style="border-left:4px solid #1f6feb"><strong>{{ t('receiptTemplates.editTitle') }}</strong> <span class="small muted">{{ t('receiptTemplates.layoutHint') }}</span></div>

    <div v-if="showHistory" class="modal-mask" @click.self="showHistory = false">
      <div class="modal" style="max-width:760px">
        <div class="panel-head"><h2>{{ t('receiptTemplates.history') }}</h2><button class="sm" @click="showHistory = false">{{ t('receiptTemplates.close') }}</button></div>
        <div v-if="!historyRows.length" class="empty">{{ t('receiptTemplates.empty') }}</div>
        <table v-else><thead><tr><th>{{ t('receiptTemplates.version') }}</th><th>{{ t('receiptTemplates.config') }}</th><th>{{ t('receiptTemplates.time') }}</th></tr></thead><tbody><tr v-for="h in historyRows" :key="h.id"><td>{{ h.version }}</td><td class="mono small">{{ h.configJson }}</td><td>{{ h.createTime }}</td></tr></tbody></table>
      </div>
    </div>

    <div v-if="preview" class="modal-mask" @click.self="preview = false">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('receiptTemplates.preview') }}</h2><button class="sm" @click="preview = false">{{ t('receiptTemplates.close') }}</button></div>
        <h3>{{ form.title }}</h3><p>{{ form.company }}</p><p class="small muted">{{ form.footer }}</p><p>{{ t('receiptTemplates.previewHint') }}</p>
      </div>
    </div>
  </div>
</template>
