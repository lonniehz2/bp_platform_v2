export const HELP_VERSION_EN = 'v1.0 (2026-11-01)'
export const HELP_PDF_EN = '/docs/user-manual-en.pdf'

/** Concise English guide; full Chinese manual remains available in ZH. */
export const HELP_SECTIONS_EN = [
  {
    id: 'start',
    title: 'Quick start',
    blocks: [
      { type: 'p', text: 'This guide covers the English interface of the Housing Operations Platform.' },
      { type: 'table', head: ['I want to...', 'Where to go'], rows: [
        ['Create a contract', 'Contracts & Leasing → Contracts → New Contract'],
        ['Issue bills in batch', 'Billing & Finance → Bills → Batch Bill'],
        ['Register and allocate a payment', 'Billing & Finance → Bills → Register Payment → Allocate'],
        ['Terminate a lease', 'Contracts & Leasing → Terminations → Inspect → Settle'],
        ['Translate a housing name', 'System & Data → Data Translations']
      ] },
      { type: 'note', text: 'The language selector is in the top-right corner. Your choice is remembered for the next sign-in.' }
    ]
  },
  {
    id: 'signin',
    title: 'Sign in and language',
    blocks: [
      { type: 'ol', items: [
        'Enter the platform code, username and password.',
        'Select EN or ZH in the top-right language selector.',
        'After signing in, the interface, menus, tables, dialogs and validation messages use the selected language.'
      ] },
      { type: 'p', text: 'Business names (organizations, housing, persons, fee items) are translated only when a translation has been maintained.' }
    ]
  },
  {
    id: 'dashboard',
    title: 'Operations Dashboard',
    blocks: [
      { type: 'p', text: 'The dashboard shows housing mix and occupancy, receivables and collection rate, subsidies, device events, alerts, work orders, applications and deposits.' },
      { type: 'ul', items: [
        'All / My Organization changes the data scope.',
        'Refresh reloads all indicators.',
        'Full Screen opens the operations wall display.',
        'Metric Details lists metric code, current value and description.'
      ] }
    ]
  },
  {
    id: 'housing',
    title: 'Housing, spaces and persons',
    blocks: [
      { type: 'h3', text: 'Housing' },
      { type: 'p', text: 'Search by organization, code or name, status and type. Create housing with organization, space node, code, name, type, building area and rent standard.' },
      { type: 'p', text: 'Occupancy shows the active contract, lease term, lessee, phone, occupant count and cohabitants.' },
      { type: 'h3', text: 'Persons and eligibility' },
      { type: 'p', text: 'Maintain person profiles, identity verification and eligibility files. An application requires a verified identity; approval requires an eligibility file.' },
      { type: 'p', text: 'Qualification checks income level, property ownership and talent validity. Exiting a person closes the eligibility file and removes the person from the waiting queue.' }
    ]
  },
  {
    id: 'contract',
    title: 'Applications and contracts',
    blocks: [
      { type: 'p', text: 'Applications move through Submitted → Accepted → Reviewing → Approved or Rejected. Every review step is kept in Review History.' },
      { type: 'p', text: 'Contracts support create, submit for signing, sign, renew, change, switch housing and terminate.' },
      { type: 'ol', items: [
        'Create a contract or use Quick Signing.',
        'Submit it for signing, then sign.',
        'Use Change for rent or term changes; use Termination to end a lease.',
        'Renew before the lease end date to avoid expiry.'
      ] },
      { type: 'note', text: 'Termination and change operations keep the original contract and create an audit trail.' }
    ]
  },
  {
    id: 'billing',
    title: 'Billing and payments',
    blocks: [
      { type: 'h3', text: 'Fee items and rules' },
      { type: 'p', text: 'A fee item defines the billing method: fixed, by area, by unit, by person, by bed, by night or meter. Billing rules support standard, tiered, discount and exemption pricing.' },
      { type: 'h3', text: 'Bills' },
      { type: 'p', text: 'Generate bills one by one, in batch, by meter reading or by allocation. A bill stores amount, paid amount, waived amount, payable amount, due date and status.' },
      { type: 'h3', text: 'Payments, deposits and subsidies' },
      { type: 'p', text: 'Register a payment, then allocate it to bills. Deposits support receive, deduct and refund. Subsidies support batch issue, bank transfer or rent offset.' },
      { type: 'h3', text: 'Cash flow' },
      { type: 'p', text: 'Cash Flow shows income and expense flows, reconciliation against channels and payment confirmation.' }
    ]
  },
  {
    id: 'energy',
    title: 'Metering and energy',
    blocks: [
      { type: 'p', text: 'Maintain meters by space and fee item. Enter manual readings or read from IoT; meter readings feed meter-based bills.' },
      { type: 'p', text: 'Monthly Allocation splits a building meter by occupancy days and person-days. Policy sets whether vacant-bed cost is borne by the operator or by occupants.' },
      { type: 'p', text: 'Energy Analysis compares total and submeter usage and flags excessive differences.' }
    ]
  },
  {
    id: 'service',
    title: 'Service, devices and access',
    blocks: [
      { type: 'p', text: 'Work orders support assignment, acceptance, completion, SLA and inspection plans. Alerts support handling, escalation and conversion to work orders.' },
      { type: 'p', text: 'Devices show online status, battery and events. Bind devices to housing spaces; residents inherit access through the space chain.' },
      { type: 'p', text: 'Keyrings bind persons to face, fingerprint, palm vein, password, card, ID card or QR credentials. Access grants can be reconciled against IoT and audited.' }
    ]
  },
  {
    id: 'system',
    title: 'System and permissions',
    blocks: [
      { type: 'p', text: 'Organizations form a tree used for data scope. Users are assigned roles; roles carry data scope and permission codes. Administrators have all permissions.' },
      { type: 'p', text: 'System Support provides audit logs, data dictionaries and system parameters. The Platform Console creates platforms and initial administrators.' }
    ]
  },
  {
    id: 'translations',
    title: 'Data translations',
    blocks: [
      { type: 'p', text: 'Open System & Data → Data Translations. Choose the resource type, enter the resource ID and the English name, then save.' },
      { type: 'ul', items: [
        'Resource types: organization, housing, person, space, fee item and device.',
        'Only the name field is translated. Codes, amounts and dates are not changed.',
        'The translation applies automatically to lists and detail pages in English.'
      ] },
      { type: 'note', text: 'Business data is not machine translated; maintain translations for names that users need to read in English.' }
    ]
  },
  {
    id: 'faq',
    title: 'Common questions',
    blocks: [
      { type: 'faq', items: [
        { q: 'The interface is English but some names are still Chinese.', a: 'Maintain those names in Data Translations.' },
        { q: 'A menu is missing.', a: 'The role lacks the required permission code. Ask an administrator.' },
        { q: 'A bill cannot be generated.', a: 'Check the fee item, billing rule, contract status and billing period.' },
        { q: 'A door cannot be opened.', a: 'Check the access grant, keyring status and IoT reconciliation differences.' },
        { q: 'Where can I see who changed a record?', a: 'Use Audit Log, Grant Audit and Work Order Log.' }
      ] }
    ]
  }
]
