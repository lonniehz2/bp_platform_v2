import io
p=r'src\pages\Changes.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''const changes = ref([])''','''const changes = ref([])
const houses = ref([])''')
s=s.replace('''const form = reactive({ changeType: 'RENT_CHANGE', rentAmount: 1500, endDate: '2027-10-31', effectiveDate: '2026-12-01', reason: '页面调整' })''','''const form = reactive({ changeType: 'RENT_CHANGE', rentAmount: 1500, endDate: '2027-10-31', houseId: '', effectiveDate: '2026-12-01', reason: '页面调整' })''')
s=s.replace('''    contracts.value = await api.contracts(project.value.id)
    if (!selectedContractId.value && contracts.value.length) selectedContractId.value = contracts.value[0].id''','''    const [cs, hs] = await Promise.all([api.contracts(project.value.id), api.houses(project.value.id)])
    contracts.value = cs
    houses.value = hs.filter(h => h.houseStatus === 'VACANT')
    if (!selectedContractId.value && contracts.value.length) selectedContractId.value = contracts.value[0].id
    if (!form.houseId && houses.value.length) form.houseId = houses.value[0].id''')
s=s.replace('''      after: form.changeType === 'RENT_CHANGE' ? { rentAmount: Number(form.rentAmount) } : { endDate: form.endDate },''','''      after: form.changeType === 'RENT_CHANGE'
        ? { rentAmount: Number(form.rentAmount) }
        : form.changeType === 'ROOM_CHANGE'
          ? { houseId: form.houseId }
          : { endDate: form.endDate },''')
s=s.replace('''<select v-model="form.changeType"><option value="RENT_CHANGE">租金变更</option><option value="TERM_CHANGE">期限变更</option><option value="TERMINATION">退租</option></select>''','''<select v-model="form.changeType"><option value="RENT_CHANGE">租金变更</option><option value="TERM_CHANGE">期限变更</option><option value="ROOM_CHANGE">换房</option><option value="TERMINATION">退租</option></select>''')
s=s.replace('''          <div class="field" v-if="form.changeType === 'RENT_CHANGE'"><label>新租金</label><input v-model.number="form.rentAmount" type="number" /></div>
          <div class="field" v-else><label>新结束日期</label><input v-model="form.endDate" type="date" /></div>''','''          <div class="field" v-if="form.changeType === 'RENT_CHANGE'"><label>新租金</label><input v-model.number="form.rentAmount" type="number" /></div>
          <div class="field" v-else-if="form.changeType === 'ROOM_CHANGE'"><label>新房屋</label>
            <select v-model="form.houseId"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select>
          </div>
          <div class="field" v-else><label>新结束日期</label><input v-model="form.endDate" type="date" /></div>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('exchange form added')
