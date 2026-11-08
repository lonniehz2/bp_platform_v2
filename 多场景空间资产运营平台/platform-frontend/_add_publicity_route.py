import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Complaints from './pages/Complaints.vue'","import Complaints from './pages/Complaints.vue'\nimport Publicity from './pages/Publicity.vue'")
s=s.replace("    { path: '/complaints', component: Complaints, meta: { title: '投诉与申诉' } },","    { path: '/complaints', component: Complaints, meta: { title: '投诉与申诉' } },\n    { path: '/publicities', component: Publicity, meta: { title: '公示管理' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/complaints', key: 'complaint', menu: 'complaint', icon: '☏' },","  { to: '/complaints', key: 'complaint', menu: 'complaint', icon: '☏' },\n  { to: '/publicities', key: 'publicity', menu: 'publicity', icon: '▣' },")
s=s.replace("  '/complaints': 'nav.complaint',","  '/complaints': 'nav.complaint',\n  '/publicities': 'nav.publicity',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      complaint: '投诉与申诉',","      complaint: '投诉与申诉',\n      publicity: '公示管理',")
s=s.replace("      complaint: 'Complaints & Appeals',","      complaint: 'Complaints & Appeals',\n      publicity: 'Publicity',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('publicity route')
