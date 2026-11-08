import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Credit from './pages/Credit.vue'","import Credit from './pages/Credit.vue'\nimport ShortRent from './pages/ShortRent.vue'")
s=s.replace("    { path: '/credits', component: Credit, meta: { title: '信用惩戒' } },","    { path: '/credits', component: Credit, meta: { title: '信用惩戒' } },\n    { path: '/short-rent-orders', component: ShortRent, meta: { title: '短租订单' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/credits', key: 'credit', menu: 'credit', icon: '✖' },","  { to: '/credits', key: 'credit', menu: 'credit', icon: '✖' },\n  { to: '/short-rent-orders', key: 'shortrent', menu: 'shortrent', icon: '⌂' },")
s=s.replace("  '/credits': 'nav.credit',","  '/credits': 'nav.credit',\n  '/short-rent-orders': 'nav.shortrent',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      credit: '信用惩戒',","      credit: '信用惩戒',\n      shortrent: '短租订单',")
s=s.replace("      credit: 'Credit Discipline',","      credit: 'Credit Discipline',\n      shortrent: 'Short Rent',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('short route')
