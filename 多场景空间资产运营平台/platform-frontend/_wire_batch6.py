import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Translations from './pages/Translations.vue'","import Translations from './pages/Translations.vue'\nimport Patrol from './pages/Patrol.vue'\nimport HouseAccess from './pages/HouseAccess.vue'\nimport Rbac from './pages/Rbac.vue'")
s=s.replace("{ path: '/patrol', component: Alerts, meta: { title: '自动巡查' } }","{ path: '/patrol', component: Patrol, meta: { title: '自动巡查' } }")
s=s.replace("{ path: '/house-access', component: Devices, meta: { title: '房源权限' } }","{ path: '/house-access', component: HouseAccess, meta: { title: '房源权限' } }")
s=s.replace("{ path: '/rbac', component: Users, meta: { title: '用户与权限' } }","{ path: '/rbac/:tab?', component: Rbac, meta: { title: '用户与权限' } }")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('batch6 routes')
