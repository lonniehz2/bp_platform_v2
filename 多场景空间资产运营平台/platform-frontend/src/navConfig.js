export const navGroups = [
  {
    key: 'workbench',
    labelKey: 'group.workbench',
    icon: '◈',
    items: [
      { to: '/guarantee/dashboard', key: 'dashboard', menu: 'dashboard', icon: '◈' },
      { to: '/search', key: 'search', menu: 'search', icon: '⌕' },
      { to: '/todos', key: 'todos', menu: 'audit', icon: '✓' },
      { to: '/messages', key: 'message', menu: 'message', icon: '✉' }
    ]
  },
  {
    key: 'risk',
    labelKey: 'group.risk',
    icon: '⚠',
    items: [
      { to: '/alerts', key: 'alertCenter', menu: 'alert', icon: '⚠' },
      { to: '/patrol', key: 'patrol', menu: 'alert', icon: '◎' },
      { to: '/arrears', key: 'arrears', menu: 'billing', icon: '!' },
      { to: '/house-access', key: 'houseAccess', menu: 'device', icon: '⌂' },
      { to: '/credits', key: 'credit', menu: 'credit', icon: '✖' },
      { to: '/visits', key: 'visits', menu: 'complaint', icon: '☏' }
    ]
  },
  {
    key: 'guarantee',
    labelKey: 'group.guarantee',
    icon: '♙',
    items: [
      { to: '/guarantee/applications', key: 'applications', menu: 'application', icon: '☷' },
      { to: '/guarantee/waitlist', key: 'waitlist', menu: 'application', icon: '↕' },
      { to: '/guarantee/allocations', key: 'allocations', menu: 'application', icon: '◎' },
      { to: '/publicities', key: 'publicity', menu: 'publicity', icon: '▣' },
      { to: '/guarantee/persons', key: 'person', menu: 'person', icon: '♙' },
      { to: '/annual-reviews', key: 'annualReviews', menu: 'contract', icon: '✓' }
    ]
  },
  {
    key: 'contract',
    labelKey: 'group.contract',
    icon: '▤',
    items: [
      { to: '/guarantee/contracts', key: 'contracts', menu: 'contract', icon: '▤' },
      { to: '/contract-changes', key: 'contractChanges', menu: 'contract', icon: '⇄' },
      { to: '/exchanges', key: 'exchanges', menu: 'contract', icon: '⇄' },
      { to: '/terminations', key: 'terminations', menu: 'contract', icon: '✖' },
      { to: '/houses', key: 'houses', menu: 'asset', icon: '▦' },
      { to: '/spaces', key: 'spaces', menu: 'asset', icon: '▤' },
      { to: '/house-calendar', key: 'calendar', menu: 'calendar', icon: '▦' },
      { to: '/short-rent', key: 'shortrent', menu: 'shortrent', icon: '⌂' }
    ]
  },
  {
    key: 'finance',
    labelKey: 'group.finance',
    icon: '¥',
    items: [
      { to: '/guarantee/billing', key: 'bills', menu: 'billing', icon: '¥' },
      { to: '/deposits', key: 'deposits', menu: 'billing', icon: '◫' },
      { to: '/subsidies', key: 'subsidies', menu: 'billing', icon: '◫' },
      { to: '/cashflow', key: 'cashflow', menu: 'billing', icon: '↕' },
      { to: '/fee-items', key: 'fee', menu: 'billing', icon: '≡' },
      { to: '/meter-readings', key: 'meterReadings', menu: 'asset', icon: '◉' },
      { to: '/energy', key: 'energy', menu: 'energy', icon: '▤' }
    ]
  },
  {
    key: 'access',
    labelKey: 'group.access',
    icon: '⌘',
    items: [
      { to: '/guarantee/devices', key: 'devices', menu: 'device', icon: '⌘' },
      { to: '/device-bind', key: 'deviceBind', menu: 'device', icon: '⌁' },
      { to: '/dev-events', key: 'devEvents', menu: 'alert', icon: '⚠' },
      { to: '/access', key: 'accessRecords', menu: 'access', icon: '⌂' },
      { to: '/keyring', key: 'keyring', menu: 'person', icon: '⚿' },
      { to: '/grants', key: 'grants', menu: 'device', icon: '⇄' }
    ]
  },
  {
    key: 'service',
    labelKey: 'group.service',
    icon: '⚒',
    items: [
      { to: '/work-orders', key: 'workOrders', menu: 'service', icon: '⚒' },
      { to: '/complaints', key: 'complaints', menu: 'complaint', icon: '☏' },
      { to: '/appeals', key: 'appeals', menu: 'complaint', icon: '☏' }
    ]
  },
  {
    key: 'system',
    labelKey: 'group.system',
    icon: '☰',
    items: [
      { to: '/reports', key: 'reports', menu: 'billing', icon: '▤' },
      { to: '/gov', key: 'gov', menu: 'gov', icon: '⇪' },
      { to: '/orgs', key: 'orgs', menu: 'asset', icon: '▦' },
      { to: '/rbac', key: 'rbac', menu: 'config', icon: '♟' },
      { to: '/sys', key: 'sys', menu: 'config', icon: '☰' },
      { to: '/open-apps', key: 'open', menu: 'open', icon: '⇄' },
      { to: '/help', key: 'help', menu: 'help', icon: '?' },
      { to: '/translations', key: 'translations', menu: 'help', icon: '文' },
      { to: '/platform-info', key: 'platformInfo', menu: 'help', icon: 'ⓘ' }
    ]
  }
]

export const navItems = navGroups.flatMap(g => g.items)
