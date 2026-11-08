import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Reports from './pages/Reports.vue'","import Reports from './pages/Reports.vue'\nimport FeeItems from './pages/FeeItems.vue'")
s=s.replace("    { path: '/reports', component: Reports, meta: { title: '运营报表' } },","    { path: '/fee-items', component: FeeItems, meta: { title: '计费项目' } },\n    { path: '/reports', component: Reports, meta: { title: '运营报表' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/reports', key: 'reports', menu: 'billing', icon: '▤' },","  { to: '/fee-items', key: 'fee', menu: 'billing', icon: '≡' },\n  { to: '/reports', key: 'reports', menu: 'billing', icon: '▤' },")
s=s.replace("  '/reports': 'nav.reports',","  '/fee-items': 'nav.fee',\n  '/reports': 'nav.reports',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      reports: '运营报表',","      reports: '运营报表',\n      fee: '计费项目',")
s=s.replace("      reports: 'Reports',","      reports: 'Reports',\n      fee: 'Fee Items',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('fee route')
