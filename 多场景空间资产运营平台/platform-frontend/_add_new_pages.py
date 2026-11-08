import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Billing from './pages/Billing.vue'","import Billing from './pages/Billing.vue'\nimport Deposits from './pages/Deposits.vue'\nimport Changes from './pages/Changes.vue'\nimport Audit from './pages/Audit.vue'")
s=s.replace("    { path: '/billing', component: Billing, meta: { title: '收费与账务' } },","    { path: '/billing', component: Billing, meta: { title: '收费与账务' } },\n    { path: '/deposits', component: Deposits, meta: { title: '押金与补贴' } },\n    { path: '/changes', component: Changes, meta: { title: '合同变更' } },")
s=s.replace("    { path: '/devices', component: Devices, meta: { title: '设备与授权' } },","    { path: '/devices', component: Devices, meta: { title: '设备与授权' } },\n    { path: '/audit', component: Audit, meta: { title: '审批中心' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)

p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("""  { to: '/contracts', label: '合同与租赁', icon: '▤' },
  { to: '/billing', label: '收费与账务', icon: '¥' },
  { to: '/devices', label: '设备与授权', icon: '⌘' },""","""  { to: '/contracts', label: '合同与租赁', icon: '▤' },
  { to: '/changes', label: '合同变更', icon: '⇄' },
  { to: '/billing', label: '收费与账务', icon: '¥' },
  { to: '/deposits', label: '押金与补贴', icon: '◫' },
  { to: '/devices', label: '设备与授权', icon: '⌘' },
  { to: '/audit', label: '审批中心', icon: '✓' },""")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('routes/nav updated')
