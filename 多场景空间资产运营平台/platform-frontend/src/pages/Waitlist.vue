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
    if (!form.waitlistId || !form.houseId) throw new Error(t('waitlist.required'))
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
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('waitlist.title') }}</h2><p>{{ project?.orgName || t('waitlist.noProject') }} · {{ t('waitlist.subtitle') }}</p></div><span class="badge blue">{{ waiting.length }} {{ t('waitlist.waiting') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('waitlist.record') }}</label><SearchSelect v-model="form.waitlistId" :options="waiting" label-key="queueNo" sublabel-key="applicantName" value-key="id" :placeholder="t('waitlist.searchRecord')" /></div>
        <div class="field"><label>{{ t('waitlist.vacant') }}</label><SearchSelect v-model="form.houseId" :options="vacant" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('waitlist.searchVacant')" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="allocate">{{ t('waitlist.allocate') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('waitlist.queue') }}</h2><span class="small muted">{{ waitlist.length }} {{ t('waitlist.count') }}</span></div>
      <div v-if="!waitlist.length" class="empty">{{ t('waitlist.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('waitlist.queueNo') }}</th><th>{{ t('waitlist.applicationNo') }}</th><th>{{ t('waitlist.applicant') }}</th><th>{{ t('waitlist.status') }}</th><th>{{ t('waitlist.createTime') }}</th></tr></thead>
          <tbody>
            <tr v-for="w in waitlist" :key="w.id">
              <td class="mono">{{ w.queueNo }}</td><td class="mono">{{ w.applicationNo }}</td><td>{{ w.applicantName }}</td>
              <td><span class="badge" :class="w.waitlistStatus === 'ALLOCATED' ? 'green' : 'blue'">{{ enumLabel(w.waitlistStatus) }}</span></td>
              <td class="small">{{ w.createTime }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
