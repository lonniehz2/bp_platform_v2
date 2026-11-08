export const navGroups = [
  {
    key: 'workbench',
    labelKey: 'group.workbench',
    icon: '◈',
    items: [
      { to: '/', key: 'dashboard', menu: 'dashboard', icon: '◈' },
      { to: '/search', key: 'search', menu: 'search', icon: '⌕' },
      { to: '/messages', key: 'message', menu: 'message', icon: '✉' }
    ]
  },
  {
    key: 'risk',
    labelKey: 'group.risk',
    icon: '⚠',
    items: [
      { to: '/alerts', key: 'alert', menu: 'alert', icon: '⚠' },
      { to: '/arrears', key: 'arrears', menu: 'billing', icon: '!' },
      { to: '/credits', key: 'credit', menu: 'credit', icon: '✖' }
    ]
  },
  {
    key: 'guarantee',
    labelKey: 'group.guarantee',
    icon: '♙',
    items: [
      { to: '/persons', key: 'person', menu: 'person', icon: '♙' },
      { to: '/applications', key: 'application', menu: 'application', icon: '☷' },
      { to: '/qualification', key: 'qualification', menu: 'contract', icon: '◎' },
      { to: '/publicities', key: 'publicity', menu: 'publicity', icon: '▣' }
    ]
  },
  {
    key: 'contract',
    labelKey: 'group.contract',
    icon: '▤',
    items: [
      { to: '/projects', key: 'asset', menu: 'asset', icon: '▦' },
      { to: '/contracts', key: 'contract', menu: 'contract', icon: '▤' },
      { to: '/changes', key: 'changes', menu: 'contract', icon: '⇄' },
      { to: '/house-calendar', key: 'calendar', menu: 'calendar', icon: '▦' },
      { to: '/short-rent-orders', key: 'shortrent', menu: 'shortrent', icon: '⌂' }
    ]
  },
  {
    key: 'finance',
    labelKey: 'group.finance',
    icon: '¥',
    items: [
      { to: '/billing', key: 'billing', menu: 'billing', icon: '¥' },
      { to: '/fee-items', key: 'fee', menu: 'billing', icon: '≡' },
      { to: '/deposits', key: 'deposits', menu: 'billing', icon: '◫' },
      { to: '/cashflow', key: 'cashflow', menu: 'billing', icon: '↕' },
      { to: '/meters', key: 'meter', menu: 'asset', icon: '◉' },
      { to: '/energy', key: 'energy', menu: 'energy', icon: '▤' },
      { to: '/reports', key: 'reports', menu: 'billing', icon: '▤' }
    ]
  },
  {
    key: 'access',
    labelKey: 'group.access',
    icon: '⌘',
    items: [
      { to: '/devices', key: 'device', menu: 'device', icon: '⌘' },
      { to: '/access-records', key: 'access', menu: 'access', icon: '⌂' }
    ]
  },
  {
    key: 'service',
    labelKey: 'group.service',
    icon: '⚒',
    items: [
      { to: '/work-orders', key: 'service', menu: 'service', icon: '⚒' },
      { to: '/complaints', key: 'complaint', menu: 'complaint', icon: '☏' }
    ]
  },
  {
    key: 'system',
    labelKey: 'group.system',
    icon: '☰',
    items: [
      { to: '/users', key: 'users', menu: 'config', icon: '♟' },
      { to: '/menus', key: 'config', menu: 'config', icon: '☰' },
      { to: '/open-apps', key: 'open', menu: 'open', icon: '⇄' },
      { to: '/gov-report', key: 'gov', menu: 'gov', icon: '⇪' },
      { to: '/audit', key: 'audit', menu: 'audit', icon: '✓' },
      { to: '/migration-exceptions', key: 'migration', menu: 'system', icon: '!' },
      { to: '/help', key: 'help', menu: 'help', icon: '?' }
    ]
  }
]

export const navItems = navGroups.flatMap(g => g.items)
