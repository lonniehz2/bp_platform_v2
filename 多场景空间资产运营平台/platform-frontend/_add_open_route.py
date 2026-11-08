import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import ShortRent from './pages/ShortRent.vue'","import ShortRent from './pages/ShortRent.vue'\nimport OpenApps from './pages/OpenApps.vue'")
s=s.replace("    { path: '/short-rent-orders', component: ShortRent, meta: { title: '短租订单' } },","    { path: '/short-rent-orders', component: ShortRent, meta: { title: '短租订单' } },\n    { path: '/open-apps', component: OpenApps, meta: { title: '开放平台' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/short-rent-orders', key: 'shortrent', menu: 'shortrent', icon: '⌂' },","  { to: '/short-rent-orders', key: 'shortrent', menu: 'shortrent', icon: '⌂' },\n  { to: '/open-apps', key: 'open', menu: 'open', icon: '⇄' },")
s=s.replace("  '/short-rent-orders': 'nav.shortrent',","  '/short-rent-orders': 'nav.shortrent',\n  '/open-apps': 'nav.open',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      shortrent: '短租订单',","      shortrent: '短租订单',\n      open: '开放平台',")
s=s.replace("      shortrent: 'Short Rent',","      shortrent: 'Short Rent',\n      open: 'Open Platform',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('open route')
