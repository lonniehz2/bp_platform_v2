import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Messages from './pages/Messages.vue'","import Messages from './pages/Messages.vue'\nimport GovReport from './pages/GovReport.vue'")
s=s.replace("    { path: '/messages', component: Messages, meta: { title: '消息中心' } },","    { path: '/messages', component: Messages, meta: { title: '消息中心' } },\n    { path: '/gov-report', component: GovReport, meta: { title: '监管报送' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/messages', key: 'message', menu: 'message', icon: '✉' },","  { to: '/messages', key: 'message', menu: 'message', icon: '✉' },\n  { to: '/gov-report', key: 'gov', menu: 'gov', icon: '⇪' },")
s=s.replace("  '/messages': 'nav.message',","  '/messages': 'nav.message',\n  '/gov-report': 'nav.gov',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      message: '消息中心',","      message: '消息中心',\n      gov: '监管报送',")
s=s.replace("      message: 'Messages',","      message: 'Messages',\n      gov: 'Regulatory Reporting',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('gov route')
