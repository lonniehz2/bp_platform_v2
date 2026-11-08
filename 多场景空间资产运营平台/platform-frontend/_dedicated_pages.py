import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Allocations from './pages/Allocations.vue'","import Allocations from './pages/Allocations.vue'\nimport Houses from './pages/Houses.vue'\nimport Spaces from './pages/Spaces.vue'\nimport Subsidies from './pages/Subsidies.vue'\nimport MeterReadings from './pages/MeterReadings.vue'")
s=s.replace("{ path: '/houses', component: Projects, meta: { title: '房源台账' } }","{ path: '/houses', component: Houses, meta: { title: '房源台账' } }")
s=s.replace("{ path: '/spaces', component: Projects, meta: { title: '空间层级' } }","{ path: '/spaces', component: Spaces, meta: { title: '空间层级' } }")
s=s.replace("{ path: '/subsidies', component: Deposits, meta: { title: '补贴管理' } }","{ path: '/subsidies', component: Subsidies, meta: { title: '补贴管理' } }")
s=s.replace("{ path: '/meter-readings', component: Meters, meta: { title: '抄表管理' } }","{ path: '/meter-readings', component: MeterReadings, meta: { title: '抄表管理' } }")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('dedicated pages')
