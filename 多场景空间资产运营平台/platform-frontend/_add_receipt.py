import io
p=r'src\pages\Billing.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const payForm = reactive({ billId: '', amount: '', method: 'CASH' })","const payForm = reactive({ billId: '', amount: '', method: 'CASH' })\nconst receipt = ref(null)")
s=s.replace("async function pay() {","function openReceipt(p) { receipt.value = p }\nfunction printReceipt() { window.print() }\n\nasync function pay() {")
s=s.replace('''        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>收款单号</th><th>金额</th><th>方式</th><th>状态</th><th>收据</th><th>时间</th></tr></thead>
            <tbody>
              <tr v-for="p in payments" :key="p.id">
                <td class="mono">{{ p.paymentNo }}</td><td>¥{{ money(p.amount) }}</td><td>{{ p.paymentMethod }}</td>
                <td><span class="badge green">{{ p.paymentStatus }}</span></td><td class="mono">{{ p.receiptNo || '-' }}</td><td class="small">{{ p.paidTime }}</td>
              </tr>
            </tbody>
          </table>
        </div>''','''        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>收款单号</th><th>金额</th><th>方式</th><th>状态</th><th>收据</th><th>时间</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="p in payments" :key="p.id">
                <td class="mono">{{ p.paymentNo }}</td><td>¥{{ money(p.amount) }}</td><td>{{ p.paymentMethod }}</td>
                <td><span class="badge green">{{ p.paymentStatus }}</span></td><td class="mono">{{ p.receiptNo || '-' }}</td><td class="small">{{ p.paidTime }}</td>
                <td><button v-if="p.receiptNo" class="sm" @click="openReceipt(p)">打印</button></td>
              </tr>
            </tbody>
          </table>
        </div>''')
s=s.replace('''    </template>
  </div>
</template>''','''    </template>

    <div v-if="receipt" class="modal-mask" @click.self="receipt = null">
      <div class="modal receipt-box">
        <div class="panel-head"><h2>收款收据</h2><button class="sm no-print" @click="receipt = null">关闭</button></div>
        <div class="receipt">
          <h3>保障房租金收据</h3>
          <p>收据号：{{ receipt.receiptNo }}</p>
          <p>收款单号：{{ receipt.paymentNo }}</p>
          <p>收款金额：¥{{ money(receipt.amount) }}</p>
          <p>收款方式：{{ receipt.paymentMethod }}</p>
          <p>收款时间：{{ receipt.paidTime }}</p>
          <p class="small muted">本收据由多场景空间资产运营平台生成</p>
        </div>
        <div class="row no-print" style="justify-content:flex-end;margin-top:12px">
          <button class="primary" @click="printReceipt">打印</button>
        </div>
      </div>
    </div>
  </div>
</template>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('receipt')
