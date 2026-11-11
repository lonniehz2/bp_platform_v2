<script setup>
import { computed, onMounted, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const houses = ref([])
const persons = ref([])
const houseId = ref('')
const personId = ref('')
const grants = ref([])
const error = ref('')
const busy = ref(false)
const house = computed(() => houses.value.find(h => String(h.id) === String(houseId.value)) || null)
const houseGrants = computed(() => grants.value.filter(g => g.targetType === 'SPACE' && String(g.targetId) === String(house.value?.spaceId)))

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
    const [h, p] = await Promise.all([api.houses(project.value.id), api.persons()])
    houses.value = h; persons.value = p
    if (!houseId.value && h.length) houseId.value = h[0].id
    if (!personId.value && p.length) personId.value = p[0].id
    await loadGrants()
  } catch (e) { error.value = e.message }
}

async function loadGrants() {
  if (!personId.value) { grants.value = []; return }
  try { grants.value = await api.grants(personId.value) } catch { grants.value = [] }
}

async function grant() {
  busy.value = true; error.value = ''
  try {
    if (!house.value?.spaceId) throw new Error(t('houseAccess.noSpace'))
    await api.createGrant({
      projectId: project.value.id, personId: personId.value, targetType: 'SPACE', targetId: house.value.spaceId,
      grantLevel: 'OPEN', validStart: '2026-11-08', validEnd: '2027-11-07', sourceType: 'MANUAL'
    })
    await loadGrants()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revoke(g) {
  if (!await confirmAction({ title: t('houseAccess.revokeTitle'), message: t('houseAccess.revokeMessage'), confirmText: t('houseAccess.revokeConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, t('houseAccess.revokeReason')); await loadGrants() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('houseAccess.title') }}</h2><p>{{ project?.orgName || t('houseAccess.noProject') }} · {{ t('houseAccess.subtitle') }}</p></div><span class="badge blue">{{ houseGrants.length }} {{ t('houseAccess.count') }}</span></div>
      <div class="row">
        <div class="field" style="flex:2"><label>{{ t('houseAccess.house') }}</label><SearchSelect v-model="houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('houseAccess.house')" /></div>
        <div class="field" style="flex:2"><label>{{ t('houseAccess.person') }}</label><SearchSelect v-model="personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('houseAccess.person')" @change="loadGrants" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="grant">{{ t('houseAccess.grant') }}</button></div>
      </div>
      <div class="alert" style="margin-top:10px">{{ t('houseAccess.hint') }}</div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('houseAccess.current') }}</h2><span class="small muted">{{ house?.houseName || t('houseAccess.noHouse') }}</span></div>
      <div v-if="!houseGrants.length" class="empty">{{ t('houseAccess.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('houseAccess.person') }}</th><th>{{ t('houseAccess.target') }}</th><th>{{ t('houseAccess.level') }}</th><th>{{ t('houseAccess.validity') }}</th><th>{{ t('houseAccess.status') }}</th><th>{{ t('houseAccess.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="g in houseGrants" :key="g.id">
              <td>{{ persons.find(p => String(p.id) === String(g.personId))?.personName || g.personId }}</td>
              <td class="mono">{{ g.targetId }}</td><td>{{ enumLabel(g.grantLevel) }}</td>
              <td class="small">{{ g.validStart }} ~ {{ g.validEnd || t('houseAccess.longTerm') }}</td>
              <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ enumLabel(g.grantStatus) }}</span></td>
              <td><button v-if="g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revoke(g)">{{ t('houseAccess.revoke') }}</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
