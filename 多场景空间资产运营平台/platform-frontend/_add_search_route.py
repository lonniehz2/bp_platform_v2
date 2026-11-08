import io
p=r'src\main.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import GovReport from './pages/GovReport.vue'","import GovReport from './pages/GovReport.vue'\nimport Search from './pages/Search.vue'")
s=s.replace("    { path: '/gov-report', component: GovReport, meta: { title: '监管报送' } },","    { path: '/gov-report', component: GovReport, meta: { title: '监管报送' } },\n    { path: '/search', component: Search, meta: { title: '统一查询' } },")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("  { to: '/projects', key: 'asset', menu: 'asset', icon: '▦' },","  { to: '/search', key: 'search', menu: 'search', icon: '⌕' },\n  { to: '/projects', key: 'asset', menu: 'asset', icon: '▦' },")
s=s.replace("  '/projects': 'nav.asset',","  '/search': 'nav.search',\n  '/projects': 'nav.asset',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\i18n.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace("      asset: '项目与资产',","      asset: '项目与资产',\n      search: '统一查询',")
s=s.replace("      asset: 'Projects & Assets',","      asset: 'Projects & Assets',\n      search: 'Search',")
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('search route')
