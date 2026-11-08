import io
p=r'src\auto-i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  if (!parent || ['SCRIPT', 'STYLE', 'TEXTAREA'].includes(parent.tagName)) return","  if (!parent || ['SCRIPT', 'STYLE', 'TEXTAREA'].includes(parent.tagName)) return\n  if (parent.closest('[data-no-i18n]')) return")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Translations.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('<table>','<table data-no-i18n>')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Complaints.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const type = ref('')","const type = ref(forcedType.value || '')")
s=s.replace('''        <select v-model="type" @change="load" style="width:140px"><option value="">全部</option><option value="COMPLAINT">投诉</option><option value="APPEAL">申诉</option><option value="VISIT">走访</option></select>''','''        <select v-if="!forcedType" v-model="type" @change="load" style="width:140px"><option value="">全部</option><option value="COMPLAINT">投诉</option><option value="APPEAL">申诉</option><option value="VISIT">走访</option></select>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('fixes')
