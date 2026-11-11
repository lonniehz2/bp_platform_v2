<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'
import { confirmAction } from '../confirm'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const contracts = ref([])
const contractId = ref('')
const subsidies = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ amount: 300, startDate: '2026-11-01', endDate: '2027-10-31', remark: t('subsidies.defaultValue') })
const editing = ref(null)
const editForm = reactive({ subsidyType: 'RENT_SUBSIDY', amount: 0, startDate: '', endDate: '', remark: '' })
const selected = computed(() => contracts.value.find(c => String(c.id) === String(contractId.value)) || null)
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
    contracts.value = await api.contracts(project.value.id)
    if (!contractId.value && contracts.value.length) contractId.value = contracts.value[0].id
    await loadSubsidies()
  } catch (e) { error.value = e.message }
}

async function loadSubsidies() {
  if (!contractId.value) { subsidies.value = []; return }
  try { subsidies.value = await api.subsidies(contractId.value) } catch { subsidies.value = [] }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!contractId.value) throw new Error(t('subsidies.required'))
    await api.createSubsidy(contractId.value, {
      amount: Number(form.amount || 0), startDate: form.startDate, endDate: form.endDate, remark: form.remark
    })
    await loadSubsidies()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


function openEdit(s) {
  editing.value = s
  Object.assign(editForm, { subsidyType: s.subsidyType || 'RENT_SUBSIDY', amount: s.subsidyAmount || 0, startDate: s.startDate || '', endDate: s.endDate || '', remark: s.remark || '' })
}

async function saveEdit() {
  busy.value = true; error.value = ''
  try {
    await api.updateSubsidy(editing.value.id, { subsidyType: editForm.subsidyType, amount: Number(editForm.amount || 0), startDate: editForm.startDate, endDate: editForm.endDate, remark: editForm.remark })
    editing.value = null
    await loadSubsidies()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function terminate(s) {
  if (!await confirmAction({ title: t('subsidies.terminateTitle'), message: t('subsidies.terminateMessage'), confirmText: t('subsidies.terminateConfirm'), danger: true })) return
  busy.value = true; error.value = ''
  try { await api.terminateSubsidy(s.id); await loadSubsidies() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('subsidies.title') }}</h2><p>{{ project?.orgName || t('subsidies.noProject') }} · {{ t('subsidies.subtitle') }}</p></div><span class="badge blue">{{ subsidies.length }} {{ t('subsidies.count') }}</span></div>
      <div class="row">
        <div class="field" style="flex:2"><label>{{ t('subsidies.contract') }}</label><SearchSelect v-model="contractId" :options="contracts" label-key="contractNo" sublabel-key="personName" value-key="id" :placeholder="t('subsidies.searchContract')" @change="loadSubsidies" /></div>
        <div class="field"><label>{{ t('subsidies.amount') }}</label><input v-model.number="form.amount" type="number" /></div>
        <div class="field"><label>{{ t('subsidies.start') }}</label><input v-model="form.startDate" type="date" /></div>
        <div class="field"><label>{{ t('subsidies.end') }}</label><input v-model="form.endDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('billing')" class="primary" :disabled="busy" @click="create">{{ t('subsidies.add') }}</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('subsidies.records') }}</h2><span class="small muted">{{ selected?.contractNo || t('subsidies.noContract') }}</span></div>
      <div v-if="!subsidies.length" class="empty">{{ t('subsidies.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('subsidies.type') }}</th><th>{{ t('subsidies.amountPerMonth') }}</th><th>{{ t('subsidies.start') }}</th><th>{{ t('subsidies.end') }}</th><th>{{ t('subsidies.status') }}</th><th>{{ t('subsidies.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="s in subsidies" :key="s.id">
              <td>{{ s.subsidyType || 'RENT_SUBSIDY' }}</td><td>¥{{ money(s.amount) }}</td><td>{{ s.startDate }}</td><td>{{ s.endDate }}</td>
              <td><span class="badge" :class="s.subsidyStatus === 'ACTIVE' ? 'green' : 'orange'">{{ s.subsidyStatus }}</span></td>
              <td>
                <button v-if="can('billing') && s.subsidyStatus === 'ACTIVE'" class="sm" @click="openEdit(s)">{{ t('subsidies.edit') }}</button>
                <button v-if="can('billing') && s.subsidyStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="terminate(s)">{{ t('subsidies.terminate') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="editing" class="modal-mask" @click.self="editing = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('subsidies.editTitle') }}</h2><button class="sm" @click="editing = null">{{ t('subsidies.close') }}</button></div>
        <div class="field"><label>{{ t('subsidies.subsidyType') }}</label><select v-model="editForm.subsidyType"><option value="RENT_SUBSIDY">{{ t('subsidies.rentSubsidy') }}</option><option value="OTHER">{{ t('subsidies.other') }}</option></select></div>
        <div class="field"><label>{{ t('subsidies.amount') }}</label><input v-model.number="editForm.amount" type="number" /></div>
        <div class="field"><label>{{ t('subsidies.start') }}</label><input v-model="editForm.startDate" type="date" /></div>
        <div class="field"><label>{{ t('subsidies.end') }}</label><input v-model="editForm.endDate" type="date" /></div>
        <div class="field"><label>{{ t('subsidies.remark') }}</label><input v-model="editForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="saveEdit">{{ t('subsidies.save') }}</button></div>
      </div>
    </div>
  </div>
</template>
