import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import HouseCalendar from './pages/HouseCalendar.vue'","import HouseCalendar from './pages/HouseCalendar.vue'\nimport Energy from './pages/Energy.vue'")
s=s.replace("    { path: '/house-calendar', component: HouseCalendar, meta: { title: '日房态' } },","    { path: '/house-calendar', component: HouseCalendar, meta: { title: '日房态' } },\n    { path: '/energy', component: Energy, meta: { title: '能耗分析' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/meters', key: 'meter', menu: 'asset', icon: '◉' },","  { to: '/meters', key: 'meter', menu: 'asset', icon: '◉' },\n  { to: '/energy', key: 'energy', menu: 'energy', icon: '▤' },")
s=s.replace("  '/meters': 'nav.meter',","  '/meters': 'nav.meter',\n  '/energy': 'nav.energy',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      meter: '计量与能耗',","      meter: '计量与能耗',\n      energy: '能耗分析',")
s=s.replace("      meter: 'Meters & Energy',","      meter: 'Meters & Energy',\n      energy: 'Energy Analysis',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('energy route')
