import io
p=r'src\pages\Dashboard.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const labels = { LOCK: '门锁', METER: '水电表', ELEVATOR: '电梯', GATE: '门禁' }","const labels = { LOCK: '门锁', METER: '水电表', WATER_METER: '水表', ELEC_METER: '电表', ELECTRICITY_METER: '电表', GAS_METER: '燃气表', ELEVATOR: '电梯', GATE: '门禁' }")
s=s.replace("const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED']","const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED']\n    const statusLabels = { UNPAID: '未缴', PARTIAL: '部分缴', PAID: '已付', OVERDUE: '逾期', WAIVED: '已减免' }")
s=s.replace("data: statuses.map(s => ({ name: s, value: count(bills.value, s, 'billStatus') }))","data: statuses.map(s => ({ name: statusLabels[s], value: count(bills.value, s, 'billStatus') }))")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('chart labels')
