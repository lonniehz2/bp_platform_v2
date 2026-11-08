import io
p=r'src\App.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace("import { computed, onMounted, reactive, ref } from 'vue'","import { computed, onMounted, reactive, ref, watch } from 'vue'")
old='''const openGroups = ref(new Set(JSON.parse(localStorage.getItem('platformOpenGroups') || '["workbench","risk","guarantee","contract","finance"]')))

const visibleGroups = computed(() => navGroups.map(g => ({
  ...g,
  items: g.items.filter(item => allowedMenus.value.length === 0 || allowedMenus.value.includes(item.menu))
})).filter(g => g.items.length > 0))

function isGroupOpen(key) {
  return openGroups.value.has(key)
}

function toggleGroup(key) {
  const next = new Set(openGroups.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  openGroups.value = next
  localStorage.setItem('platformOpenGroups', JSON.stringify([...next]))
}'''
new='''const openGroups = ref(new Set())

const visibleGroups = computed(() => navGroups.map(g => ({
  ...g,
  items: g.items.filter(item => allowedMenus.value.length === 0 || allowedMenus.value.includes(item.menu))
})).filter(g => g.items.length > 0))

const currentGroupKey = computed(() => {
  const path = route.path
  const group = navGroups.find(g => g.items.some(item =>
    path === item.to || path.startsWith(item.to + '/')))
  return group ? group.key : ''
})

function isGroupOpen(key) {
  return openGroups.value.has(key)
}

function isCurrentGroup(group) {
  return currentGroupKey.value === group.key
}

function toggleGroup(key) {
  const next = new Set()
  if (!openGroups.value.has(key)) next.add(key)
  openGroups.value = next
}

watch(currentGroupKey, (key) => {
  if (key) openGroups.value = new Set([key])
}, { immediate: true })'''
if old not in s: raise SystemExit('openGroups block missing')
s=s.replace(old,new,1)
s=s.replace('''<div v-for="g in visibleGroups" :key="g.key" class="nav-group">
          <button class="nav-group-head" @click="toggleGroup(g.key)" :title="t(g.labelKey)">
            <span class="nav-group-icon">{{ g.icon }}</span>
            <span class="nav-label">{{ t(g.labelKey) }}</span>
            <span class="nav-label nav-group-arrow">{{ isGroupOpen(g.key) ? '−' : '+' }}</span>
          </button>''','''<div v-for="g in visibleGroups" :key="g.key" class="nav-group" :class="{ active: isCurrentGroup(g) }">
          <button class="nav-group-head" :class="{ active: isCurrentGroup(g) }" @click="toggleGroup(g.key)" :title="t(g.labelKey)">
            <span class="nav-group-icon">{{ g.icon }}</span>
            <span class="nav-label">{{ t(g.labelKey) }}</span>
            <span class="nav-label nav-group-arrow">{{ isGroupOpen(g.key) ? '⌄' : '›' }}</span>
          </button>''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\styles.css'
s=io.open(p,encoding='utf-8').read()
old='''.nav-group { margin: 2px 0 4px; }
.nav-group-head {
  width: 100%; display: flex; align-items: center; gap: 8px;
  padding: 7px 12px; border: 0; background: transparent; color: var(--muted);
  font-size: 11px; letter-spacing: .3px; text-align: left; cursor: pointer;
}
.nav-group-head:hover { color: var(--brand); }
.nav-group-icon { width: 16px; text-align: center; font-size: 12px; }
.nav-group-arrow { margin-left: auto; }
.nav-group-items .nav-item { margin: 1px 8px; height: 36px; }
.sidebar.collapsed .nav-group-head { justify-content: center; padding: 7px 0; }
.sidebar.collapsed .nav-group-arrow { display: none; }'''
new='''.nav-group { margin: 4px 8px; }
.nav-group-head {
  width: 100%; display: flex; align-items: center; gap: 9px;
  padding: 9px 10px; border: 0; background: transparent; color: var(--regular);
  font-size: 12.5px; font-weight: 600; letter-spacing: .02em;
  text-align: left; cursor: pointer; border-radius: 7px;
}
.nav-group-head:hover { color: var(--brand); background: var(--brand-soft); }
.nav-group-head.active { color: var(--brand); background: var(--brand-soft); }
.nav-group-head.active .nav-group-icon { color: var(--brand); }
.nav-group-icon { width: 18px; text-align: center; font-size: 13px; color: var(--muted); }
.nav-group-arrow { margin-left: auto; font-size: 15px; color: var(--muted); line-height: 1; }
.nav-group-head.active .nav-group-arrow { color: var(--brand); }
.nav-group-items {
  margin: 2px 0 5px 18px; padding: 2px 0 2px 10px;
  border-left: 1px solid var(--line);
}
.nav-group-items .nav-item {
  margin: 1px 0; height: 38px; padding: 0 10px 0 9px;
  border-radius: 6px; font-size: 13.5px;
}
.nav-group-items .nav-item.router-link-active {
  background: var(--brand-soft); color: var(--brand); font-weight: 600;
  box-shadow: inset 3px 0 0 var(--brand);
}
.sidebar.collapsed .nav-group { margin: 2px 0; }
.sidebar.collapsed .nav-group-head { justify-content: center; padding: 9px 0; }
.sidebar.collapsed .nav-group-arrow { display: none; }
.sidebar.collapsed .nav-group-items { margin: 0; padding: 0; border-left: 0; }
.sidebar.collapsed .nav-group-items .nav-item { margin: 2px 4px; padding: 0; justify-content: center; }
.sidebar.collapsed .nav-group-items .nav-item.router-link-active { box-shadow: none; }'''
if old not in s: raise SystemExit('css block missing')
s=s.replace(old,new,1)
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('sidebar B')
