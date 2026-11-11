<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { contractStatusLabel, contractStatusTone } from '../contractStatus'
import { relationLabel, relationStatusLabel } from '../relationLabels'
import { api } from '../api'
import { sceneRoot } from '../scene'
import { can } from '../permissions'
import DataTable from '../components/DataTable.vue'
import SearchSelect from '../components/SearchSelect.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { confirmAction } from '../confirm'
import { PERSON_TYPES } from '../personTypes'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const persons = ref([])
const grants = ref([])
const relations = ref([])
const projects = ref([])
const houses = ref([])
const project = ref(null)
const selected = ref(null)
const contractRelations = ref(null)
const error = ref('')
const busy = ref(false)
const page = ref(1)
const route = useRoute()
const router = useRouter()
const personQuery = ref('')
const relForm = reactive({ targetType: 'HOUSE', targetId: '', relationType: 'TENANT', startDate: '', endDate: '' })
const form = reactive({ personCode: '', personName: '', phone: '', idCardMask: '', personType: PERSON_TYPES.GT, gender: '', birthDate: '', address: '', employer: '', emergencyContact: '', remark: '' })
const filteredPersons = computed(() => {
  const q = personQuery.value.trim().toLowerCase()
  if (!q) return persons.value
  return persons.value.filter(p => (String(p.personCode) + ' ' + String(p.personName || '') + ' ' + String(p.phone || '')).toLowerCase().includes(q))
})
const paged = computed(() => filteredPersons.value.slice((page.value - 1) * 10, page.value * 10))
const editingPerson = ref(null)
const personEditForm = reactive({ personCode: '', personName: '', phone: '', idCardMask: '', personType: PERSON_TYPES.GT, gender: '', birthDate: '', address: '', employer: '', emergencyContact: '', remark: '' })
const personColumns = [
  { key: 'personCode', title: t('pp.code'), width: '140px' },
  { key: 'personName', title: t('pp.name'), width: '110px' },
  { key: 'phone', title: t('pp.phone'), width: '130px' },
  { key: 'gender', title: t('pp.gender'), width: '70px' },
  { key: 'personType', title: t('pp.type'), width: '120px' },
  { key: 'status', title: t('pp.status'), width: '80px' },
  { key: 'actions', title: t('pp.action'), width: '200px' }
]

async function load() {
  error.value = ''
  try {
    const all = await api.projects()
    projects.value = all
    const saved = String(localStorage.getItem('platformProjectId') || '')
    project.value = all.find(p => String(p.id) === saved) || all[0] || null
    persons.value = await api.persons()
    houses.value = project.value ? await api.houses(project.value.id) : []
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.personCode.trim() || !form.personName.trim()) throw new Error(t('pp.required'))
    if (form.phone && !/^1\d{10}$/.test(form.phone)) throw new Error(t('pp.invalidPhone'))
    if (form.birthDate && new Date(form.birthDate) > new Date()) throw new Error(t('pp.birthFuture'))
    await api.createPerson({
      personCode: form.personCode.trim(), personName: form.personName.trim(),
      phone: form.phone, idCardMask: form.idCardMask, personType: form.personType,
      gender: form.gender, birthDate: form.birthDate || null, address: form.address,
      employer: form.employer, emergencyContact: form.emergencyContact, remark: form.remark
    })
    form.personCode = ''; form.personName = ''; form.phone = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function selectPerson(p) {
  selected.value = p
  contractRelations.value = null
  try {
    const [g, r, cr] = await Promise.all([
      api.keyring(p.id),
      api.relations(p.id),
      api.personContractRelations(p.id).catch(() => null)
    ])
    grants.value = g
    relations.value = r
    contractRelations.value = cr
  } catch {
    grants.value = []
    relations.value = []
    contractRelations.value = null
  }
  await nextTick()
  document.getElementById('person-detail')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}


async function removeRelation(r) {
  if (!selected.value) return
  if (!await confirmAction({ title: t('pp.removeRelTitle'), message: t('pp.removeRelMessage', { name: r.targetName || r.relationType }), confirmText: t('pp.removeRelConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.removePersonRelation(selected.value.id, r.id); relations.value = await api.relations(selected.value.id) } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function addRelation() {
  if (!selected.value || !relForm.targetId) { error.value = t('pp.requiredTarget'); return }
  busy.value = true; error.value = ''
  try {
    await api.createRelation(selected.value.id, {
      projectId: project.value?.id, targetType: relForm.targetType, targetId: relForm.targetId,
      relationType: relForm.relationType, startDate: relForm.startDate || null, endDate: relForm.endDate || null
    })
    relations.value = await api.relations(selected.value.id)
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openPersonEdit(p) {
  editingPerson.value = p
  Object.assign(personEditForm, {
    personCode: p.personCode || '', personName: p.personName || '', phone: p.phone || '',
    idCardMask: p.idCardMask || '', personType: p.personType || PERSON_TYPES.GT, gender: p.gender || '',
    birthDate: p.birthDate || '', address: p.address || '', employer: p.employer || '',
    emergencyContact: p.emergencyContact || '', remark: p.remark || ''
  })
}


async function archivePerson(p) {
  if (!await confirmAction({ title: t('pp.archiveTitle'), message: t('pp.archiveMessage', { name: p.personName }), confirmText: t('pp.archiveConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.archivePerson(p.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function savePersonEdit() {
  busy.value = true; error.value = ''
  try {
    if (!personEditForm.personName.trim()) throw new Error(t('pp.noName'))
    await api.updatePerson(editingPerson.value.id, { ...personEditForm })
    editingPerson.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function togglePersonStatus(p) {
  const next = p.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  if (!await confirmAction({ title: t('pp.statusTitle'), message: t('pp.statusMessage', { name: p.personName, status: next }), confirmText: t('pp.confirm') })) return
  busy.value = true; error.value = ''
  try { await api.updatePersonStatus(p.id, next); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(async () => {
  await load()
  const id = String(route.query.id || '')
  const found = persons.value.find(p => String(p.id) === id)
  if (found) selectPerson(found)
})
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="route.query.from === 'contract' && route.query.contractId" class="alert">
      {{ t('pp.fromContract', { id: route.query.contractId }) }}
      <button class="sm" @click="router.push(`${sceneRoot()}/contracts/${route.query.contractId}?tab=persons`)">{{ t('pp.backContract') }}</button>
    </div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('pp.title') }}</h2><p>{{ t('pp.subtitle') }}</p></div><div class="row"><span class="badge blue">{{ persons.length }} {{ t('pp.count') }}</span><RouterLink class="sm" :to="sceneRoot() + '/imports'">{{ t('pp.import') }}</RouterLink></div></div>
      <div class="row">
        <div class="field"><label>{{ t('pp.code') }}</label><input v-model="form.personCode" :placeholder="t('pp.code')" /></div>
        <div class="field"><label>{{ t('pp.name') }}</label><input v-model="form.personName" /></div>
        <div class="field"><label>{{ t('pp.phone') }}</label><input v-model="form.phone" /></div>
        <div class="field"><label>{{ t('pp.idMask') }}</label><input v-model="form.idCardMask" :placeholder="t('pp.idMask')" /></div>
        <div class="field"><label>{{ t('pp.gender') }}</label><select v-model="form.gender"><option value="">{{ t('pp.unset') }}</option><option value="MALE">{{ t('pp.male') }}</option><option value="FEMALE">{{ t('pp.female') }}</option></select></div>
        <div class="field"><label>{{ t('pp.birth') }}</label><input v-model="form.birthDate" type="date" /></div>
        <div class="field"><label>{{ t('pp.type') }}</label>
          <select v-model="form.personType">
            <option :value="PERSON_TYPES.GT">{{ t('pp.guarantee') }}</option>
            <option value="FAMILY">{{ t('pp.family') }}</option>
            <option value="TENANT">{{ t('pp.tenant') }}</option>
            <option value="COHABITANT">{{ t('pp.cohabitant') }}</option>
            <option value="VISITOR">{{ t('pp.visitor') }}</option>
            <option value="STAFF">{{ t('pp.staff') }}</option>
          </select>
        </div>
        <div class="field" style="flex:2"><label>{{ t('pp.address') }}</label><input v-model="form.address" /></div>
        <div class="field"><label>{{ t('pp.employer') }}</label><input v-model="form.employer" /></div>
        <div class="field"><label>{{ t('pp.emergency') }}</label><input v-model="form.emergencyContact" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('person')" class="primary" :disabled="busy" @click="create">{{ t('pp.add') }}</button></div>
      </div>
    </div>

    <div class="grid" style="grid-template-columns: 1.3fr .7fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('pp.list') }}</h2><span class="small muted">{{ t('pp.listHint') }}</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="personQuery" :placeholder="t('pp.search')" style="max-width:280px" @input="page = 1" />
        </div>
        <div v-if="selected" class="alert">{{ t('pp.current')+'：' }}<strong>{{ selected.personName }}</strong>（{{ selected.personCode }}）<span v-if="contractRelations" class="small muted"> · {{ t('pp.tenantContracts') }} {{ contractRelations.tenantContracts?.length || 0 }} · {{ t('pp.cohabContracts') }} {{ contractRelations.cohabitantContracts?.length || 0 }}</span></div>
        <DataTable :rows="paged" :columns="personColumns" :page="page" :page-size="10" :total="filteredPersons.length" :empty-text="t('pp.empty')" @update:page="page = $event" @row-click="selectPerson">
          <template #cell-gender="{ row }">{{ row.gender === 'MALE' ? t('pp.male') : row.gender === 'FEMALE' ? t('pp.female') : '-' }}</template>
          <template #cell-status="{ row }"><span class="badge" :class="row.status === 'ENABLED' ? 'green' : 'orange'">{{ row.status }}</span></template>
          <template #cell-actions="{ row }">
            <button class="sm" @click.stop="openPersonEdit(row)">{{ t('pp.edit') }}</button>
            <button class="sm" :class="row.status === 'ENABLED' ? 'danger' : ''" :disabled="busy" @click.stop="togglePersonStatus(row)">{{ row.status === 'ENABLED' ? t('pp.disable') : t('pp.enable') }}</button>
            <button class="sm danger" :disabled="busy" @click.stop="archivePerson(row)">{{ t('pp.archive') }}</button>
          </template>
        </DataTable>
      </div>

      <div v-if="selected" id="person-detail" class="row" style="justify-content:flex-end;margin-bottom:8px"><RouterLink class="sm" :to="`${sceneRoot()}/detail/PERSON/${selected.id}`">{{ t('pp.openDetail') }}</RouterLink></div>
      <EntityDetailTabs v-if="selected" type="PERSON" :entity-id="selected.id" />

      <div class="panel">
        <div class="panel-head"><h2>{{ t('pp.keyring') }}</h2><span class="small muted">{{ selected?.personName || t('pp.noSelected') }}</span></div>
        <div v-if="!selected" class="empty">{{ t('pp.selectPerson') }}</div>
        <div v-else-if="!grants.length" class="empty">{{ t('pp.noGrants') }}</div>
        <div v-for="g in grants" :key="g.id" class="row" style="padding:9px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1">
            <div>{{ g.targetName || g.targetType }}</div>
            <div class="small muted">{{ g.targetType }} · {{ g.validStart }} ~ {{ g.validEnd || t('pp.longTerm') }}</div>
          </div>
          <span class="badge blue">{{ g.grantLevel }}</span>
        </div>
      </div>
    </div>

    <div v-if="editingPerson" class="modal-mask" @click.self="editingPerson = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('pp.editTitle') }}</h2><button class="sm" @click="editingPerson = null">{{ t('pp.close') }}</button></div>
        <div class="field"><label>{{ t('pp.code') }}</label><input v-model="personEditForm.personCode" disabled /></div>
        <div class="field"><label>{{ t('pp.name') }}</label><input v-model="personEditForm.personName" /></div>
        <div class="field"><label>{{ t('pp.phone') }}</label><input v-model="personEditForm.phone" /></div>
        <div class="field"><label>{{ t('pp.type') }}</label><select v-model="personEditForm.personType"><option :value="PERSON_TYPES.GT">{{ t('pp.guarantee') }}</option><option value="APPLICANT">{{ t('pp.applicant') }}</option><option value="COHABITANT">{{ t('pp.cohabitant') }}</option><option value="STAFF">{{ t('pp.staffAlt') }}</option></select></div>
        <div class="field"><label>{{ t('pp.gender') }}</label><select v-model="personEditForm.gender"><option value="">{{ t('pp.unknown') }}</option><option value="MALE">{{ t('pp.male') }}</option><option value="FEMALE">{{ t('pp.female') }}</option></select></div>
        <div class="field"><label>{{ t('pp.address') }}</label><input v-model="personEditForm.address" /></div>
        <div class="field"><label>{{ t('pp.employer') }}</label><input v-model="personEditForm.employer" /></div>
        <div class="field"><label>{{ t('pp.remark') }}</label><input v-model="personEditForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="savePersonEdit">{{ t('pp.save') }}</button></div>
      </div>
    </div>

    <div v-if="selected" class="panel">
      <div class="panel-head"><div><h2>{{ t('pp.relations') }}</h2><p>{{ selected.personName }} · {{ t('pp.relationHint') }}</p></div><span class="small muted">{{ relations.length }} {{ t('pp.countUnit') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('pp.targetType') }}</label><select v-model="relForm.targetType" @change="relForm.targetId = ''"><option value="HOUSE">{{ t('pp.house') }}</option><option value="PROJECT">{{ t('pp.project') }}</option></select></div>
        <div class="field" style="flex:2"><label>{{ t('pp.target') }}</label>
          <SearchSelect v-if="relForm.targetType === 'HOUSE'" v-model="relForm.targetId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('pp.searchHouse')" />
          <SearchSelect v-else v-model="relForm.targetId" :options="projects" label-key="orgName" sublabel-key="orgCode" value-key="id" :placeholder="t('pp.searchProject')" />
        </div>
        <div class="field"><label>{{ t('pp.relation') }}</label><select v-model="relForm.relationType"><option value="TENANT">{{ t('pp.tenant') }}</option><option value="FAMILY">{{ t('pp.family') }}</option><option value="COHABITANT">{{ t('pp.cohabitant') }}</option><option value="OWNER">{{ t('pp.owner') }}</option></select></div>
        <div class="field"><label>{{ t('pp.start') }}</label><input v-model="relForm.startDate" type="date" /></div>
        <div class="field"><label>{{ t('pp.end') }}</label><input v-model="relForm.endDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addRelation">{{ t('pp.addRelation') }}</button></div>
      </div>
      <div v-if="!relations.length" class="empty">{{ t('pp.noRelations') }}</div>
      <div v-for="r in relations" :key="r.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
        <div style="flex:1"><div>{{ r.targetName }} · {{ relationLabel(r.relationType) }}</div><div class="small muted">{{ r.startDate || '' }} ~ {{ r.endDate || t('pp.longTerm') }}</div></div>
        <span class="badge green">{{ relationStatusLabel(r.status) }}</span>
        <button class="sm danger" :disabled="busy" @click="removeRelation(r)">{{ t('pp.remove') }}</button>
      </div>
    </div>
  </div>
</template>
