import io
p=r'src\pages\Applications.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const money = (v) => Number(v || 0).toLocaleString('zh-CN')","const money = (v) => Number(v || 0).toLocaleString('zh-CN')\nconst incomeLabel = (v) => ({ LOW: '低收入', LOWER_MIDDLE: '中低收入', MIDDLE: '中等收入' }[v] || v || '-')\nconst housingLabel = (v) => ({ NO_HOUSE: '无房', RENTING: '租房', WITH_FAMILY: '与家人同住' }[v] || v || '-')\nconst urgencyLabel = (v) => ({ NORMAL: '普通', URGENT: '紧急' }[v] || v || '-')")
s=s.replace("{{ a.incomeLevel || '-' }}","{{ incomeLabel(a.incomeLevel) }}")
s=s.replace("{{ a.housingStatus || '-' }}","{{ housingLabel(a.housingStatus) }}")
s=s.replace("{{ a.urgency || '-' }}","{{ urgencyLabel(a.urgency) }}")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('labels')
