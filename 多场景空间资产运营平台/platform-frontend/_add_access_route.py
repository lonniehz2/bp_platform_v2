import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import WorkOrders from './pages/WorkOrders.vue'","import WorkOrders from './pages/WorkOrders.vue'\nimport Access from './pages/Access.vue'")
s=s.replace("    { path: '/work-orders', component: WorkOrders, meta: { title: '服务与工单' } },","    { path: '/work-orders', component: WorkOrders, meta: { title: '服务与工单' } },\n    { path: '/access-records', component: Access, meta: { title: '访客通行' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/work-orders', key: 'service', menu: 'service', icon: '⚒' },","  { to: '/work-orders', key: 'service', menu: 'service', icon: '⚒' },\n  { to: '/access-records', key: 'access', menu: 'access', icon: '⌂' },")
s=s.replace("  '/work-orders': 'nav.service',","  '/work-orders': 'nav.service',\n  '/access-records': 'nav.access',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      service: '服务与工单',","      service: '服务与工单',\n      access: '访客通行',")
s=s.replace("      service: 'Service Orders',","      service: 'Service Orders',\n      access: 'Access Records',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('access route')
