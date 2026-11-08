import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import MeterReadings from './pages/MeterReadings.vue'","import MeterReadings from './pages/MeterReadings.vue'\nimport Todos from './pages/Todos.vue'\nimport Keyring from './pages/Keyring.vue'\nimport Grants from './pages/Grants.vue'\nimport DeviceEvents from './pages/DeviceEvents.vue'")
s=s.replace("{ path: '/todos', component: Audit, meta: { title: '我的待办' } }","{ path: '/todos', component: Todos, meta: { title: '我的待办' } }")
s=s.replace("{ path: '/keyring', component: Persons, meta: { title: '钥匙包' } }","{ path: '/keyring', component: Keyring, meta: { title: '钥匙包' } }")
s=s.replace("{ path: '/grants', component: Devices, meta: { title: '通行授权' } }","{ path: '/grants', component: Grants, meta: { title: '通行授权' } }")
s=s.replace("{ path: '/dev-events', component: Alerts, meta: { title: '设备告警' } }","{ path: '/dev-events', component: DeviceEvents, meta: { title: '设备告警' } }")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('routes')
