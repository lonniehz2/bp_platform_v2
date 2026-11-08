import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'adjustBill' not in s:
 s=s.replace("  pay: (billId, body) =>","  adjustBill: (billId, body) => request(`/billing/bills/${billId}/adjust`, { method: 'POST', body: JSON.stringify(body) }),\n  pay: (billId, body) =>")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Billing.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const receipt = ref(null)","const receipt = ref(null)\nconst adjusting = ref(null)\nconst adjustForm = reactive({ discountAmount: 0, remark: '' })")
s=s.replace("function openReceipt(p) { receipt.value = p }","function openAdjust(b) { adjusting.value = b; adjustForm.discountAmount = 0; adjustForm.remark = '' }\n\nasync function adjust() {\n  busy.value = true; error.value = ''\n  try {\n    if (!adjusting.value) return\n    await api.adjustBill(adjusting.value.id, { discountAmount: Number(adjustForm.discountAmount || 0), remark: adjustForm.remark })\n    adjusting.value = null\n    await load()\n  } catch (e) { error.value = e.message } finally { busy.value = false }\n}\n\nfunction openReceipt(p) { receipt.value = p }")
s=s.replace('''            <thead><tr><th>账单号</th><th>承租人</th><th>周期</th><th>账单金额</th><th>补贴</th><th>应付</th><th>已收</th><th>状态</th></tr></thead>''','''            <thead><tr><th>账单号</th><th>承租人</th><th>周期</th><th>账单金额</th><th>补贴</th><th>应付</th><th>已收</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''                <td><span class="badge" :class="statusClass(b.billStatus)">{{ b.billStatus }}</span></td>
              </tr>''','''                <td><span class="badge" :class="statusClass(b.billStatus)">{{ b.billStatus }}</span></td>
                <td><button v-if="can('billing') && b.billStatus !== 'PAID'" class="sm" @click="openAdjust(b)">调整</button></td>
              </tr>''')
s=s.replace('''    <div v-if="receipt" class="modal-mask"''','''    <div v-if="adjusting" class="modal-mask" @click.self="adjusting = null">
      <div class="modal">
        <div class="panel-head"><h2>账单调整</h2><button class="sm" @click="adjusting = null">关闭</button></div>
        <div class="field"><label>账单</label><div class="mono">{{ adjusting.billNo }}</div></div>
        <div class="field"><label>新增减免</label><input v-model.number="adjustForm.discountAmount" type="number" /></div>
        <div class="field"><label>调整原因</label><input v-model="adjustForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="adjust">保存</button></div>
      </div>
    </div>

    <div v-if="receipt" class="modal-mask"''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('adjust ui')
