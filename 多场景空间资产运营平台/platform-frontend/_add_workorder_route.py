import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Audit from './pages/Audit.vue'","import Audit from './pages/Audit.vue'\nimport WorkOrders from './pages/WorkOrders.vue'")
s=s.replace("    { path: '/audit', component: Audit, meta: { title: '审批中心' } },","    { path: '/work-orders', component: WorkOrders, meta: { title: '服务与工单' } },\n    { path: '/audit', component: Audit, meta: { title: '审批中心' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/audit', key: 'audit', menu: 'audit', icon: '✓' },","  { to: '/work-orders', key: 'service', menu: 'service', icon: '⚒' },\n  { to: '/audit', key: 'audit', menu: 'audit', icon: '✓' },")
s=s.replace("  '/audit': 'nav.audit',","  '/work-orders': 'nav.service',\n  '/audit': 'nav.audit',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      audit: '审批中心',","      service: '服务与工单',\n      audit: '审批中心',")
s=s.replace("      audit: 'Approvals',","      service: 'Service Orders',\n      audit: 'Approvals',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('workorder route')
