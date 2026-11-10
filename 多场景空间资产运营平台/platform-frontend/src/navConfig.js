export const navGroups = [
  {
    key: 'workbench',
    labelKey: 'group.workbench',
    icon: '◈',
    items: [
      { to: '/guarantee/dashboard', key: 'dashboard', menu: 'dashboard', icon: '◈' },
      { to: '/guarantee/search', key: 'search', menu: 'search', icon: '⌕' },
      { to: '/guarantee/todos', key: 'todos', menu: 'audit', icon: '✓' },
      { to: '/guarantee/messages', key: 'message', menu: 'message', icon: '✉' }
    ]
  },
  {
    key: 'application',
    labelKey: 'group.application',
    icon: '☷',
    items: [
      { to: '/guarantee/applications', key: 'applications', menu: 'application', icon: '☷' },
      { to: '/guarantee/persons', key: 'person', menu: 'person', icon: '♙' },
      { to: '/guarantee/qualification', key: 'qualification', menu: 'contract', icon: '✓' }
    ]
  },
  {
    key: 'waitlist',
    labelKey: 'group.waitlist',
    icon: '↕',
    items: [
      { to: '/guarantee/waitlist', key: 'waitlist', menu: 'waitlist', icon: '↕' },
      { to: '/guarantee/allocations', key: 'allocations', menu: 'application', icon: '◎' },
      { to: '/guarantee/publicities', key: 'publicities', menu: 'publicity', icon: '▣' }
    ]
  },
  {
    key: 'contract',
    labelKey: 'group.contract',
    icon: '▤',
    items: [
      { to: '/guarantee/contracts', key: 'contracts', menu: 'contract', icon: '▤' },
      { to: '/guarantee/contract-changes', key: 'contractChanges', menu: 'contract', icon: '⇄' },
      { to: '/guarantee/exchanges', key: 'exchanges', menu: 'contract', icon: '⇄' },
      { to: '/guarantee/terminations', key: 'terminations', menu: 'contract', icon: '✖' }
    ]
  },
  {
    key: 'finance',
    labelKey: 'group.finance',
    icon: '¥',
    items: [
      { to: '/guarantee/billing', key: 'billing', menu: 'billing', icon: '¥' },
      { to: '/guarantee/deposits', key: 'deposits', menu: 'billing', icon: '◫' },
      { to: '/guarantee/subsidies', key: 'subsidies', menu: 'billing', icon: '◫' },
      { to: '/guarantee/cashflow', key: 'cashflow', menu: 'billing', icon: '↕' },
      { to: '/guarantee/fee-items', key: 'fee', menu: 'billing', icon: '≡' },
      { to: '/guarantee/arrears', key: 'arrears', menu: 'billing', icon: '!' }
    ]
  },
  {
    key: 'asset',
    labelKey: 'group.asset',
    icon: '▦',
    items: [
      { to: '/guarantee/assets', key: 'asset', menu: 'asset', icon: '▦' },
      { to: '/guarantee/listings', key: 'listings', menu: 'asset', icon: '⌂' },
      { to: '/guarantee/houses', key: 'houses', menu: 'asset', icon: '▦' },
      { to: '/guarantee/spaces', key: 'spaces', menu: 'asset', icon: '▤' },
      { to: '/guarantee/house-calendar', key: 'calendar', menu: 'calendar', icon: '▦' },
      { to: '/guarantee/short-rent', key: 'shortrent', menu: 'shortrent', icon: '⌂' }
    ]
  },
  {
    key: 'service',
    labelKey: 'group.service',
    icon: '⚒',
    items: [
      { to: '/guarantee/work-orders', key: 'workOrders', menu: 'service', icon: '⚒' },
      { to: '/guarantee/complaints', key: 'complaints', menu: 'complaint', icon: '☏' },
      { to: '/guarantee/appeals', key: 'appeals', menu: 'complaint', icon: '☏' },
      { to: '/guarantee/visits', key: 'visits', menu: 'complaint', icon: '☏' }
    ]
  },
  {
    key: 'access',
    labelKey: 'group.access',
    icon: '⌘',
    items: [
      { to: '/guarantee/devices', key: 'devices', menu: 'device', icon: '⌘' },
      { to: '/guarantee/device-bind', key: 'deviceBind', menu: 'device', icon: '⌁' },
      { to: '/guarantee/dev-events', key: 'devEvents', menu: 'alert', icon: '⚠' },
      { to: '/guarantee/access', key: 'accessRecords', menu: 'access', icon: '⌂' },
      { to: '/guarantee/keyring', key: 'keyring', menu: 'person', icon: '⚿' },
      { to: '/guarantee/grants', key: 'grants', menu: 'device', icon: '⇄' }
    ]
  },
  {
    key: 'risk',
    labelKey: 'group.risk',
    icon: '⚠',
    items: [
      { to: '/guarantee/alerts', key: 'alertCenter', menu: 'alert', icon: '⚠' },
      { to: '/guarantee/patrol', key: 'patrol', menu: 'alert', icon: '◎' },
      { to: '/guarantee/house-access', key: 'houseAccess', menu: 'device', icon: '⌂' },
      { to: '/guarantee/credits', key: 'credit', menu: 'credit', icon: '✖' }
    ]
  },
  {
    key: 'system',
    labelKey: 'group.system',
    icon: '☰',
    items: [
      { to: '/guarantee/audit', key: 'audit', menu: 'audit', icon: '✓' },
      { to: '/guarantee/reports', key: 'reports', menu: 'billing', icon: '▤' },
      { to: '/guarantee/gov', key: 'gov', menu: 'gov', icon: '⇪' },
      { to: '/guarantee/orgs', key: 'orgs', menu: 'asset', icon: '▦' },
      { to: '/guarantee/rbac', key: 'rbac', menu: 'config', icon: '♟' },
      { to: '/guarantee/imports', key: 'batchImport', menu: 'config', icon: '⇪' },
      { to: '/guarantee/sys', key: 'sys', menu: 'config', icon: '☰' },
      { to: '/guarantee/help', key: 'help', menu: 'help', icon: '?' }
    ]
  }
]

export const navItems = navGroups.flatMap(g => g.items)
