import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Access from './pages/Access.vue'","import Access from './pages/Access.vue'\nimport Complaints from './pages/Complaints.vue'")
s=s.replace("    { path: '/access-records', component: Access, meta: { title: '访客通行' } },","    { path: '/access-records', component: Access, meta: { title: '访客通行' } },\n    { path: '/complaints', component: Complaints, meta: { title: '投诉与申诉' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/access-records', key: 'access', menu: 'access', icon: '⌂' },","  { to: '/access-records', key: 'access', menu: 'access', icon: '⌂' },\n  { to: '/complaints', key: 'complaint', menu: 'complaint', icon: '☏' },")
s=s.replace("  '/access-records': 'nav.access',","  '/access-records': 'nav.access',\n  '/complaints': 'nav.complaint',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      access: '访客通行',","      access: '访客通行',\n      complaint: '投诉与申诉',")
s=s.replace("      access: 'Access Records',","      access: 'Access Records',\n      complaint: 'Complaints & Appeals',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('complaint route')
