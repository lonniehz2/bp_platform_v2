<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can, canAction } from '../permissions'
import SearchSelect from '../components/SearchSelect.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import DataTable from '../components/DataTable.vue'
import { confirmAction } from '../confirm'
import { contractStatusLabel, contractStatusTone } from '../contractStatus'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const contracts = ref([])
const persons = ref([])
const houses = ref([])
const error = ref('')
const busy = ref(false)
const detailOpen = ref(false)
const createOpen = ref(false)
const billOpen = ref(false)
const router = useRouter()
const page = ref(1)
const contractQuery = ref('')
const form = reactive({
  contractNo: '', houseId: '', personId: '', startDate: '2026-11-01', endDate: '2027-10-31',
  rentAmount: 1200, depositAmount: 1200, billingCycle: 'MONTH', billDay: 1, draft: false
})
const billForm = reactive({ contractId: '', periodStart: '2026-11-01', periodEnd: '2026-11-30', amount: 1200 })
const selectedContract = ref(null)
const files = ref([])
const cohabitants = ref([])
const cohabForm = reactive({ personId: '', relationType: 'FAMILY', startDate: '', endDate: '', remark: '' })
const fileBusy = ref(false)
const payOpen = ref(false)
const payContractRow = ref(null)
const payBills = ref([])
const payMethod = ref('CASH')
const payBusy = ref(false)
const payTotal = computed(() => payBills.value.filter(b => b.checked).reduce((s, b) => s + Number(b.amount || 0), 0))

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const filteredContracts = computed(() => {
  const q = contractQuery.value.trim().toLowerCase()
  if (!q) return contracts.value
  return contracts.value.filter(c => (String(c.contractNo) + ' ' + String(c.personName || '') + ' ' + String(c.houseName || '')).toLowerCase().includes(q))
})
const pagedContracts = computed(() => filteredContracts.value.slice((page.value - 1) * 10, page.value * 10))
const contractColumns = [
  { key: 'contractNo', title: t('ct.contractNo'), width: '170px' },
  { key: 'houseName', title: t('ct.house'), width: '150px' },
  { key: 'personName', title: t('ct.tenant'), width: '110px' },
  { key: 'rentAmount', title: t('ct.rent'), width: '90px' },
  { key: 'depositAmount', title: t('ct.deposit'), width: '90px' },
  { key: 'billingCycle', title: t('ct.cycle'), width: '80px' },
  { key: 'billDay', title: t('ct.billDay'), width: '70px' },
  { key: 'contractStatus', title: t('ct.status'), width: '90px' },
  { key: 'actions', title: t('ct.action'), width: '360px' }
]

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
    const [c, p, h] = await Promise.all([
      api.contracts(project.value.id), api.persons(), api.houses(project.value.id)
    ])
    contracts.value = c; persons.value = p; houses.value = h
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
    if (!billForm.contractId && c.length) billForm.contractId = c[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.contractNo.trim()) throw new Error(t('ct.requiredNo'))
    if (!form.houseId || !form.personId) throw new Error(t('ct.requiredHousePerson'))
    if (!form.startDate || !form.endDate) throw new Error(t('ct.requiredDates'))
    if (new Date(form.endDate) <= new Date(form.startDate)) throw new Error(t('ct.requiredEndAfterStart'))
    if (Number(form.rentAmount) < 0 || Number(form.depositAmount) < 0) throw new Error(t('ct.negativeAmount'))
    if (Number(form.billDay) < 1 || Number(form.billDay) > 28) throw new Error(t('ct.billDayRange'))
    await api.createContract({
      projectId: project.value.id, contractNo: form.contractNo.trim(),
      houseId: form.houseId, personId: form.personId,
      startDate: form.startDate, endDate: form.endDate,
      rentAmount: Number(form.rentAmount), depositAmount: Number(form.depositAmount),
      billingCycle: form.billingCycle, billDay: Number(form.billDay || 1), draft: form.draft
    })
    form.contractNo = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function contractAction(c, action) {
  if (action === 'discard' || action === 'withdraw') {
    const ok = await confirmAction({ title: t(action === 'discard' ? 'ct.discardTitle' : 'ct.withdrawTitle'), message: t('ct.confirmAction', { action: t(action === 'discard' ? 'ct.discard' : 'ct.withdraw'), no: c.contractNo }), confirmText: t(action === 'discard' ? 'ct.discard' : 'ct.withdraw'), danger: action === 'discard' })
    if (!ok) return
  }
  error.value = ''
  busy.value = true
  try {
    if (action === 'submit') await api.submitContract(c.id)
    if (action === 'approve') await api.approveContract(c.id)
    if (action === 'withdraw') await api.withdrawContract(c.id)
    if (action === 'discard') await api.discardContract(c.id)
    if (action === 'activate') {
      const reason = window.prompt(t('ct.promptTitle'), t('ct.promptDefault'))
      if (reason === null) return
      await api.activateContract(c.id, reason)
    }
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function openDetail(c) {
  router.push(`/guarantee/contracts/${c.id}`)
}

async function openFiles(c) {
  selectedContract.value = c
  files.value = await api.files('CONTRACT', c.id)
  cohabitants.value = await api.cohabitants(c.id)
  if (!cohabForm.personId && persons.value.length) cohabForm.personId = persons.value[0].id
}

async function uploadFile(e) {
  const file = e.target.files?.[0]
  if (!file || !selectedContract.value) return
  fileBusy.value = true; error.value = ''
  try {
    await api.uploadFile('CONTRACT', selectedContract.value.id, file)
    files.value = await api.files('CONTRACT', selectedContract.value.id)
    e.target.value = ''
  } catch (err) { error.value = err.message } finally { fileBusy.value = false }
}

async function addCohabitant() {
  if (!selectedContract.value || !cohabForm.personId) { error.value = t('ct.requiredPerson'); return }
  busy.value = true; error.value = ''
  try {
    await api.addCohabitant(selectedContract.value.id, {
      personId: cohabForm.personId, relationType: cohabForm.relationType,
      startDate: cohabForm.startDate || null, endDate: cohabForm.endDate || null, remark: cohabForm.remark
    })
    cohabitants.value = await api.cohabitants(selectedContract.value.id)
    cohabForm.remark = ''
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function removeCohabitant(c) {
  busy.value = true; error.value = ''
  try { await api.removeCohabitant(c.id); cohabitants.value = await api.cohabitants(selectedContract.value.id) } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function openPayment(c) {
  error.value = ''
  try {
    const rows = await api.contractBills(c.id)
    payBills.value = rows.filter(b => b.billStatus !== 'PAID').map(b => ({
      ...b,
      checked: false,
      amount: Number(b.payableAmount || 0) - Number(b.paidAmount || 0)
    }))
    if (!payBills.value.length) { error.value = t('ct.noUnpaid'); return }
    payContractRow.value = c
    payMethod.value = 'CASH'
    payOpen.value = true
  } catch (e) { error.value = e.message }
}

function togglePayBill(b) {
  if (b.checked && (!b.amount || b.amount <= 0)) {
    b.amount = Number(b.payableAmount || 0) - Number(b.paidAmount || 0)
  }
}

async function submitPayment() {
  payBusy.value = true; error.value = ''
  try {
    const allocations = payBills.value.filter(b => b.checked).map(b => ({ billId: b.id, amount: Number(b.amount || 0) }))
    if (!allocations.length) throw new Error(t('ct.requiredAllocations'))
    if (allocations.some(a => a.amount <= 0)) throw new Error(t('ct.positiveAmount'))
    const r = await api.payContract(payContractRow.value.id, { paymentMethod: payMethod.value, allocations })
    payOpen.value = false
    await load()
    alert(t('ct.paySuccess', { no: r.paymentNo, amount: money(r.totalAmount), receipt: r.receiptNo }))
  } catch (e) { error.value = e.message } finally { payBusy.value = false }
}

async function downloadFile(f) {
  try { await api.downloadFile(f.id, f.fileName) } catch (e) { error.value = e.message }
}

async function generateBill() {
  busy.value = true; error.value = ''
  try {
    if (!billForm.contractId) throw new Error(t('ct.requiredContract'))
    await api.generateBill(billForm.contractId, {
      periodStart: billForm.periodStart, periodEnd: billForm.periodEnd,
      amount: Number(billForm.amount)
    })
    error.value = ''
    alert(t('ct.created'))
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">{{ t('ct.createProject') }}</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ t('ct.title') }}</h2><p>{{ project.orgName }} · {{ t('ct.subtitle') }}</p></div>
          <div class="row"><button v-if="canAction('contract:create', 'contract')" class="primary" @click="createOpen = true">{{ t('ct.createTitle') }}</button><button class="sm" @click="billOpen = true">{{ t('ct.billTitle') }}</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('ct.list') }}</h2><span class="small muted">{{ t('ct.listHint') }}</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="contractQuery" :placeholder="t('ct.search')" style="max-width:300px" @input="page = 1" />
        </div>
        <DataTable :rows="pagedContracts" :columns="contractColumns" :page="page" :page-size="10" :total="filteredContracts.length" :empty-text="t('ct.empty')" @update:page="page = $event">
          <template #cell-rentAmount="{ row }">¥{{ money(row.rentAmount) }}</template>
          <template #cell-depositAmount="{ row }">¥{{ money(row.depositAmount) }}</template>
          <template #cell-contractStatus="{ row }"><span class="badge" :class="contractStatusTone(row.contractStatus)">{{ contractStatusLabel(row.contractStatus) }}</span></template>
          <template #cell-actions="{ row }">
            <div class="row">
              <button class="sm" @click="openDetail(row)">{{ t('ct.detail') }}</button>
              <button v-if="canAction('contract:submit', 'contract') && row.contractStatus === 'DRAFT'" class="sm" :disabled="busy" @click="contractAction(row, 'submit')">{{ t('ct.submit') }}</button>
              <button v-if="canAction('contract:activate', 'contract') && row.contractStatus === 'DRAFT'" class="sm" :disabled="busy" @click="contractAction(row, 'activate')">{{ t('ct.activate') }}</button>
              <button v-if="canAction('contract:discard', 'contract') && row.contractStatus === 'DRAFT'" class="sm danger" :disabled="busy" @click="contractAction(row, 'discard')">{{ t('ct.discard') }}</button>
              <button v-if="canAction('contract:approve', 'contract') && row.contractStatus === 'APPROVING'" class="sm primary" :disabled="busy" @click="contractAction(row, 'approve')">{{ t('ct.approve') }}</button>
              <button v-if="canAction('contract:withdraw', 'contract') && row.contractStatus === 'APPROVING'" class="sm" :disabled="busy" @click="contractAction(row, 'withdraw')">{{ t('ct.withdraw') }}</button>
              <button v-if="canAction('billing:pay', 'billing') && row.contractStatus === 'ACTIVE'" class="sm primary" @click="openPayment(row)">{{ t('ct.pay') }}</button>
            </div>
          </template>
        </DataTable>
      </div>

      <div v-if="detailOpen" class="modal-mask" @click.self="detailOpen = false">
        <div class="modal" style="max-width:900px">
          <div class="panel-head"><h2>{{ t('ct.detailTitle') }}</h2><button class="sm" @click="detailOpen = false">{{ t('ct.close') }}</button></div>
      <EntityDetailTabs v-if="selectedContract" type="CONTRACT" :entity-id="selectedContract.id" />
      <div v-if="detailOpen && selectedContract" class="panel">
        <div class="panel-head"><h2>{{ t('ct.attachments') }}</h2><span class="small muted">{{ selectedContract.contractNo }}</span></div>
        <div class="row" style="margin-bottom:10px">
          <input type="file" @change="uploadFile" :disabled="fileBusy" style="max-width:320px" />
        </div>
        <div v-if="!files.length" class="empty">{{ t('ct.noFiles') }}</div>
        <div v-for="f in files" :key="f.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ f.fileName }}</div><div class="small muted">{{ f.fileSize }} bytes · {{ f.createTime }}</div></div>
          <button class="sm" @click="downloadFile(f)">{{ t('ct.download') }}</button>
        </div>
      </div>

      <div v-if="detailOpen && selectedContract" class="panel">
        <div class="panel-head"><h2>{{ t('ct.cohabitants') }}</h2><span class="small muted">{{ selectedContract.contractNo }} · {{ cohabitants.length }} {{ t('ct.people') }}</span></div>
        <div class="row" style="margin-bottom:10px">
          <div class="field" style="flex:2"><label>{{ t('ct.person') }}</label><SearchSelect v-model="cohabForm.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('ct.searchPerson')" /></div>
          <div class="field"><label>{{ t('ct.relation') }}</label><select v-model="cohabForm.relationType"><option value="SPOUSE">{{ t('ct.spouse') }}</option><option value="CHILD">{{ t('ct.child') }}</option><option value="PARENT">{{ t('ct.parent') }}</option><option value="FAMILY">{{ t('ct.family') }}</option><option value="OTHER">{{ t('ct.other') }}</option></select></div>
          <div class="field"><label>{{ t('ct.start') }}</label><input v-model="cohabForm.startDate" type="date" /></div>
          <div class="field"><label>{{ t('ct.end') }}</label><input v-model="cohabForm.endDate" type="date" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addCohabitant">{{ t('ct.addCohabitant') }}</button></div>
        </div>
        <div v-if="!cohabitants.length" class="empty">{{ t('ct.noCohabitants') }}</div>
        <div v-for="c in cohabitants" :key="c.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ c.personName }} · {{ c.relationType }}</div><div class="small muted">{{ c.startDate || '' }} ~ {{ c.endDate || t('ct.longTerm') }}</div></div>
          <span class="badge green">{{ c.cohabitantStatus }}</span>
          <button class="sm danger" :disabled="busy" @click="removeCohabitant(c)">{{ t('ct.remove') }}</button>
        </div>
      </div>

        </div>
      </div>

      <div v-if="createOpen" class="modal-mask" @click.self="createOpen = false">
        <div class="modal" style="max-width:860px">
          <div class="panel-head"><h2>{{ t('ct.createTitle') }}</h2><button class="sm" @click="createOpen = false">{{ t('ct.close') }}</button></div>
          <div class="row">
            <div class="field"><label>{{ t('ct.contractNo') }}</label><input v-model="form.contractNo" :placeholder="t('ct.placeholderNo')" /></div>
            <div class="field"><label>{{ t('ct.house') }}</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" :placeholder="t('ct.searchHouse')" /></div>
            <div class="field"><label>{{ t('ct.tenant') }}</label><SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('ct.searchTenant')" /></div>
            <div class="field"><label>{{ t('ct.startDate') }}</label><input v-model="form.startDate" type="date" /></div>
            <div class="field"><label>{{ t('ct.endDate') }}</label><input v-model="form.endDate" type="date" /></div>
            <div class="field"><label>{{ t('ct.rent') }}</label><input v-model.number="form.rentAmount" type="number" /></div>
            <div class="field"><label>{{ t('ct.deposit') }}</label><input v-model.number="form.depositAmount" type="number" /></div>
            <div class="field"><label>{{ t('ct.cycle') }}</label><select v-model="form.billingCycle"><option value="MONTH">{{ t('ct.monthly') }}</option><option value="QUARTER">{{ t('ct.quarterly') }}</option><option value="YEAR">{{ t('ct.yearly') }}</option></select></div>
            <div class="field"><label>{{ t('ct.billDay') }}</label><input v-model.number="form.billDay" type="number" min="1" max="28" /></div>
            <div class="field" style="flex:0 0 auto"><label><input type="checkbox" v-model="form.draft" /> {{ t('ct.draft') }}</label></div>
          </div>
          <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="create">{{ t('ct.create') }}</button></div>
        </div>
      </div>

      <div v-if="billOpen" class="modal-mask" @click.self="billOpen = false">
        <div class="modal" style="max-width:640px">
          <div class="panel-head"><h2>{{ t('ct.billTitle') }}</h2><button class="sm" @click="billOpen = false">{{ t('ct.close') }}</button></div>
          <div class="row">
            <div class="field"><label>{{ t('ct.contract') }}</label><SearchSelect v-model="billForm.contractId" :options="contracts" label-key="contractNo" sublabel-key="personName" value-key="id" :placeholder="t('ct.searchContract')" /></div>
            <div class="field"><label>{{ t('ct.periodStart') }}</label><input v-model="billForm.periodStart" type="date" /></div>
            <div class="field"><label>{{ t('ct.periodEnd') }}</label><input v-model="billForm.periodEnd" type="date" /></div>
            <div class="field"><label>{{ t('ct.amount') }}</label><input v-model.number="billForm.amount" type="number" /></div>
          </div>
          <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="generateBill(); billOpen = false">{{ t('ct.generate') }}</button></div>
        </div>
      </div>

      <div v-if="payOpen" class="modal-mask" @click.self="payOpen = false">
        <div class="modal" style="max-width:760px">
          <div class="panel-head"><h2>{{ t('ct.payTitle') }}</h2><button class="sm" @click="payOpen = false">{{ t('ct.close') }}</button></div>
          <div class="small muted" style="margin-bottom:8px">{{ payContractRow?.contractNo }} · {{ t('ct.payHint') }}</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>{{ t('ct.choose') }}</th><th>{{ t('ct.billNo') }}</th><th>{{ t('ct.period') }}</th><th>{{ t('ct.payable') }}</th><th>{{ t('ct.paid') }}</th><th>{{ t('ct.outstanding') }}</th><th>{{ t('ct.thisPay') }}</th></tr></thead>
              <tbody>
                <tr v-for="b in payBills" :key="b.id">
                  <td><input type="checkbox" v-model="b.checked" @change="togglePayBill(b)" /></td>
                  <td class="mono">{{ b.billNo }}</td>
                  <td>{{ b.periodStart }} ~ {{ b.periodEnd }}</td>
                  <td>¥{{ money(b.payableAmount) }}</td>
                  <td>¥{{ money(b.paidAmount) }}</td>
                  <td>¥{{ money(Number(b.payableAmount || 0) - Number(b.paidAmount || 0)) }}</td>
                  <td><input v-model.number="b.amount" type="number" :disabled="!b.checked" style="width:110px" /></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="row" style="justify-content:space-between;margin-top:10px">
            <div class="field" style="max-width:180px"><label>{{ t('ct.method') }}</label><select v-model="payMethod"><option value="CASH">{{ t('ct.cash') }}</option><option value="WECHAT">{{ t('ct.wechat') }}</option><option value="ALIPAY">{{ t('ct.alipay') }}</option><option value="BANK">{{ t('ct.bankTransfer') }}</option></select></div>
            <strong>{{ t('ct.total') }}: ¥{{ money(payTotal) }}</strong>
          </div>
          <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="payBusy" @click="submitPayment">{{ t('ct.confirmPay') }}</button></div>
        </div>
      </div>
    </template>
  </div>
</template>
