<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()
const forcedType = computed(() => route.meta?.changeType || '')
const visibleChanges = computed(() => forcedType.value ? changes.value.filter(c => c.changeType === forcedType.value) : changes.value)
const pageTitle = computed(() => ({ TERMINATION: t('changes.termination'), ROOM_CHANGE: t('changes.room') }[forcedType.value] || t('changes.title')))
const project = ref(null)
const contracts = ref([])
const selectedContractId = ref('')
const changes = ref([])
const houses = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ changeType: forcedType.value || 'RENT_CHANGE', rentAmount: 1500, endDate: '2027-10-31', houseId: '', effectiveDate: '2026-12-01', reason: t('changes.pageReason') })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', APPROVING: 'orange' }[s] || '')

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  return chosen || all.slice().sort((a, b) =>
    ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
    ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
  )[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const [cs, hs] = await Promise.all([api.contracts(project.value.id), api.houses(project.value.id)])
    contracts.value = cs
    houses.value = hs.filter(h => h.houseStatus === 'VACANT')
    if (!selectedContractId.value && contracts.value.length) selectedContractId.value = contracts.value[0].id
    if (!form.houseId && houses.value.length) form.houseId = houses.value[0].id
    await loadChanges()
  } catch (e) { error.value = e.message }
}

async function loadChanges() {
  if (!selectedContractId.value) return
  changes.value = await api.changes(selectedContractId.value)
}

async function create() {
  busy.value = true; error.value = ''
  try {
    await api.createChange(selectedContractId.value, {
      changeType: form.changeType,
      after: form.changeType === 'RENT_CHANGE'
        ? { rentAmount: Number(form.rentAmount) }
        : form.changeType === 'ROOM_CHANGE'
          ? { houseId: form.houseId }
          : { endDate: form.endDate },
      effectiveDate: form.effectiveDate,
      reason: form.reason
    })
    await loadChanges()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function submit(id) { await run(() => api.submitChange(id)) }
async function approve(id) { await run(() => api.approveChange(id, { approverName: t('changes.manager'), comment: t('changes.approvedComment') })) }
async function reject(id) { await run(() => api.rejectChange(id, { approverName: t('changes.manager'), comment: t('changes.rejectedComment') })) }

async function run(fn) {
  busy.value = true; error.value = ''
  try { await fn(); await loadChanges() } catch (e) { error.value = e.message } finally { busy.value = false }
}

watch(selectedContractId, loadChanges)
watch(forcedType, (v) => { if (v) form.changeType = v }, { immediate: true })
onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">{{ t('changes.createProject') }}</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ pageTitle }}</h2><p>{{ project.orgName }} · {{ t('changes.subtitle') }}</p></div>
          <select v-model="selectedContractId" style="max-width:320px">
            <option value="">{{ t('changes.selectContract') }}</option>
            <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.contractNo }} · {{ c.personName }}</option>
          </select>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('changes.newChange') }}</h2><span class="small muted">{{ t('changes.approvalHint') }}</span></div>
        <div class="row">
          <div class="field" v-if="!forcedType"><label>{{ t('changes.type') }}</label>
            <select v-model="form.changeType"><option value="RENT_CHANGE">{{ t('changes.rentChange') }}</option><option value="TERM_CHANGE">{{ t('changes.termChange') }}</option><option value="ROOM_CHANGE">{{ t('changes.roomChange') }}</option><option value="TERMINATION">{{ t('changes.terminationType') }}</option></select>
          </div>
          <div class="field" v-if="form.changeType === 'RENT_CHANGE'"><label>{{ t('changes.newRent') }}</label><input v-model.number="form.rentAmount" type="number" /></div>
          <div class="field" v-else-if="form.changeType === 'ROOM_CHANGE'"><label>{{ t('changes.newHouse') }}</label>
            <SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('changes.searchHouse')" />
          </div>
          <div class="field" v-else><label>{{ t('changes.newEnd') }}</label><input v-model="form.endDate" type="date" /></div>
          <div class="field"><label>{{ t('changes.effectiveDate') }}</label><input v-model="form.effectiveDate" type="date" /></div>
          <div class="field"><label>{{ t('changes.reason') }}</label><input v-model="form.reason" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('contract')" class="primary" :disabled="busy" @click="create">{{ t('changes.create') }}</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('changes.records') }}</h2><span class="small muted">{{ changes.length }} {{ t('changes.records') }} · {{ t('changes.recordHint') }}</span></div>
        <div v-if="!changes.length" class="empty">{{ t('changes.empty') }}</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>{{ t('changes.type') }}</th><th>{{ t('changes.effectiveDate') }}</th><th>{{ t('changes.status') }}</th><th>{{ t('changes.reason') }}</th><th>{{ t('changes.action') }}</th></tr></thead>
            <tbody>
              <tr v-for="c in visibleChanges" :key="c.id">
                <td>{{ c.changeType }}</td><td>{{ c.effectiveDate }}</td>
                <td>
                  <span class="badge" :class="statusClass(c.changeStatus)">{{ c.changeStatus }}</span>
                  <div v-if="c.changeStatus === 'APPROVING' && c.currentNode" class="small muted">{{ t('changes.currentNode') }}：{{ c.currentNode }}</div>
                </td>
                <td>{{ c.reason }}</td>
                <td class="row">
                  <button class="sm" v-if="c.changeStatus === 'DRAFT'" @click="submit(c.id)">{{ t('changes.submit') }}</button>
                  <button class="sm" v-if="c.changeStatus === 'APPROVING'" @click="approve(c.id)">{{ t('changes.approve') }}</button>
                  <button class="sm danger" v-if="c.changeStatus === 'APPROVING'" @click="reject(c.id)">{{ t('changes.reject') }}</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
