import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Devices from './pages/Devices.vue'","import Devices from './pages/Devices.vue'\nimport Meters from './pages/Meters.vue'")
s=s.replace("    { path: '/devices', component: Devices, meta: { title: '设备与授权' } },","    { path: '/meters', component: Meters, meta: { title: '计量与能耗' } },\n    { path: '/devices', component: Devices, meta: { title: '设备与授权' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/devices', key: 'device', menu: 'device', icon: '⌘' },","  { to: '/meters', key: 'meter', menu: 'asset', icon: '◉' },\n  { to: '/devices', key: 'device', menu: 'device', icon: '⌘' },")
s=s.replace("  '/devices': 'nav.device',","  '/meters': 'nav.meter',\n  '/devices': 'nav.device',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      device: '设备与授权',","      meter: '计量与能耗',\n      device: '设备与授权',")
s=s.replace("      device: 'Devices & Access',","      meter: 'Meters & Energy',\n      device: 'Devices & Access',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('meter route')
