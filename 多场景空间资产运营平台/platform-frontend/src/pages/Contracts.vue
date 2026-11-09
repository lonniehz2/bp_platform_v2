<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can, canAction } from '../permissions'
import SearchSelect from '../components/SearchSelect.vue'
import DataTable from '../components/DataTable.vue'
import { confirmAction } from '../confirm'

const project = ref(null)
const contracts = ref([])
const persons = ref([])
const houses = ref([])
const error = ref('')
const busy = ref(false)
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
  { key: 'contractNo', title: '合同编号', width: '170px' },
  { key: 'houseName', title: '房屋', width: '150px' },
  { key: 'personName', title: '承租人', width: '110px' },
  { key: 'rentAmount', title: '租金', width: '90px' },
  { key: 'depositAmount', title: '押金', width: '90px' },
  { key: 'billingCycle', title: '周期', width: '80px' },
  { key: 'billDay', title: '账单日', width: '70px' },
  { key: 'contractStatus', title: '状态', width: '90px' },
  { key: 'actions', title: '操作', width: '360px' }
]

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  if (chosen) return chosen
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
    if (!form.contractNo.trim()) throw new Error('请填写合同编号')
    if (!form.houseId || !form.personId) throw new Error('请选择房屋和承租人')
    if (!form.startDate || !form.endDate) throw new Error('请选择合同起止日期')
    if (new Date(form.endDate) <= new Date(form.startDate)) throw new Error('合同结束日期必须晚于开始日期')
    if (Number(form.rentAmount) < 0 || Number(form.depositAmount) < 0) throw new Error('租金和押金不能为负数')
    if (Number(form.billDay) < 1 || Number(form.billDay) > 28) throw new Error('账单日需在 1-28 之间')
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
    const ok = await confirmAction({ title: action === 'discard' ? '作废合同' : '撤回合同', message: `确认${action === 'discard' ? '作废' : '撤回'}合同 ${c.contractNo}？`, confirmText: action === 'discard' ? '作废' : '撤回', danger: action === 'discard' })
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
      const reason = window.prompt('无模板直接生效说明', '无审批模板，项目负责人确认直接生效')
      if (reason === null) return
      await api.activateContract(c.id, reason)
    }
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
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
  if (!selectedContract.value || !cohabForm.personId) { error.value = '请选择人员'; return }
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
    if (!payBills.value.length) { error.value = '该合同没有未结清账单'; return }
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
    if (!allocations.length) throw new Error('请选择至少一笔账单')
    if (allocations.some(a => a.amount <= 0)) throw new Error('每笔收款金额必须大于 0')
    const r = await api.payContract(payContractRow.value.id, { paymentMethod: payMethod.value, allocations })
    payOpen.value = false
    await load()
    alert(`收款成功：${r.paymentNo}，金额 ¥${money(r.totalAmount)}，收据 ${r.receiptNo}`)
  } catch (e) { error.value = e.message } finally { payBusy.value = false }
}

async function downloadFile(f) {
  try { await api.downloadFile(f.id, f.fileName) } catch (e) { error.value = e.message }
}

async function generateBill() {
  busy.value = true; error.value = ''
  try {
    if (!billForm.contractId) throw new Error('请选择合同')
    await api.generateBill(billForm.contractId, {
      periodStart: billForm.periodStart, periodEnd: billForm.periodEnd,
      amount: Number(billForm.amount)
    })
    error.value = ''
    alert('账单已生成，请到“收费与账务”查看')
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>保障房合同</h2><p>{{ project.orgName }} · 合同创建与账单生成</p></div><span class="pill">CONTRACT</span></div>
        <div class="row">
          <div class="field"><label>合同编号</label><input v-model="form.contractNo" placeholder="如 HT2026001" /></div>
          <div class="field"><label>房屋</label>
            <SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索房屋编码/名称" />
          </div>
          <div class="field"><label>承租人</label>
            <SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" placeholder="搜索承租人" />
          </div>
          <div class="field"><label>开始日期</label><input v-model="form.startDate" type="date" /></div>
          <div class="field"><label>结束日期</label><input v-model="form.endDate" type="date" /></div>
          <div class="field"><label>月租金</label><input v-model.number="form.rentAmount" type="number" /></div>
          <div class="field"><label>押金</label><input v-model.number="form.depositAmount" type="number" /></div>
          <div class="field"><label>账单周期</label><select v-model="form.billingCycle"><option value="MONTH">按月</option><option value="QUARTER">按季</option><option value="YEAR">按年</option></select></div>
          <div class="field"><label>账单日</label><input v-model.number="form.billDay" type="number" min="1" max="28" /></div>
          <div class="field" style="flex:0 0 auto"><label><input type="checkbox" v-model="form.draft" /> 保存草稿</label></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="canAction('contract:create', 'contract')" class="primary" :disabled="busy" @click="create">创建合同</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>合同列表</h2><span class="small muted">生效合同可生成租金账单</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="contractQuery" placeholder="搜索合同号/承租人/房屋" style="max-width:300px" @input="page = 1" />
        </div>
        <DataTable :rows="pagedContracts" :columns="contractColumns" :page="page" :page-size="10" :total="filteredContracts.length" empty-text="暂无合同" @update:page="page = $event">
          <template #cell-rentAmount="{ row }">¥{{ money(row.rentAmount) }}</template>
          <template #cell-depositAmount="{ row }">¥{{ money(row.depositAmount) }}</template>
          <template #cell-contractStatus="{ row }"><span class="badge" :class="row.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ row.contractStatus }}</span></template>
          <template #cell-actions="{ row }">
            <div class="row">
              <button class="sm" @click="openFiles(row)">附件</button>
              <button v-if="canAction('contract:submit', 'contract') && row.contractStatus === 'DRAFT'" class="sm" :disabled="busy" @click="contractAction(row, 'submit')">提交</button>
              <button v-if="canAction('contract:activate', 'contract') && row.contractStatus === 'DRAFT'" class="sm" :disabled="busy" @click="contractAction(row, 'activate')">直接生效</button>
              <button v-if="canAction('contract:discard', 'contract') && row.contractStatus === 'DRAFT'" class="sm danger" :disabled="busy" @click="contractAction(row, 'discard')">作废</button>
              <button v-if="canAction('contract:approve', 'contract') && row.contractStatus === 'APPROVING'" class="sm primary" :disabled="busy" @click="contractAction(row, 'approve')">审批通过</button>
              <button v-if="canAction('contract:withdraw', 'contract') && row.contractStatus === 'APPROVING'" class="sm" :disabled="busy" @click="contractAction(row, 'withdraw')">撤回</button>
              <button v-if="canAction('billing:pay', 'billing') && row.contractStatus === 'ACTIVE'" class="sm primary" @click="openPayment(row)">收款</button>
            </div>
          </template>
        </DataTable>
      </div>

      <div v-if="selectedContract" class="panel">
        <div class="panel-head"><h2>合同附件</h2><span class="small muted">{{ selectedContract.contractNo }}</span></div>
        <div class="row" style="margin-bottom:10px">
          <input type="file" @change="uploadFile" :disabled="fileBusy" style="max-width:320px" />
        </div>
        <div v-if="!files.length" class="empty">暂无附件</div>
        <div v-for="f in files" :key="f.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ f.fileName }}</div><div class="small muted">{{ f.fileSize }} bytes · {{ f.createTime }}</div></div>
          <button class="sm" @click="downloadFile(f)">下载</button>
        </div>
      </div>

      <div v-if="selectedContract" class="panel">
        <div class="panel-head"><h2>合同同住人</h2><span class="small muted">{{ selectedContract.contractNo }} · {{ cohabitants.length }} 人</span></div>
        <div class="row" style="margin-bottom:10px">
          <div class="field" style="flex:2"><label>人员</label><SearchSelect v-model="cohabForm.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" placeholder="搜索人员" /></div>
          <div class="field"><label>关系</label><select v-model="cohabForm.relationType"><option value="SPOUSE">配偶</option><option value="CHILD">子女</option><option value="PARENT">父母</option><option value="FAMILY">家庭成员</option><option value="OTHER">其他</option></select></div>
          <div class="field"><label>开始</label><input v-model="cohabForm.startDate" type="date" /></div>
          <div class="field"><label>结束</label><input v-model="cohabForm.endDate" type="date" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addCohabitant">新增同住人</button></div>
        </div>
        <div v-if="!cohabitants.length" class="empty">暂无同住人</div>
        <div v-for="c in cohabitants" :key="c.id" class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <div style="flex:1"><div>{{ c.personName }} · {{ c.relationType }}</div><div class="small muted">{{ c.startDate || '' }} ~ {{ c.endDate || '长期' }}</div></div>
          <span class="badge green">{{ c.cohabitantStatus }}</span>
          <button class="sm danger" :disabled="busy" @click="removeCohabitant(c)">移除</button>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>生成租金账单</h2><span class="small muted">补贴会在账单生成时自动抵扣</span></div>
        <div class="row">
          <div class="field"><label>合同</label>
            <SearchSelect v-model="billForm.contractId" :options="contracts" label-key="contractNo" sublabel-key="personName" value-key="id" placeholder="搜索合同号/承租人" />
          </div>
          <div class="field"><label>周期开始</label><input v-model="billForm.periodStart" type="date" /></div>
          <div class="field"><label>周期结束</label><input v-model="billForm.periodEnd" type="date" /></div>
          <div class="field"><label>金额</label><input v-model.number="billForm.amount" type="number" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button :disabled="busy" @click="generateBill">生成账单</button></div>
        </div>
      </div>

      <div v-if="payOpen" class="modal-mask" @click.self="payOpen = false">
        <div class="modal" style="max-width:760px">
          <div class="panel-head"><h2>合同收款</h2><button class="sm" @click="payOpen = false">关闭</button></div>
          <div class="small muted" style="margin-bottom:8px">{{ payContractRow?.contractNo }} · 选择未结清账单，支持部分收款</div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>选择</th><th>账单号</th><th>账期</th><th>应付</th><th>已收</th><th>未收</th><th>本次收款</th></tr></thead>
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
            <div class="field" style="max-width:180px"><label>收款方式</label><select v-model="payMethod"><option value="CASH">现金</option><option value="WECHAT">微信</option><option value="ALIPAY">支付宝</option><option value="BANK">银行转账</option></select></div>
            <strong>合计：¥{{ money(payTotal) }}</strong>
          </div>
          <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="payBusy" @click="submitPayment">确认收款</button></div>
        </div>
      </div>
    </template>
  </div>
</template>
