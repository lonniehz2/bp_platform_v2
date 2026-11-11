<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const waitlist = ref([])
const houses = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ waitlistId: '', houseId: '' })
const waiting = computed(() => waitlist.value.filter(w => w.waitlistStatus === 'WAITING'))
const vacant = computed(() => houses.value.filter(h => h.houseStatus === 'VACANT'))
const allocated = computed(() => waitlist.value.filter(w => w.waitlistStatus === 'ALLOCATED'))

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
    const [w, h] = await Promise.all([api.waitlist(project.value.id), api.houses(project.value.id)])
    waitlist.value = w; houses.value = h
  } catch (e) { error.value = e.message }
}

async function allocate() {
  busy.value = true; error.value = ''
  try {
    if (!form.waitlistId || !form.houseId) throw new Error(t('allocations.required'))
    await api.allocate(form.waitlistId, form.houseId)
    form.waitlistId = ''; form.houseId = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card"><div class="label">{{ t('allocations.waiting') }}</div><div class="value">{{ waiting.length }}</div><div class="hint">{{ t('allocations.queue') }}</div></div>
      <div class="card"><div class="label">{{ t('allocations.allocated') }}</div><div class="value">{{ allocated.length }}</div><div class="hint">{{ t('allocations.history') }}</div></div>
      <div class="card"><div class="label">{{ t('allocations.vacant') }}</div><div class="value">{{ vacant.length }}</div><div class="hint">{{ t('allocations.available') }}</div></div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>{{ t('allocations.title') }}</h2><p>{{ project?.orgName || t('allocations.noProject') }} · {{ t('allocations.subtitle') }}</p></div></div>
      <div class="row">
        <div class="field"><label>{{ t('allocations.record') }}</label><SearchSelect v-model="form.waitlistId" :options="waiting" label-key="queueNo" sublabel-key="applicantName" value-key="id" :placeholder="t('allocations.searchRecord')" /></div>
        <div class="field"><label>{{ t('allocations.house') }}</label><SearchSelect v-model="form.houseId" :options="vacant" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('allocations.searchVacant')" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="allocate">{{ t('allocations.confirm') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('allocations.records') }}</h2><span class="small muted">{{ waitlist.length }} {{ t('allocations.count') }}</span></div>
      <div v-if="!waitlist.length" class="empty">{{ t('allocations.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('allocations.queueNo') }}</th><th>{{ t('allocations.applicationNo') }}</th><th>{{ t('allocations.applicant') }}</th><th>{{ t('allocations.status') }}</th></tr></thead>
          <tbody>
            <tr v-for="w in waitlist" :key="w.id">
              <td>{{ w.queueNo }}</td><td class="mono">{{ w.applicationNo }}</td><td>{{ w.applicantName }}</td>
              <td><span class="badge" :class="w.waitlistStatus === 'ALLOCATED' ? 'green' : 'orange'">{{ enumLabel(w.waitlistStatus) }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
