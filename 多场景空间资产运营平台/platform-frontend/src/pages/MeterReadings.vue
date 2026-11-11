<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const meters = ref([])
const selected = ref(null)
const readings = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ readingDate: '', readingValue: '', readerName: t('readings.reader') })
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
    meters.value = await api.meters(project.value.id)
    if (!selected.value && meters.value.length) await selectMeter(meters.value[0])
  } catch (e) { error.value = e.message }
}

async function selectMeter(m) {
  selected.value = m
  readings.value = await api.meterReadings(m.id)
}

async function read() {
  busy.value = true; error.value = ''
  try {
    if (!selected.value) throw new Error(t('readings.requiredMeter'))
    if (form.readingValue === '') throw new Error(t('readings.requiredReading'))
    await api.readMeter(selected.value.id, {
      readingDate: form.readingDate || null, readingValue: Number(form.readingValue), readerName: form.readerName
    })
    form.readingValue = ''
    await load()
    await selectMeter(meters.value.find(m => String(m.id) === String(selected.value.id)) || selected.value)
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="panel">
        <div class="panel-head"><div><h2>{{ t('readings.title') }}</h2><p>{{ project?.orgName || t('readings.noProject') }} · {{ t('readings.subtitle') }}</p></div><span class="badge blue">{{ meters.length }} {{ t('readings.count') }}</span></div>
        <div v-if="!meters.length" class="empty">{{ t('readings.emptyMeters') }}</div>
        <div v-else class="table-wrap">
          <table>
            <thead><tr><th>{{ t('readings.meterNo') }}</th><th>{{ t('readings.type') }}</th><th>{{ t('readings.house') }}</th><th>{{ t('readings.current') }}</th></tr></thead>
            <tbody>
              <tr v-for="m in meters" :key="m.id" @click="selectMeter(m)" style="cursor:pointer">
                <td class="mono">{{ m.meterNo }}</td><td>{{ m.meterType }}</td><td>{{ m.houseName }}</td><td>{{ money(m.currentReading) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('readings.records') }}</h2><span class="small muted">{{ selected?.meterNo || t('readings.noSelected') }}</span></div>
        <div v-if="selected" class="row" style="margin-bottom:10px">
          <div class="field"><label>{{ t('readings.currentReading') }}</label><input v-model="form.readingValue" type="number" /></div>
          <div class="field"><label>{{ t('readings.date') }}</label><input v-model="form.readingDate" type="date" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('asset')" class="primary" :disabled="busy" @click="read">{{ t('readings.save') }}</button></div>
        </div>
        <div v-if="!readings.length" class="empty">{{ t('readings.empty') }}</div>
        <div v-for="r in readings" :key="r.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ r.readingDate }}</div><div class="small muted">{{ r.previousValue }} → {{ r.readingValue }}</div></div>
          <span class="badge blue">{{ t('readings.usage') }} {{ money(r.usageAmount) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
