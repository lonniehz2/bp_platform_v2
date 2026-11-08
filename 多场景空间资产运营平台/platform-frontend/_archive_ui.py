import io
p=r'src\pages\Applications.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("urgency: 'NORMAL', remark: '' })","urgency: 'NORMAL', remark: '', guaranteeType: 'PUBLIC_RENTAL', familyType: 'SINGLE', subsidyStatus: 'NONE', archiveNo: '' })")
s=s.replace("      urgency: form.urgency, remark: form.remark\n    })","      urgency: form.urgency, remark: form.remark,\n      guaranteeType: form.guaranteeType, familyType: form.familyType,\n      subsidyStatus: form.subsidyStatus, archiveNo: form.archiveNo\n    })")
s=s.replace('''          <div class="field" style="flex:2"><label>备注</label><input v-model="form.remark" /></div>''','''          <div class="field"><label>保障类型</label><select v-model="form.guaranteeType"><option value="PUBLIC_RENTAL">公共租赁</option><option value="LOW_RENT">廉租住房</option><option value="SUBSIDY">租赁补贴</option></select></div>
          <div class="field"><label>家庭结构</label><select v-model="form.familyType"><option value="SINGLE">单身</option><option value="COUPLE">夫妻</option><option value="WITH_CHILDREN">有子女家庭</option><option value="ELDERLY">老年家庭</option></select></div>
          <div class="field"><label>补贴状态</label><select v-model="form.subsidyStatus"><option value="NONE">无</option><option value="APPLYING">申请中</option><option value="ACTIVE">已享受</option></select></div>
          <div class="field"><label>档案编号</label><input v-model="form.archiveNo" /></div>
          <div class="field" style="flex:2"><label>备注</label><input v-model="form.remark" /></div>''')
s=s.replace('''            <thead><tr><th>申请编号</th><th>申请人</th><th>家庭人数</th><th>收入水平</th><th>住房情况</th><th>紧急程度</th><th>状态</th><th>操作</th></tr></thead>''','''            <thead><tr><th>申请编号</th><th>申请人</th><th>保障类型</th><th>家庭结构</th><th>档案编号</th><th>家庭人数</th><th>收入水平</th><th>住房情况</th><th>状态</th><th>操作</th></tr></thead>''')
s=s.replace('''                <td>{{ a.familySize }}</td><td>{{ incomeLabel(a.incomeLevel) }}</td><td>{{ housingLabel(a.housingStatus) }}</td><td>{{ urgencyLabel(a.urgency) }}</td>''','''                <td>{{ a.guaranteeType || '-' }}</td><td>{{ a.familyType || '-' }}</td><td>{{ a.archiveNo || '-' }}</td>
                <td>{{ a.familySize }}</td><td>{{ incomeLabel(a.incomeLevel) }}</td><td>{{ housingLabel(a.housingStatus) }}</td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('archive ui')
