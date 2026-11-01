import { getLocale } from './index'

/**
 * 展示层英文标签。
 *
 * 说明：现有 pages 通过 labelOf()/enumLabel() 统一取文案，先覆盖合同、账单、
 * 房源、缴费等高频字段；未登记的字段回退中文，避免一次性改动所有页面。
 * 后续新增字段应优先补这里，或在页面使用 t('domain.key')。
 */
export const FIELD_LABEL_EN = {
  // 合同
  contractNo: 'Contract No.',
  contractType: 'Contract Type',
  contractStatus: 'Status',
  lesseeName: 'Lessee',
  lesseePhone: 'Phone',
  lesseePersonId: 'Lessee ID',
  houseName: 'Housing',
  houseAddress: 'Address',
  houseCode: 'Housing Code',
  building: 'Building',
  orgName: 'Organization',
  area: 'Area',
  monthlyRent: 'Monthly Rent',
  lessorName: 'Lessor',
  securityType: 'Security Type',
  oldHouseName: 'Original Housing',
  oldLease: 'Original Lease',
  newMonthlyRent: 'New Monthly Rent',
  newLeaseEnd: 'New Lease End',
  effectiveDate: 'Effective Date',
  changeReason: 'Change Reason',
  changeType: 'Change Type',
  exchangeReason: 'Exchange Reason',
  targetHouse: 'Target Housing',
  leaseTerm: 'Lease Term',
  leaseChange: 'Lease Change',
  signDate: 'Sign Date',
  signMethod: 'Sign Method',
  signFileUrl: 'Sign File URL',
  signFlowId: 'Sign Flow ID',
  terminationType: 'Termination Type',
  terminationReason: 'Termination Reason',
  prevReading: 'Previous Reading',
  readDate: 'Read Date',
  readCount: 'Read Count',
  explain: 'Calculation',
  skipReason: 'Skip Reason',
  targetBill: 'Target Bill',
  billPayable: 'Bill Payable',
  payDue: 'Payment Due',
  availableAmount: 'Available Amount',
  allocateTime: 'Allocation Time',
  allocateAmount: 'Allocated Amount',
  waiveReason: 'Waive Reason',
  waiveAmount: 'Waive Amount',
  totalAmount: 'Total Amount',
  transactionNo: 'Transaction No.',
  channel: 'Channel',
  balance: 'Balance',
  value: 'Value',
  personId: 'Person ID',
  houseCode: 'Housing Code',
  unknownSource: 'Unknown Source',
  item: 'Item',
  month: 'Month',
  allocationMode: 'Allocation Mode',
  ruleName: 'Billing Rule',
  result: 'Result',
  cash: 'Cash',
  alipay: 'Alipay',
  wechat: 'WeChat',
  bankTransfer: 'Bank Transfer',


  unitPrice: 'Unit Price',
  rentUnit: 'Rent Unit',
  depositAmount: 'Deposit',
  leaseStart: 'Lease Start',
  leaseEnd: 'Lease End',
  signDate: 'Sign Date',
  paymentCycle: 'Payment Cycle',
  paymentDay: 'Payment Day',
  subsidyAmount: 'Subsidy',
  actualPay: 'Net Payable',
  billingPersonCount: 'Billing Persons',
  billingBedCount: 'Billing Beds',
  terminateDate: 'Termination Date',
  changeType: 'Change Type',
  oldRent: 'Old Rent',
  newRent: 'New Rent',
  effectiveDate: 'Effective Date',
  reason: 'Reason',
  remark: 'Remark',
  // 账单 / 收款
  billNo: 'Bill No.',
  billPeriod: 'Billing Period',
  billStatus: 'Status',
  billAmount: 'Amount',
  discountAmount: 'Discount',
  lateFee: 'Late Fee',
  paidAmount: 'Paid',
  waivedAmount: 'Waived',
  payableAmount: 'Payable',
  dueDate: 'Due Date',
  payerName: 'Payer',
  feeItemName: 'Fee Item',
  overdueDays: 'Overdue Days',
  paymentNo: 'Payment No.',
  payTime: 'Payment Time',
  payMethod: 'Payment Method',
  payAmount: 'Payment Amount',
  remainAmount: 'Balance',
  reconciledAmount: 'Reconciled',
  allocateAmount: 'Allocated',
  // 房源 / 空间
  spaceName: 'Space',
  spaceType: 'Space Type',
  fullName: 'Full Name',
  houseStatus: 'Housing Status',
  houseType: 'Housing Type',
  securityType: 'Security Type',
  rentStandard: 'Rent Standard',
  // 人员
  personName: 'Name',
  personStatus: 'Status',
  idNumber: 'ID No.',
  phone: 'Phone',
  // 组织 / 系统
  orgCode: 'Org Code',
  orgType: 'Org Type',
  parentName: 'Parent',
  status: 'Status',
  createTime: 'Created At',
  updateTime: 'Updated At',
  // 能耗
  meterName: 'Meter',
  meterScope: 'Scope',
  reading: 'Reading',
  prevReading: 'Previous',
  usage: 'Usage',
  usageAmount: 'Usage',
  readDate: 'Read Date',
  totalUsage: 'Total Usage',
  totalAmount: 'Total Amount',
  operatorBearAmount: 'Operator Share'
}

export const ENUM_LABEL_EN = {
  // 合同
  DRAFT: 'Draft',
  PENDING: 'Pending',
  APPROVED: 'Approved',
  EFFECTIVE: 'Effective',
  ACTIVE: 'Active',
  RENEWING: 'Renewing',
  RENEWED: 'Renewed',
  TERMINATED: 'Terminated',
  EXPIRED: 'Expired',
  CANCELLED: 'Cancelled',
  REJECTED: 'Rejected',
  COMPLETED: 'Completed',
  // 账单 / 收款
  UNPAID: 'Unpaid',
  PARTIAL: 'Partially Paid',
  PAID: 'Paid',
  OVERDUE: 'Overdue',
  WAIVED: 'Waived',
  VOID: 'Void',
  REFUNDED: 'Refunded',
  SUCCESS: 'Success',
  FAILED: 'Failed',
  PENDING_PAY: 'Pending Payment',
  // 押金
  HELD: 'Held',
  PARTIAL_REFUND: 'Partially Refunded',
  DEDUCTED: 'Deducted',
  TRANSFERRED: 'Transferred',

  ASSIGNED: 'Assigned',
  FINISHED: 'Completed',
  MAINTENANCE: 'Under Maintenance',
  DRAFT_REVIEW: 'Pending Review',
  SAFETY: 'Safety Hazard',
  TEST: 'Test Data',
  TENANT_APP: 'Tenant App',
  VERIFIED: 'Verified',
  UNVERIFIED: 'Unverified',
  VERIFYING: 'Verifying',
  WIFI_LOCK: 'Wireless Lock',
  SUBMIT: 'Submitted',
  OBJECTION: 'Objection',
  ON_TIME: 'On Time',
  PAPER: 'Paper',
  ELECTRONIC: 'E-Signature',
  FACE: 'Face',
  RECONCILED: 'Reconciled',
  UNRECONCILED: 'Unreconciled',
  RECONCILING: 'Reconciling',
  DIFF: 'Difference',
  ROUTINE: 'Routine Visit',
  VERIFY: 'Eligibility Check',
  VACANCY: 'Vacancy Check',
  ALERT: 'Alert Check',
  APPLYING: 'Applying',
  APPROVING: 'Approving',
  REVIEWING: 'Reviewing',
  SUBMITTED: 'Submitted',
  ACCEPTED: 'Accepted',
  SUPPLEMENT: 'Supplement',
  DONE: 'Done',
  READ: 'Read',
  INFO: 'Info',
  WARNING: 'Warning',
  CRITICAL: 'Critical',
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
  NORMAL: 'Normal',
  URGENT: 'Urgent',
  PENDING_ALLOC: 'Pending Allocation',
  ALLOCATED: 'Allocated',
  VACANT: 'Vacant',
  OCCUPIED: 'Occupied',
  SENT: 'Sent',
  TIMEOUT: 'Timeout',
  CHECKED_IN: 'Checked In',
  CHECKED_OUT: 'Checked Out',
  CONFIRMED: 'Confirmed',
  MATCHED: 'Matched',
  HANDLED: 'Handled',
  IGNORED: 'Ignored',
  LOCAL_MISSING: 'Local Missing',
  IOT_EXTRA: 'IoT Extra',
  // 通用
  ENABLED: 'Enabled',
  DISABLED: 'Disabled',
  YES: 'Yes',
  NO: 'No',
  AREA_MONTH: 'Per sqm / month',
  HOUSE_MONTH: 'Per unit / month',
  BED_MONTH: 'Per bed / month',
  HOUSE_NIGHT: 'Per unit / night',
  BED_NIGHT: 'Per bed / night',
  OFFLINE: 'Offline Paper',
  ESIGN: 'E-Signature',
  CA: 'CA Certificate',
  AGREEMENT: 'Mutual Termination',
  BREACH: 'Breach Termination',
  EXPIRE: 'Expiry Termination',
  RENT_ADJUST: 'Rent Adjustment',
  RENEW: 'Renewal',
  OTHER: 'Other',
  CASH: 'Cash',
  BANK: 'Bank Transfer',
  WECHAT: 'WeChat Pay',
  ALIPAY: 'Alipay',
  ECONOMIC: 'Affordable Housing',
  MONTH: 'Monthly',
  QUARTER: 'Quarterly',
  HALF_YEAR: 'Semi-annual',
  YEAR: 'Annual',
  PUBLIC_RENTAL: 'Public Rental',
  TALENT: 'Talent Apartment',
  PUBLIC: 'Public Rental',
  AFFORDABLE: 'Affordable Rental',
  LOW_RENT: 'Low-rent Housing',
  METER: 'Meter Reading',
  SHARED: 'Shared Allocation',
  SHORT_RENT: 'Short-term Order',
  MANUAL: 'Manual',
  AUTO: 'Auto',
  NONE: 'None',
  ALL: 'All',
  OTHER: 'Other'
}

const ACRONYMS = {
  ID: 'ID', SLA: 'SLA', IOT: 'IoT', IP: 'IP', URL: 'URL', API: 'API',
  CSV: 'CSV', QR: 'QR', CA: 'CA', OCR: 'OCR', APP: 'App', UI: 'UI'
}

/** 把 camelCase / SNAKE_CASE 键或枚举码转为可读英文。 */
export function humanizeKey(value) {
  const raw = String(value ?? '').trim()
  if (!raw) return ''
  return raw
    .replace(/[_-]+/g, ' ')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/\s+/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((w) => {
      const up = w.toUpperCase()
      if (ACRONYMS[up]) return ACRONYMS[up]
      return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()
    })
    .join(' ')
}

export function trField(key, zh) {
  if (getLocale() !== 'en-US') return zh
  return FIELD_LABEL_EN[key] || humanizeKey(key) || zh
}

export function trEnum(value, zh) {
  if (getLocale() !== 'en-US') return zh
  const v = String(value)
  return ENUM_LABEL_EN[v] || (v ? humanizeKey(v) : zh)
}
