import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import OpenApps from './pages/OpenApps.vue'","import OpenApps from './pages/OpenApps.vue'\nimport Messages from './pages/Messages.vue'")
s=s.replace("    { path: '/open-apps', component: OpenApps, meta: { title: '开放平台' } },","    { path: '/open-apps', component: OpenApps, meta: { title: '开放平台' } },\n    { path: '/messages', component: Messages, meta: { title: '消息中心' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/open-apps', key: 'open', menu: 'open', icon: '⇄' },","  { to: '/open-apps', key: 'open', menu: 'open', icon: '⇄' },\n  { to: '/messages', key: 'message', menu: 'message', icon: '✉' },")
s=s.replace("  '/open-apps': 'nav.open',","  '/open-apps': 'nav.open',\n  '/messages': 'nav.message',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      open: '开放平台',","      open: '开放平台',\n      message: '消息中心',")
s=s.replace("      open: 'Open Platform',","      open: 'Open Platform',\n      message: 'Messages',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('message route')
