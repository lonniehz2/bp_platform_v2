import io
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("const isLogin = computed(() => route.path === '/login')","const isLogin = computed(() => route.path === '/login')\nconst collapsed = ref(localStorage.getItem('platformSidebar') === '1')")
s=s.replace("const pwdOpen = ref(false)","const pwdOpen = ref(false)\nfunction toggleSidebar() {\n  collapsed.value = !collapsed.value\n  localStorage.setItem('platformSidebar', collapsed.value ? '1' : '0')\n}")
s=s.replace('<aside class="sidebar">','<aside class="sidebar" :class="{ collapsed }">')
s=s.replace('''          <span>{{ t('nav.' + item.key) }}</span>''','''          <span class="nav-label">{{ t('nav.' + item.key) }}</span>''')
s=s.replace('''      <header class="topbar">
        <div class="page-heading">''','''      <header class="topbar">
        <button class="ghost sm" @click="toggleSidebar" title="折叠菜单">☰</button>
        <div class="page-heading">''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
if '.sidebar.collapsed' not in s:
 s += '''

.sidebar.collapsed { width: 64px; flex-basis: 64px; }
.sidebar.collapsed .brand-text,
.sidebar.collapsed .nav-label,
.sidebar.collapsed .sidebar-foot { display: none; }
.sidebar.collapsed .brand { justify-content: center; padding: 0; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 0; }
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('collapse')
