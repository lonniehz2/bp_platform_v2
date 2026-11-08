import io
p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("rentAmount: 1200, depositAmount: 1200, billingCycle: 'MONTH', billDay: 1","rentAmount: 1200, depositAmount: 1200, billingCycle: 'MONTH', billDay: 1, draft: false")
s=s.replace('''      rentAmount: Number(form.rentAmount), depositAmount: Number(form.depositAmount),
      billingCycle: form.billingCycle, billDay: Number(form.billDay)''','''      rentAmount: Number(form.rentAmount), depositAmount: Number(form.depositAmount),
      billingCycle: form.billingCycle, billDay: Number(form.billDay), draft: form.draft''')
insert='''
async function contractAction(c, action) {
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

'''
marker="async function openFiles(c) {"
s=s.replace(marker,insert+marker,1)
s=s.replace('''<div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('contract')" class="primary" :disabled="busy" @click="create">创建合同</button></div>''','''<div class="field" style="flex:0 0 auto"><label><input type="checkbox" v-model="form.draft" /> 保存草稿</label></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('contract')" class="primary" :disabled="busy" @click="create">创建合同</button></div>''')
s=s.replace('''<td><div class="row"><button class="sm" @click="openFiles(c)">附件</button><button v-if="can('billing') && c.contractStatus === 'ACTIVE'" class="sm primary" @click="openPayment(c)">收款</button></div></td>''','''<td><div class="row">
                  <button class="sm" @click="openFiles(c)">附件</button>
                  <button v-if="can('contract') && c.contractStatus === 'DRAFT'" class="sm" :disabled="busy" @click="contractAction(c, 'submit')">提交</button>
                  <button v-if="can('contract') && c.contractStatus === 'DRAFT'" class="sm" :disabled="busy" @click="contractAction(c, 'activate')">直接生效</button>
                  <button v-if="can('contract') && c.contractStatus === 'DRAFT'" class="sm danger" :disabled="busy" @click="contractAction(c, 'discard')">作废</button>
                  <button v-if="can('contract') && c.contractStatus === 'APPROVING'" class="sm primary" :disabled="busy" @click="contractAction(c, 'approve')">审批通过</button>
                  <button v-if="can('contract') && c.contractStatus === 'APPROVING'" class="sm" :disabled="busy" @click="contractAction(c, 'withdraw')">撤回</button>
                  <button v-if="can('billing') && c.contractStatus === 'ACTIVE'" class="sm primary" @click="openPayment(c)">收款</button>
                </div></td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('contract ui actions')
