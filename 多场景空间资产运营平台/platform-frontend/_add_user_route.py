import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Messages from './pages/Messages.vue'","import Messages from './pages/Messages.vue'\nimport Users from './pages/Users.vue'")
s=s.replace("    { path: '/messages', component: Messages, meta: { title: '消息中心' } },","    { path: '/messages', component: Messages, meta: { title: '消息中心' } },\n    { path: '/users', component: Users, meta: { title: '用户管理' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/menus', key: 'config', menu: 'config', icon: '☰' },","  { to: '/users', key: 'users', menu: 'config', icon: '♟' },\n  { to: '/menus', key: 'config', menu: 'config', icon: '☰' },")
s=s.replace("  '/menus': 'nav.config',","  '/users': 'nav.users',\n  '/menus': 'nav.config',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      message: '消息中心',","      message: '消息中心',\n      users: '用户管理',")
s=s.replace("      message: 'Messages',","      message: 'Messages',\n      users: 'Users',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('user route')
