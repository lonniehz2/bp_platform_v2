import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import Search from './pages/Search.vue'","import Search from './pages/Search.vue'\nimport Help from './pages/Help.vue'")
s=s.replace("    { path: '/search', component: Search, meta: { title: '统一查询' } },","    { path: '/search', component: Search, meta: { title: '统一查询' } },\n    { path: '/help', component: Help, meta: { title: '使用帮助' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/migration-exceptions', key: 'migration', menu: 'system', icon: '!' }","  { to: '/migration-exceptions', key: 'migration', menu: 'system', icon: '!' },\n  { to: '/help', key: 'help', menu: 'help', icon: '?' }")
s=s.replace("  '/migration-exceptions': 'nav.migration'","  '/migration-exceptions': 'nav.migration',\n  '/help': 'nav.help'")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      migration: '迁移异常'","      migration: '迁移异常',\n      help: '使用帮助'")
s=s.replace("      migration: 'Migration Exceptions'","      migration: 'Migration Exceptions',\n      help: 'Help'")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('help route')
