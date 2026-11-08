import io
p=r'src\pages\Applications.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const form = reactive({ applicationNo: '', applicantPersonId: '', familySize: 1, applicationType: 'PUBLIC_RENTAL' })","const form = reactive({ applicationNo: '', applicantPersonId: '', familySize: 1, applicationType: 'PUBLIC_RENTAL', contactPhone: '', incomeLevel: 'LOW', housingStatus: 'NO_HOUSE', urgency: 'NORMAL', remark: '' })")
s=s.replace("      familySize: Number(form.familySize || 1)\n    })","      familySize: Number(form.familySize || 1), contactPhone: form.contactPhone,\n      incomeLevel: form.incomeLevel, housingStatus: form.housingStatus,\n      urgency: form.urgency, remark: form.remark\n    })")
s=s.replace('''          <div class="field"><label>家庭人数</label><input v-model.number="form.familySize" type="number" min="1" /></div>''','''          <div class="field"><label>家庭人数</label><input v-model.number="form.familySize" type="number" min="1" /></div>
          <div class="field"><label>联系电话</label><input v-model="form.contactPhone" /></div>
          <div class="field"><label>收入水平</label><select v-model="form.incomeLevel"><option value="LOW">低收入</option><option value="LOWER_MIDDLE">中低收入</option><option value="MIDDLE">中等收入</option></select></div>
          <div class="field"><label>住房情况</label><select v-model="form.housingStatus"><option value="NO_HOUSE">无房</option><option value="RENTING">租房</option><option value="WITH_FAMILY">与家人同住</option></select></div>
          <div class="field"><label>紧急程度</label><select v-model="form.urgency"><option value="NORMAL">普通</option><option value="URGENT">紧急</option></select></div>
          <div class="field" style="flex:2"><label>备注</label><input v-model="form.remark" /></div>''')
s=s.replace('''            <thead><tr><th>申请编号</th><th>申请人</th><th>家庭人数</th><th>状态</th><th>操作</th></tr></thead>''','''            <thead><tr><th>申请编号</th><th>申请人</th><th>家庭人数</th><th>收入水平</th><th>住房情况</th><th>紧急程度</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''                <td>{{ a.familySize }}</td>''','''                <td>{{ a.familySize }}</td><td>{{ a.incomeLevel || '-' }}</td><td>{{ a.housingStatus || '-' }}</td><td>{{ a.urgency || '-' }}</td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('application ui')
