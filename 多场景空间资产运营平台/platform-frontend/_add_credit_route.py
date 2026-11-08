import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Alerts from './pages/Alerts.vue'","import Alerts from './pages/Alerts.vue'\nimport Credit from './pages/Credit.vue'")
s=s.replace("    { path: '/alerts', component: Alerts, meta: { title: '风险告警' } },","    { path: '/alerts', component: Alerts, meta: { title: '风险告警' } },\n    { path: '/credits', component: Credit, meta: { title: '信用惩戒' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/alerts', key: 'alert', menu: 'alert', icon: '⚠' },","  { to: '/alerts', key: 'alert', menu: 'alert', icon: '⚠' },\n  { to: '/credits', key: 'credit', menu: 'credit', icon: '✖' },")
s=s.replace("  '/alerts': 'nav.alert',","  '/alerts': 'nav.alert',\n  '/credits': 'nav.credit',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      alert: '风险告警',","      alert: '风险告警',\n      credit: '信用惩戒',")
s=s.replace("      alert: 'Risk Alerts',","      alert: 'Risk Alerts',\n      credit: 'Credit Discipline',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('credit route')
