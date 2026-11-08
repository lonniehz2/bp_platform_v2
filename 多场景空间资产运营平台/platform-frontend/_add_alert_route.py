import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Publicity from './pages/Publicity.vue'","import Publicity from './pages/Publicity.vue'\nimport Alerts from './pages/Alerts.vue'")
s=s.replace("    { path: '/publicities', component: Publicity, meta: { title: '公示管理' } },","    { path: '/publicities', component: Publicity, meta: { title: '公示管理' } },\n    { path: '/alerts', component: Alerts, meta: { title: '风险告警' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/publicities', key: 'publicity', menu: 'publicity', icon: '▣' },","  { to: '/publicities', key: 'publicity', menu: 'publicity', icon: '▣' },\n  { to: '/alerts', key: 'alert', menu: 'alert', icon: '⚠' },")
s=s.replace("  '/publicities': 'nav.publicity',","  '/publicities': 'nav.publicity',\n  '/alerts': 'nav.alert',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      publicity: '公示管理',","      publicity: '公示管理',\n      alert: '风险告警',")
s=s.replace("      publicity: 'Publicity',","      publicity: 'Publicity',\n      alert: 'Risk Alerts',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('alert route')
