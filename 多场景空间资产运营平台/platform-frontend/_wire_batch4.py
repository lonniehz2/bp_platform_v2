import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import DeviceEvents from './pages/DeviceEvents.vue'","import DeviceEvents from './pages/DeviceEvents.vue'\nimport DeviceBinding from './pages/DeviceBinding.vue'\nimport AccessRecords from './pages/AccessRecords.vue'\nimport Orgs from './pages/Orgs.vue'\nimport PlatformInfo from './pages/PlatformInfo.vue'")
s=s.replace("{ path: '/device-bind', component: Devices, meta: { title: '设备绑定' } }","{ path: '/device-bind', component: DeviceBinding, meta: { title: '设备绑定' } }")
s=s.replace("{ path: '/access', component: Access, meta: { title: '通行记录' } }","{ path: '/access', component: AccessRecords, meta: { title: '通行记录' } }")
s=s.replace("{ path: '/orgs', component: Projects, meta: { title: '组织机构' } }","{ path: '/orgs', component: Orgs, meta: { title: '组织机构' } }")
s=s.replace("{ path: '/platform-info', component: Help, meta: { title: '平台信息' } }","{ path: '/platform-info', component: PlatformInfo, meta: { title: '平台信息' } }")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('batch4 routes')
