import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Help from './pages/Help.vue'","import Help from './pages/Help.vue'\nimport HouseCalendar from './pages/HouseCalendar.vue'")
s=s.replace("    { path: '/help', component: Help, meta: { title: '使用帮助' } },","    { path: '/help', component: Help, meta: { title: '使用帮助' } },\n    { path: '/house-calendar', component: HouseCalendar, meta: { title: '日房态' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/short-rent-orders', key: 'shortrent', menu: 'shortrent', icon: '⌂' },","  { to: '/short-rent-orders', key: 'shortrent', menu: 'shortrent', icon: '⌂' },\n  { to: '/house-calendar', key: 'calendar', menu: 'calendar', icon: '▦' },")
s=s.replace("  '/short-rent-orders': 'nav.shortrent',","  '/short-rent-orders': 'nav.shortrent',\n  '/house-calendar': 'nav.calendar',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      shortrent: '短租订单',","      shortrent: '短租订单',\n      calendar: '日房态',")
s=s.replace("      shortrent: 'Short Rent',","      shortrent: 'Short Rent',\n      calendar: 'House Calendar',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
if '.cal-cell' not in s:
 s += '''

.cal-cell { display: block; width: 18px; height: 18px; border-radius: 3px; margin: auto; }
.cal-cell.green { background: #b7eb8f; }
.cal-cell.blue { background: #69c0ff; }
.cal-cell.orange { background: #ffc069; }
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('calendar route')
