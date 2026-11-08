import io
p=r'src\pages\Contracts.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("rentAmount: 1200, depositAmount: 1200\n})","rentAmount: 1200, depositAmount: 1200, billingCycle: 'MONTH', billDay: 1\n})")
s=s.replace("rentAmount: Number(form.rentAmount), depositAmount: Number(form.depositAmount),\n      billingCycle: 'MONTH', billDay: 1","rentAmount: Number(form.rentAmount), depositAmount: Number(form.depositAmount),\n      billingCycle: form.billingCycle, billDay: Number(form.billDay || 1)")
s=s.replace('''          <div class="field"><label>押金</label><input v-model.number="form.depositAmount" type="number" /></div>''','''          <div class="field"><label>押金</label><input v-model.number="form.depositAmount" type="number" /></div>
          <div class="field"><label>账单周期</label><select v-model="form.billingCycle"><option value="MONTH">按月</option><option value="QUARTER">按季</option><option value="YEAR">按年</option></select></div>
          <div class="field"><label>账单日</label><input v-model.number="form.billDay" type="number" min="1" max="28" /></div>''')
s=s.replace('''<thead><tr><th>合同编号</th><th>房屋</th><th>承租人</th><th>租金</th><th>押金</th><th>状态</th><th>操作</th></tr></thead>''','''<thead><tr><th>合同编号</th><th>房屋</th><th>承租人</th><th>租金</th><th>押金</th><th>周期</th><th>账单日</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''                <td>¥{{ money(c.rentAmount) }}</td><td>¥{{ money(c.depositAmount) }}</td>
                <td><span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span></td>''','''                <td>¥{{ money(c.rentAmount) }}</td><td>¥{{ money(c.depositAmount) }}</td>
                <td>{{ c.billingCycle }}</td><td>{{ c.billDay }}</td>
                <td><span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span></td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Applications.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const form = reactive({ applicationNo: '', applicantPersonId: '', familySize: 1 })","const form = reactive({ applicationNo: '', applicantPersonId: '', familySize: 1, applicationType: 'PUBLIC_RENTAL' })")
s=s.replace("applicationType: 'PUBLIC_RENTAL',","applicationType: form.applicationType,")
s=s.replace('''          <div class="field"><label>家庭人数</label><input v-model.number="form.familySize" type="number" min="1" /></div>''','''          <div class="field"><label>申请类型</label><select v-model="form.applicationType"><option value="PUBLIC_RENTAL">公共租赁</option><option value="AFFORDABLE_RENTAL">保障性租赁</option><option value="TALENT_APARTMENT">人才公寓</option><option value="DORMITORY">宿舍</option></select></div>
          <div class="field"><label>家庭人数</label><input v-model.number="form.familySize" type="number" min="1" /></div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('fields')
