import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'refundPayment' not in s:
 s=s.replace("  payments: (projectId) => request(`/billing/payments?projectId=${projectId}`),","  payments: (projectId) => request(`/billing/payments?projectId=${projectId}`),\n  paymentAllocations: (paymentId) => request(`/billing/payments/${paymentId}/allocations`),\n  refundPayment: (paymentId, body) => request(`/billing/payments/${paymentId}/refund`, { method: 'POST', body: JSON.stringify(body) }),")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Billing.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const adjustForm = reactive({ discountAmount: 0, remark: '' })","const adjustForm = reactive({ discountAmount: 0, remark: '' })\nconst refunding = ref(null)\nconst refundAllocations = ref([])\nconst refundForm = reactive({ allocationId: '', amount: 0, reason: '' })")
insert='''
async function openRefund(p) {
  error.value = ''
  try {
    refunding.value = p
    refundAllocations.value = await api.paymentAllocations(p.id)
    const first = refundAllocations.value[0]
    refundForm.allocationId = first ? first.allocationId : ''
    refundForm.amount = first ? Number(first.amount) - Number(first.refunded || 0) : 0
    refundForm.reason = ''
  } catch (e) { error.value = e.message }
}

function pickAllocation() {
  const a = refundAllocations.value.find(x => String(x.allocationId) === String(refundForm.allocationId))
  refundForm.amount = a ? Number(a.amount) - Number(a.refunded || 0) : 0
}

async function submitRefund() {
  busy.value = true; error.value = ''
  try {
    if (!refunding.value || !refundForm.allocationId) throw new Error('请选择原收款分配')
    await api.refundPayment(refunding.value.id, {
      billId: refundAllocations.value.find(x => String(x.allocationId) === String(refundForm.allocationId))?.billId,
      amount: Number(refundForm.amount),
      reason: refundForm.reason
    })
    refunding.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

'''
marker="function openReceipt(p) {"
s=s.replace(marker,insert+marker,1)
s=s.replace('''                <td><button v-if="p.receiptNo" class="sm" @click="openReceipt(p)">打印</button></td>''','''                <td><div class="row"><button v-if="p.receiptNo" class="sm" @click="openReceipt(p)">打印</button><button v-if="can('billing')" class="sm" @click="openRefund(p)">退款</button></div></td>''')
# add refund modal before adjust modal
old='''    <div v-if="adjusting" class="modal-mask" @click.self="adjusting = null">'''
new='''    <div v-if="refunding" class="modal-mask" @click.self="refunding = null">
      <div class="modal">
        <div class="panel-head"><h2>账单退款</h2><button class="sm" @click="refunding = null">关闭</button></div>
        <div class="field"><label>原收款</label><div class="mono">{{ refunding.paymentNo }} · ¥{{ money(refunding.amount) }}</div></div>
        <div class="field"><label>原收款分配</label>
          <select v-model="refundForm.allocationId" @change="pickAllocation">
            <option v-for="a in refundAllocations" :key="a.allocationId" :value="a.allocationId">
              {{ a.billNo }} · {{ a.periodStart }} ~ {{ a.periodEnd }} · 可退 ¥{{ money(Number(a.amount) - Number(a.refunded || 0)) }}
            </option>
          </select>
        </div>
        <div class="field"><label>退款金额</label><input v-model.number="refundForm.amount" type="number" /></div>
        <div class="field"><label>退款原因</label><input v-model="refundForm.reason" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="submitRefund">确认退款</button></div>
      </div>
    </div>

    <div v-if="adjusting" class="modal-mask" @click.self="adjusting = null">'''
s=s.replace(old,new,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('refund UI')
