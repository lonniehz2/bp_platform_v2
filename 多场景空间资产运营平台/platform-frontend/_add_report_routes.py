import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Deposits from './pages/Deposits.vue'","import Deposits from './pages/Deposits.vue'\nimport Arrears from './pages/Arrears.vue'\nimport Cashflow from './pages/Cashflow.vue'\nimport Reports from './pages/Reports.vue'")
s=s.replace("    { path: '/deposits', component: Deposits, meta: { title: '押金与补贴' } },","    { path: '/deposits', component: Deposits, meta: { title: '押金与补贴' } },\n    { path: '/arrears', component: Arrears, meta: { title: '欠费清单' } },\n    { path: '/cashflow', component: Cashflow, meta: { title: '资金流水' } },\n    { path: '/reports', component: Reports, meta: { title: '运营报表' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/deposits', key: 'deposits', menu: 'billing', icon: '◫' },","  { to: '/deposits', key: 'deposits', menu: 'billing', icon: '◫' },\n  { to: '/arrears', key: 'arrears', menu: 'billing', icon: '!' },\n  { to: '/cashflow', key: 'cashflow', menu: 'billing', icon: '↕' },\n  { to: '/reports', key: 'reports', menu: 'billing', icon: '▤' },")
s=s.replace("  '/deposits': 'nav.deposits',","  '/deposits': 'nav.deposits',\n  '/arrears': 'nav.arrears',\n  '/cashflow': 'nav.cashflow',\n  '/reports': 'nav.reports',")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      deposits: '押金与补贴',\n      device: '设备与授权',","      deposits: '押金与补贴',\n      arrears: '欠费清单',\n      cashflow: '资金流水',\n      reports: '运营报表',\n      device: '设备与授权',")
s=s.replace("      deposits: 'Deposits & Subsidies',\n      device: 'Devices & Access',","      deposits: 'Deposits & Subsidies',\n      arrears: 'Arrears',\n      cashflow: 'Cash Flow',\n      reports: 'Reports',\n      device: 'Devices & Access',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('routes added')
