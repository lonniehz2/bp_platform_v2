<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Canvas, Textbox, FabricImage, Rect } from 'fabric'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const canvasEl = ref(null)
const error = ref('')
const busy = ref(false)
const templates = ref([])
const selectedId = ref(route.params.id ? String(route.params.id) : '')
const paper = ref('A4')
const PAPER = { A4: [595, 842], A5: [420, 595], B5: [499, 709] }
const form = reactive({ templateName: t('receiptDesigner.defaultName'), title: t('receiptDesigner.defaultTitle'), company: t('receiptDesigner.defaultCompany'), footer: t('receiptDesigner.defaultFooter') })
let canvas

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('platformToken') || ''}` }
  const res = await fetch('/api/v1/platform' + path, { ...options, headers })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json.code !== 'BP00000') throw new Error(json.message || t('receiptDesigner.failed'))
  return json.data
}
function addText(line = t('receiptDesigner.defaultText')) { canvas.add(new Textbox(line, { left: 60, top: 150, width: 300, fontSize: 16, fill: '#222' })) }
function applyPaper(size) {
  paper.value = size
  const [w, h] = PAPER[size] || PAPER.A4
  canvas.setDimensions({ width: w, height: h })
  canvas.calcOffset()
  canvas.requestRenderAll()
}
async function loadTemplateContent() {
  const tpl = templates.value.find(x => String(x.id) === selectedId.value)
  if (!tpl) return
  const c = JSON.parse(tpl.configJson || '{}')
  if (c.canvas?.objects) { canvas.clear(); canvas.backgroundColor = '#fff'; await canvas.loadFromJSON(c.canvas); canvas.requestRenderAll() }
}
function addField(key) { addText('{{' + key + '}}') }
function deleteSelected() {
  const obj = canvas.getActiveObject()
  if (obj) { canvas.remove(obj); canvas.discardActiveObject(); canvas.requestRenderAll() }
}
function addSeal(e) {
  const file = e.target.files?.[0]; if (!file) return
  const reader = new FileReader()
  reader.onload = async () => { const img = await FabricImage.fromURL(String(reader.result)); img.scaleToWidth(100); img.set({ left: 380, top: 620 }); canvas.add(img) }
  reader.readAsDataURL(file)
}
function addQr() { canvas.add(new Rect({ left: 60, top: 680, width: 80, height: 80, fill: '#111', role: 'qr' })) }
async function load() {
  templates.value = await api('/receipt-templates')
  if (!selectedId.value && templates.value[0]) selectedId.value = String(templates.value[0].id)
  const tpl = templates.value.find(x => String(x.id) === selectedId.value)
  if (!tpl) return
  form.templateName = tpl.templateName
  const c = JSON.parse(tpl.configJson || '{}')
  form.title = c.title || form.title; form.company = c.company || form.company; form.footer = c.footer || form.footer
  applyPaper(c.pageSize || 'A4')
  // Load the selected template version on entry
  if (c.canvas?.objects) {
    canvas.clear()
    canvas.backgroundColor = '#fff'
    await canvas.loadFromJSON(c.canvas)
    canvas.requestRenderAll()
  }
}
async function save() {
  busy.value = true; error.value = ''
  try {
    const configJson = JSON.stringify({ ...form, pageSize: paper.value, canvas: canvas.toJSON(['role']) })
    if (selectedId.value) await api(`/receipt-templates/${selectedId.value}`, { method: 'POST', body: JSON.stringify({ templateName: form.templateName, configJson }) })
    else await api('/receipt-templates', { method: 'POST', body: JSON.stringify({ templateName: form.templateName, configJson }) })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}
onMounted(async () => {
  canvas = new Canvas(canvasEl.value, { width: 595, height: 842, backgroundColor: '#fff', preserveObjectStacking: true })
  window.addEventListener('keydown', (e) => { if (e.key === 'Delete' || e.key === 'Backspace') deleteSelected() })
  await load()
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('receiptDesigner.title') }}</h2><p>{{ t('receiptDesigner.subtitle') }}</p></div><button class="primary" :disabled="busy" @click="save">{{ t('receiptDesigner.save') }}</button></div>
      <div class="row" style="margin-bottom:8px">
        <select v-model="selectedId" @change="load"><option v-for="x in templates" :key="x.id" :value="String(x.id)">{{ x.templateName }} v{{ x.version }}</option></select>
        <button class="sm" @click="loadTemplateContent">{{ t('receiptDesigner.loadTemplate') }}</button>
      </div>
      <div class="row" style="margin-bottom:10px">
        <label class="small muted" style="align-self:center">{{ t('receiptDesigner.paperSize') }}</label>
        <select :value="paper" @change="applyPaper($event.target.value)"><option value="A4">A4 (595 x 842)</option><option value="A5">A5 (420 x 595)</option><option value="B5">B5 (499 x 709)</option></select>
        <button class="sm" @click="addText()">{{ t('receiptDesigner.addText') }}</button>
        <button class="sm" @click="addField('paymentNo')">{{ t('receiptDesigner.paymentNo') }}</button><button class="sm" @click="addField('paymentMethod')">{{ t('receiptDesigner.paymentMethod') }}</button><button class="sm" @click="addField('issuedTime')">{{ t('receiptDesigner.issuedTime') }}</button><button class="sm" @click="addField('receiptStatus')">{{ t('receiptDesigner.status') }}</button><button class="sm" @click="addQr">{{ t('receiptDesigner.addQr') }}</button><button class="sm danger" @click="deleteSelected">{{ t('receiptDesigner.deleteSelected') }}</button>
        <label class="sm">{{ t('receiptDesigner.addSeal') }}<input type="file" accept="image/*" style="display:none" @change="addSeal" /></label>
      </div>
    </div>
    <div class="panel" style="overflow:auto;background:#eef1f5">
      <div class="canvas-stage"><canvas ref="canvasEl"></canvas></div>
    </div>
  </div>
</template>

<style scoped>
.canvas-stage {
  display: inline-block;
  padding: 8px;
  background: #fff;
  border: 1px dashed #98a2b3;
  box-shadow: 0 0 0 1px rgba(15, 23, 42, .04), 0 6px 18px rgba(15, 23, 42, .08);
}
.canvas-stage :deep(.canvas-container) {
  outline: 1px solid #e2e8f0;
  outline-offset: 0;
}
</style>
