import io
p=r'src\pages\Persons.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const form = reactive({ personCode: '', personName: '', phone: '', idCardMask: '', personType: 'GUARANTEE_TENANT' })","const form = reactive({ personCode: '', personName: '', phone: '', idCardMask: '', personType: 'GUARANTEE_TENANT', gender: '', birthDate: '', address: '', employer: '', emergencyContact: '', remark: '' })")
s=s.replace("      phone: form.phone, idCardMask: form.idCardMask, personType: form.personType","      phone: form.phone, idCardMask: form.idCardMask, personType: form.personType,\n      gender: form.gender, birthDate: form.birthDate || null, address: form.address,\n      employer: form.employer, emergencyContact: form.emergencyContact, remark: form.remark")
s=s.replace('''        <div class="field"><label>人员类型</label>''','''        <div class="field"><label>性别</label><select v-model="form.gender"><option value="">未填写</option><option value="MALE">男</option><option value="FEMALE">女</option></select></div>
        <div class="field"><label>出生日期</label><input v-model="form.birthDate" type="date" /></div>
        <div class="field"><label>人员类型</label>''')
s=s.replace('''        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('person')" class="primary" :disabled="busy" @click="create">新增人员</button></div>''','''        <div class="field" style="flex:2"><label>住址</label><input v-model="form.address" /></div>
        <div class="field"><label>工作单位</label><input v-model="form.employer" /></div>
        <div class="field"><label>紧急联系人</label><input v-model="form.emergencyContact" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('person')" class="primary" :disabled="busy" @click="create">新增人员</button></div>''')
s=s.replace('''            <thead><tr><th>人员编码</th><th>姓名</th><th>手机号</th><th>类型</th><th>状态</th></tr></thead>''','''            <thead><tr><th>人员编码</th><th>姓名</th><th>手机号</th><th>性别</th><th>类型</th><th>状态</th></tr></thead>''')
s=s.replace('''                <td class="mono">{{ p.personCode }}</td><td>{{ p.personName }}</td><td>{{ p.phone || '-' }}</td>
                <td>{{ p.personType || '-' }}</td><td><span class="badge green">{{ p.status }}</span></td>''','''                <td class="mono">{{ p.personCode }}</td><td>{{ p.personName }}</td><td>{{ p.phone || '-' }}</td>
                <td>{{ p.gender === 'MALE' ? '男' : p.gender === 'FEMALE' ? '女' : '-' }}</td>
                <td>{{ p.personType || '-' }}</td><td><span class="badge green">{{ p.status }}</span></td>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('person ui')
