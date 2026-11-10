export const navGroups = [
  {
    key: 'workbench',
    labelKey: 'group.workbench',
    icon: '◈',
    items: [
      { to: '/guarantee/dashboard', key: 'dashboard', menu: 'dashboard', icon: '◈' },
      { to: '/guarantee/search', key: 'search', menu: 'search', icon: '⌕' },
      { to: '/guarantee/todos', key: 'todos', menu: 'todos', icon: '✓' },
      { to: '/guarantee/messages', key: 'message', menu: 'message', icon: '✉' }
    ]
  },
  {
    key: 'application',
    labelKey: 'group.application',
    icon: '☷',
    items: [
      { to: '/guarantee/applications', key: 'applications', menu: 'applications', icon: '☷' },
      { to: '/guarantee/persons', key: 'person', menu: 'person', icon: '♙' },
      { to: '/guarantee/qualification', key: 'qualification', menu: 'qualification', icon: '✓' }
    ]
  },
  {
    key: 'waitlist',
    labelKey: 'group.waitlist',
    icon: '↕',
    items: [
      { to: '/guarantee/waitlist', key: 'waitlist', menu: 'waitlist', icon: '↕' },
      { to: '/guarantee/allocations', key: 'allocations', menu: 'allocations', icon: '◎' },
      { to: '/guarantee/publicities', key: 'publicities', menu: 'publicities', icon: '▣' }
    ]
  },
  {
    key: 'contract',
    labelKey: 'group.contract',
    icon: '▤',
    items: [
      { to: '/guarantee/contracts', key: 'contracts', menu: 'contracts', icon: '▤' },
      { to: '/guarantee/contract-changes', key: 'contractChanges', menu: 'contractChanges', icon: '⇄' },
      { to: '/guarantee/exchanges', key: 'exchanges', menu: 'exchanges', icon: '⇄' },
      { to: '/guarantee/terminations', key: 'terminations', menu: 'terminations', icon: '✖' }
    ]
  },
  {
    key: 'finance',
    labelKey: 'group.finance',
    icon: '¥',
    items: [
      { to: '/guarantee/billing', key: 'billing', menu: 'billing', icon: '¥' },
      { to: '/guarantee/deposits', key: 'deposits', menu: 'deposits', icon: '◫' },
      { to: '/guarantee/subsidies', key: 'subsidies', menu: 'subsidies', icon: '◫' },
      { to: '/guarantee/cashflow', key: 'cashflow', menu: 'cashflow', icon: '↕' },
      { to: '/guarantee/fee-items', key: 'fee', menu: 'fee', icon: '≡' },
      { to: '/guarantee/arrears', key: 'arrears', menu: 'arrears', icon: '!' }
    ]
  },
  {
    key: 'asset',
    labelKey: 'group.asset',
    icon: '▦',
    items: [
      { to: '/guarantee/assets', key: 'asset', menu: 'asset', icon: '▦' },
      { to: '/guarantee/listings', key: 'listings', menu: 'listings', icon: '⌂' },
      { to: '/guarantee/houses', key: 'houses', menu: 'houses', icon: '▦' },
      { to: '/guarantee/spaces', key: 'spaces', menu: 'spaces', icon: '▤' },
      { to: '/guarantee/house-calendar', key: 'calendar', menu: 'calendar', icon: '▦' },
      { to: '/guarantee/short-rent', key: 'shortrent', menu: 'shortrent', icon: '⌂' }
    ]
  },
  {
    key: 'service',
    labelKey: 'group.service',
    icon: '⚒',
    items: [
      { to: '/guarantee/work-orders', key: 'workOrders', menu: 'workOrders', icon: '⚒' },
      { to: '/guarantee/complaints', key: 'complaints', menu: 'complaints', icon: '☏' },
      { to: '/guarantee/appeals', key: 'appeals', menu: 'appeals', icon: '☏' },
      { to: '/guarantee/visits', key: 'visits', menu: 'visits', icon: '☏' }
    ]
  },
  {
    key: 'access',
    labelKey: 'group.access',
    icon: '⌘',
    items: [
      { to: '/guarantee/devices', key: 'devices', menu: 'devices', icon: '⌘' },
      { to: '/guarantee/device-bind', key: 'deviceBind', menu: 'deviceBind', icon: '⌁' },
      { to: '/guarantee/dev-events', key: 'devEvents', menu: 'devEvents', icon: '⚠' },
      { to: '/guarantee/access', key: 'accessRecords', menu: 'accessRecords', icon: '⌂' },
      { to: '/guarantee/keyring', key: 'keyring', menu: 'keyring', icon: '⚿' },
      { to: '/guarantee/grants', key: 'grants', menu: 'grants', icon: '⇄' }
    ]
  },
  {
    key: 'risk',
    labelKey: 'group.risk',
    icon: '⚠',
    items: [
      { to: '/guarantee/alerts', key: 'alertCenter', menu: 'alertCenter', icon: '⚠' },
      { to: '/guarantee/patrol', key: 'patrol', menu: 'patrol', icon: '◎' },
      { to: '/guarantee/house-access', key: 'houseAccess', menu: 'houseAccess', icon: '⌂' },
      { to: '/guarantee/credits', key: 'credit', menu: 'credit', icon: '✖' }
    ]
  },
  {
    key: 'system',
    labelKey: 'group.system',
    icon: '☰',
    items: [
      { to: '/guarantee/audit', key: 'audit', menu: 'audit', icon: '✓' },
      { to: '/guarantee/reports', key: 'reports', menu: 'reports', icon: '▤' },
      { to: '/guarantee/gov', key: 'gov', menu: 'gov', icon: '⇪' },
      { to: '/guarantee/orgs', key: 'orgs', menu: 'orgs', icon: '▦' },
      { to: '/guarantee/rbac', key: 'rbac', menu: 'rbac', icon: '♟' },
      { to: '/guarantee/imports', key: 'batchImport', menu: 'batchImport', icon: '⇪' },
      { to: '/guarantee/sys', key: 'sys', menu: 'sys', icon: '☰' },
      { to: '/guarantee/help', key: 'help', menu: 'help', icon: '?' }
    ]
  }
]

export const navItems = navGroups.flatMap(g => g.items)
