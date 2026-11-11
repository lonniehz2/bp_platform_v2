<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'
import Pager from '../components/Pager.vue'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const houses = ref([])
const meters = ref([])
const summary = ref([])
const readings = ref([])
const selected = ref(null)
const page = ref(1)
const error = ref('')
const busy = ref(false)
const form = reactive({ houseId: '', meterType: 'WATER', meterNo: '', initialReading: 0 })
const readForm = reactive({ meterId: '', readingDate: '', readingValue: '', readerName: t('meters.read') })
const editing = ref(null)
const editForm = reactive({ houseId: '', meterType: 'WATER', meterNo: '', installDate: '' })
const paged = computed(() => meters.value.slice((page.value - 1) * 10, page.value * 10))
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const id = project.value.id
    const [h, m, s] = await Promise.all([api.houses(id), api.meters(id), api.meterSummary(id)])
    houses.value = h; meters.value = m; summary.value = s
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!selected.value && m.length) selectMeter(m[0])
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.meterNo.trim()) throw new Error(t('meters.requiredNo'))
    await api.createMeter({
      projectId: project.value.id, houseId: form.houseId,
      meterType: form.meterType, meterNo: form.meterNo.trim(),
      initialReading: Number(form.initialReading || 0)
    })
    form.meterNo = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function selectMeter(m) {
  selected.value = m
  readings.value = await api.meterReadings(m.id)
}

async function read() {
  busy.value = true; error.value = ''
  try {
    if (!readForm.readingValue) throw new Error(t('meters.requiredReading'))
    await api.readMeter(selected.value.id, {
      readingDate: readForm.readingDate || null,
      readingValue: Number(readForm.readingValue),
      readerName: readForm.readerName
    })
    readForm.readingValue = ''
    await load()
    await selectMeter(meters.value.find(m => String(m.id) === String(selected.value.id)) || selected.value)
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openEdit(m) {
  editing.value = m
  Object.assign(editForm, { houseId: m.houseId || '', meterType: m.meterType || 'WATER', meterNo: m.meterNo || '', installDate: m.installDate || '' })
}

async function saveEdit() {
  busy.value = true; error.value = ''
  try {
    await api.updateMeter(editing.value.id, { ...editForm })
    editing.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function toggleStatus(m) {
  const next = m.meterStatus === 'ACTIVE' ? 'DISABLED' : 'ACTIVE'
  if (!await confirmAction({ title: t('meters.statusTitle'), message: t('meters.statusMessage', { no: m.meterNo, status: next }), confirmText: t('meters.confirm') })) return
  busy.value = true; error.value = ''
  try { await api.updateMeterStatus(m.id, next); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card"><div class="label">{{ t('meters.count') }}</div><div class="value">{{ meters.length }}</div><div class="hint">{{ t('meters.hint') }}</div></div>
      <div v-for="s in summary" :key="s.meterType" class="card">
        <div class="label">{{ t('meters.' + String(s.meterType).toLowerCase()) }}</div><div class="value">{{ s.meterCount }}</div><div class="hint">{{ t('meters.usage') }} {{ money(s.usageAmount) }}</div>
      </div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>{{ t('meters.title') }}</h2><p>{{ project?.orgName || t('meters.noProject') }} · {{ t('meters.subtitle') }}</p></div></div>
      <div class="row">
        <div class="field"><label>{{ t('meters.house') }}</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('meters.searchHouse')" /></div>
        <div class="field"><label>{{ t('meters.type') }}</label><select v-model="form.meterType"><option value="WATER">{{ t('meters.water') }}</option><option value="ELECTRICITY">{{ t('meters.electricity') }}</option><option value="GAS">{{ t('meters.gas') }}</option></select></div>
        <div class="field"><label>{{ t('meters.meterNo') }}</label><input v-model="form.meterNo" :placeholder="t('meters.meterNoPlaceholder')" /></div>
        <div class="field"><label>{{ t('meters.initial') }}</label><input v-model.number="form.initialReading" type="number" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="create">{{ t('meters.add') }}</button></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns: 1.2fr .8fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('meters.list') }}</h2><span class="small muted">{{ t('meters.listHint') }}</span></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>{{ t('meters.meterNo') }}</th><th>{{ t('meters.type') }}</th><th>{{ t('meters.house') }}</th><th>{{ t('meters.lastReading') }}</th><th>{{ t('meters.status') }}</th><th>{{ t('meters.action') }}</th></tr></thead>
            <tbody>
              <tr v-for="m in paged" :key="m.id" @click="selectMeter(m)" style="cursor:pointer">
                <td class="mono">{{ m.meterNo }}</td><td>{{ t('meters.' + String(m.meterType).toLowerCase()) }}</td><td>{{ m.houseName }}</td>
                <td>{{ money(m.currentReading) }}</td><td><span class="badge" :class="m.meterStatus === 'ACTIVE' ? 'green' : 'orange'">{{ m.meterStatus }}</span></td>
                <td><button v-if="can('asset')" class="sm" @click.stop="openEdit(m)">{{ t('meters.edit') }}</button> <button v-if="can('asset')" class="sm" :class="m.meterStatus === 'ACTIVE' ? 'danger' : ''" @click.stop="toggleStatus(m)">{{ m.meterStatus === 'ACTIVE' ? t('meters.disable') : t('meters.enable') }}</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pager :total="meters.length" :page="page" @update:page="page = $event" />
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('meters.read') }}</h2><span class="small muted">{{ selected?.meterNo || t('meters.noSelected') }}</span></div>
        <div v-if="!selected" class="empty">{{ t('meters.select') }}</div>
        <template v-else>
          <div class="row" style="margin-bottom:10px">
            <div class="field"><label>{{ t('meters.currentReading') }}</label><input v-model.number="readForm.readingValue" type="number" /></div>
            <div class="field"><label>{{ t('meters.date') }}</label><input v-model="readForm.readingDate" type="date" /></div>
            <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="read">{{ t('meters.saveReading') }}</button></div>
          </div>
          <div v-if="!readings.length" class="empty">{{ t('meters.noReadings') }}</div>
          <div v-for="r in readings" :key="r.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
            <div style="flex:1"><div>{{ r.readingDate }}</div><div class="small muted">{{ r.previousValue }} → {{ r.readingValue }}</div></div>
            <span class="badge blue">{{ t('meters.usage') }} {{ money(r.usageAmount) }}</span>
          </div>
        </template>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('meters.editTitle') }}</h2><button class="sm" @click="editing = null">{{ t('meters.close') }}</button></div>
        <div class="field"><label>{{ t('meters.meterNo') }}</label><input v-model="editForm.meterNo" /></div>
        <div class="field"><label>{{ t('meters.type') }}</label><select v-model="editForm.meterType"><option value="WATER">{{ t('meters.water') }}</option><option value="ELECTRICITY">{{ t('meters.electricity') }}</option><option value="GAS">{{ t('meters.gas') }}</option></select></div>
        <div class="field"><label>{{ t('meters.house') }}</label><SearchSelect v-model="editForm.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('meters.searchHouse')" /></div>
        <div class="field"><label>{{ t('meters.installDate') }}</label><input v-model="editForm.installDate" type="date" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveEdit">{{ t('meters.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
