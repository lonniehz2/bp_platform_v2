<script setup>
import { onMounted, reactive, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { sceneRoot } from '../scene'
import { can, canAction } from '../permissions'
import SearchSelect from '../components/SearchSelect.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const applications = ref([])
const persons = ref([])
const houses = ref([])
const waitlist = ref([])
const detailApp = ref(null)
const createOpen = ref(false)
const allocateOpen = ref(false)
const error = ref('')
const busy = ref(false)
const form = reactive({ applicationNo: '', applicantPersonId: '', familySize: 1, applicationType: 'PUBLIC_RENTAL', contactPhone: '', incomeLevel: 'LOW', housingStatus: 'NO_HOUSE', urgency: 'NORMAL', remark: '', guaranteeType: 'PUBLIC_RENTAL', familyType: 'SINGLE', subsidyStatus: 'NONE', archiveNo: '' })
const allocateForm = reactive({ waitlistId: '', houseId: '' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', SUBMITTED: 'orange' }[s] || '')
const money = (v) => Number(v || 0).toLocaleString('zh-CN')
const incomeLabel = (v) => ({ LOW: t('ap.lowIncome'), LOWER_MIDDLE: t('ap.lowerMiddle'), MIDDLE: t('ap.middle') }[v] || v || '-')
const housingLabel = (v) => ({ NO_HOUSE: t('ap.noHouse'), RENTING: t('ap.renting'), WITH_FAMILY: t('ap.withFamily') }[v] || v || '-')
const urgencyLabel = (v) => ({ NORMAL: t('ap.normal'), URGENT: t('ap.urgent') }[v] || v || '-')

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  if (chosen) return chosen
  const demo = all.find(p => p.orgCode === 'DEMO_PROJECT')
  if (demo) return demo
  return all.slice().sort((a, b) =>
    ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
    ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
  )[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    localStorage.setItem('platformProjectId', project.value.id)
    const [a, p, h, w] = await Promise.all([
      api.applications(project.value.id), api.persons().catch(() => []),
      api.houses(project.value.id).catch(() => []), api.waitlist(project.value.id).catch(() => [])
    ])
    applications.value = a; persons.value = p; houses.value = h; waitlist.value = w
    if (!form.applicantPersonId && p.length) form.applicantPersonId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.applicationNo.trim()) throw new Error(t('ap.requiredNo'))
    if (!form.applicantPersonId) throw new Error(t('ap.requiredApplicant'))
    if (form.contactPhone && !/^1\d{10}$/.test(form.contactPhone)) throw new Error(t('ap.invalidPhone'))
    if (Number(form.familySize) < 1 || Number(form.familySize) > 20) throw new Error(t('ap.familyRange'))
    await api.createApplication({
      projectId: project.value.id,
      applicationNo: form.applicationNo.trim(),
      applicantPersonId: form.applicantPersonId,
      applicationType: form.applicationType,
      familySize: Number(form.familySize || 1), contactPhone: form.contactPhone,
      incomeLevel: form.incomeLevel, housingStatus: form.housingStatus,
      urgency: form.urgency, remark: form.remark,
      guaranteeType: form.guaranteeType, familyType: form.familyType,
      subsidyStatus: form.subsidyStatus, archiveNo: form.archiveNo
    })
    form.applicationNo = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function submit(id) { await run(() => api.submitApplication(id)) }
async function approve(id) { await run(() => api.approveApplication(id, t('ap.approveComment'))) }
async function wait(id) { await run(() => api.joinWaitlist(id)) }
async function reject(id) { const comment = window.prompt(t('ap.rejectPrompt')) || t('ap.rejectDefault'); await run(() => api.rejectApplication(id, comment)) }
async function returnForSupplement(id) { const comment = window.prompt(t('ap.returnPrompt')) || t('ap.returnDefault'); await run(() => api.returnApplication(id, comment)) }
async function resubmit(id) { await run(() => api.resubmitApplication(id)) }

async function discardApplication(a) {
  if (!await confirmAction({ title: t('ap.discardTitle'), message: t('ap.discardMessage', { no: a.applicationNo }), confirmText: t('ap.discardConfirm'), danger: true })) return
  await run(() => api.discardApplication(a.id))
}

async function closeApplication(a) {
  if (!await confirmAction({ title: t('ap.closeTitle'), message: t('ap.closeMessage', { no: a.applicationNo }), confirmText: t('ap.closeConfirm'), danger: true })) return
  await run(() => api.closeApplication(a.id))
}

async function allocate() {
  if (!allocateForm.waitlistId || !allocateForm.houseId) { error.value = t('ap.requiredAllocate'); return }
  await run(() => api.allocate(allocateForm.waitlistId, allocateForm.houseId))
}

async function run(fn) {
  busy.value = true; error.value = ''
  try { await fn(); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">{{ t('ap.createProject') }}</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head">
          <div><h2>{{ t('ap.title') }}</h2><p>{{ project.orgName }} · {{ t('ap.subtitle') }}</p></div>
          <div class="row">
            <button v-if="canAction('application:create', 'application')" class="primary" @click="createOpen = true">{{ t('ap.new') }}</button>
            <button v-if="canAction('allocation:create', 'application')" class="sm" @click="allocateOpen = true">{{ t('ap.allocate') }}</button>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('ap.list') }}</h2><span class="small muted">{{ t('ap.listHint') }}</span></div>
        <div v-if="!applications.length" class="empty">{{ t('ap.empty') }}</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>{{ t('ap.appNo') }}</th><th>{{ t('ap.applicant') }}</th><th>{{ t('ap.guarantee') }}</th><th>{{ t('ap.familyType') }}</th><th>{{ t('ap.archive') }}</th><th>{{ t('ap.familySize') }}</th><th>{{ t('ap.income') }}</th><th>{{ t('ap.housing') }}</th><th>{{ t('ap.status') }}</th><th>{{ t('ap.action') }}</th></tr></thead>
            <tbody>
              <tr v-for="a in applications" :key="a.id">
                <td class="mono">{{ a.applicationNo }}</td>
                <td>{{ a.applicantName }}</td>
                <td>{{ enumLabel(a.guaranteeType || '-') }}</td><td>{{ enumLabel(a.familyType || '-') }}</td><td>{{ a.archiveNo || '-' }}</td>
                <td>{{ a.familySize }}</td><td>{{ incomeLabel(a.incomeLevel) }}</td><td>{{ housingLabel(a.housingStatus) }}</td>
                <td><span class="badge" :class="statusClass(a.applicationStatus)">{{ enumLabel(a.applicationStatus) }}</span></td>
                <td class="row">
                  <button class="sm" @click="detailApp = a">{{ t('ap.detail') }}</button>
                  <button class="sm" v-if="canAction('application:submit', 'application') && a.applicationStatus === 'DRAFT'" :disabled="busy" @click="submit(a.id)">{{ t('ap.submit') }}</button>
                  <button class="sm danger" v-if="canAction('application:discard', 'application') && a.applicationStatus === 'DRAFT'" :disabled="busy" @click="discardApplication(a)">{{ t('ap.discard') }}</button>
                  <button class="sm" v-if="canAction('application:approve', 'application') && a.applicationStatus === 'SUBMITTED'" :disabled="busy" @click="approve(a.id)">{{ t('ap.approve') }}</button>
                  <button class="sm danger" v-if="canAction('application:reject', 'application') && a.applicationStatus === 'SUBMITTED'" :disabled="busy" @click="reject(a.id)">{{ t('ap.reject') }}</button>
                  <button class="sm" v-if="canAction('application:return', 'application') && a.applicationStatus === 'SUBMITTED'" :disabled="busy" @click="returnForSupplement(a.id)">{{ t('ap.returnSupplement') }}</button>
                  <button class="sm" v-if="canAction('application:resubmit', 'application') && a.applicationStatus === 'RETURNED'" :disabled="busy" @click="resubmit(a.id)">{{ t('ap.resubmit') }}</button>
                  <button class="sm" v-if="canAction('application:waitlist', 'application') && a.applicationStatus === 'APPROVED'" :disabled="busy" @click="wait(a.id)">{{ t('ap.waitlist') }}</button>
                  <button class="sm" v-if="canAction('application:close', 'application') && ['CONTRACTED','REJECTED'].includes(a.applicationStatus)" :disabled="busy" @click="closeApplication(a)">{{ t('ap.close') }}</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('ap.waitTitle') }}</h2><span class="small muted">{{ t('ap.waitHint') }}</span></div>
        <div v-if="!waitlist.length" class="empty">{{ t('ap.noWait') }}</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>{{ t('ap.queueNo') }}</th><th>{{ t('ap.appNo') }}</th><th>{{ t('ap.applicant') }}</th><th>{{ t('ap.status') }}</th></tr></thead>
            <tbody>
              <tr v-for="w in waitlist" :key="w.id">
                <td>{{ w.queueNo }}</td><td class="mono">{{ w.applicationNo }}</td><td>{{ w.applicantName }}</td>
                <td><span class="badge" :class="w.waitlistStatus === 'ALLOCATED' ? 'green' : 'blue'">{{ enumLabel(w.waitlistStatus) }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-if="detailApp" class="modal-mask" @click.self="detailApp = null">
      <div class="modal" style="max-width:720px">
        <div class="panel-head"><h2>{{ t('ap.detailTitle') }}</h2><button class="sm" @click="detailApp = null">{{ t('ap.close') }}</button></div>
        <div class="row" style="justify-content:flex-end;margin-bottom:8px"><RouterLink class="sm" :to="`${sceneRoot()}/detail/APPLICATION/${detailApp.id}`">{{ t('ap.openDetail') }}</RouterLink></div>
        <EntityDetailTabs type="APPLICATION" :entity-id="detailApp.id" />
        <div class="row">
          <div class="field"><label>{{ t('ap.appNo') }}</label><div class="mono">{{ detailApp.applicationNo }}</div></div>
          <div class="field"><label>{{ t('ap.applicant') }}</label><div>{{ detailApp.applicantName }}</div></div>
          <div class="field"><label>{{ t('ap.status') }}</label><span class="badge" :class="statusClass(detailApp.applicationStatus)">{{ enumLabel(detailApp.applicationStatus) }}</span></div>
          <div class="field"><label>{{ t('ap.guarantee') }}</label><div>{{ enumLabel(detailApp.guaranteeType || '-') }}</div></div>
          <div class="field"><label>{{ t('ap.familyType') }}</label><div>{{ enumLabel(detailApp.familyType || '-') }}</div></div>
          <div class="field"><label>{{ t('ap.familySize') }}</label><div>{{ detailApp.familySize }}</div></div>
          <div class="field"><label>{{ t('ap.income') }}</label><div>{{ incomeLabel(detailApp.incomeLevel) }}</div></div>
          <div class="field"><label>{{ t('ap.housing') }}</label><div>{{ housingLabel(detailApp.housingStatus) }}</div></div>
          <div class="field"><label>{{ t('ap.archive') }}</label><div>{{ detailApp.archiveNo || '-' }}</div></div>
        </div>
      </div>
    </div>

    <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
      <div class="modal" style="max-width:860px">
        <div class="panel-head"><h2>{{ t('ap.new') }}</h2><button class="sm" @click="createOpen = false">{{ t('ap.close') }}</button></div>
        <div class="row">
          <div class="field"><label>{{ t('ap.appNo') }}</label><input v-model="form.applicationNo" :placeholder="t('ap.appNo')" /></div>
          <div class="field"><label>{{ t('ap.applicant') }}</label><SearchSelect v-model="form.applicantPersonId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('ap.applicant')" /></div>
          <div class="field"><label>{{ t('ap.type') }}</label><select v-model="form.applicationType"><option value="PUBLIC_RENTAL">{{ t('ap.publicRental') }}</option><option value="AFFORDABLE_RENTAL">{{ t('ap.affordable') }}</option><option value="TALENT_APARTMENT">{{ t('ap.talent') }}</option><option value="DORMITORY">{{ t('ap.dormitory') }}</option></select></div>
          <div class="field"><label>{{ t('ap.familySize') }}</label><input v-model.number="form.familySize" type="number" min="1" /></div>
          <div class="field"><label>{{ t('ap.phone') }}</label><input v-model="form.contactPhone" /></div>
          <div class="field"><label>{{ t('ap.income') }}</label><select v-model="form.incomeLevel"><option value="LOW">{{ t('ap.lowIncome') }}</option><option value="LOWER_MIDDLE">{{ t('ap.lowerMiddle') }}</option><option value="MIDDLE">{{ t('ap.middle') }}</option></select></div>
          <div class="field"><label>{{ t('ap.housing') }}</label><select v-model="form.housingStatus"><option value="NO_HOUSE">{{ t('ap.noHouse') }}</option><option value="RENTING">{{ t('ap.renting') }}</option><option value="WITH_FAMILY">{{ t('ap.withFamily') }}</option></select></div>
          <div class="field"><label>{{ t('ap.urgency') }}</label><select v-model="form.urgency"><option value="NORMAL">{{ t('ap.normal') }}</option><option value="URGENT">{{ t('ap.urgent') }}</option></select></div>
          <div class="field"><label>{{ t('ap.guarantee') }}</label><select v-model="form.guaranteeType"><option value="PUBLIC_RENTAL">{{ t('ap.publicRental') }}</option><option value="LOW_RENT">{{ t('ap.lowRent') }}</option><option value="SUBSIDY">{{ t('ap.subsidyRental') }}</option></select></div>
          <div class="field"><label>{{ t('ap.familyType') }}</label><select v-model="form.familyType"><option value="SINGLE">{{ t('ap.single') }}</option><option value="COUPLE">{{ t('ap.couple') }}</option><option value="WITH_CHILDREN">{{ t('ap.withChildren') }}</option><option value="ELDERLY">{{ t('ap.elderly') }}</option></select></div>
          <div class="field"><label>{{ t('ap.subsidy') }}</label><select v-model="form.subsidyStatus"><option value="NONE">{{ t('ap.none') }}</option><option value="APPLYING">{{ t('ap.applying') }}</option><option value="ACTIVE">{{ t('ap.active') }}</option></select></div>
          <div class="field"><label>{{ t('ap.archive') }}</label><input v-model="form.archiveNo" /></div>
          <div class="field" style="flex:2"><label>{{ t('ap.remark') }}</label><input v-model="form.remark" /></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="create">{{ t('ap.create') }}</button></div>
      </div>
    </div>

    <div v-if="allocateOpen" class="modal-mask" @click.self="allocateOpen = false">
      <div class="modal" style="max-width:620px">
        <div class="panel-head"><h2>{{ t('ap.allocate') }}</h2><button class="sm" @click="allocateOpen = false">{{ t('ap.close') }}</button></div>
        <div class="row">
          <div class="field"><label>{{ t('ap.waitRecord') }}</label><SearchSelect v-model="allocateForm.waitlistId" :options="waitlist.filter(x => x.waitlistStatus === 'WAITING')" label-key="queueNo" sublabel-key="applicantName" value-key="id" :placeholder="t('ap.waitRecord')" /></div>
          <div class="field"><label>{{ t('ap.house') }}</label><SearchSelect v-model="allocateForm.houseId" :options="houses.filter(x => x.houseStatus === 'VACANT')" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('ap.house')" /></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="allocate(); allocateOpen = false">{{ t('ap.confirmAllocate') }}</button></div>
      </div>
    </div>
  </div>
</template>
