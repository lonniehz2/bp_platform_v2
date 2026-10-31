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
  // 通用
  ENABLED: 'Enabled',
  DISABLED: 'Disabled',
  YES: 'Yes',
  NO: 'No',
  MANUAL: 'Manual',
  AUTO: 'Auto',
  NONE: 'None',
  ALL: 'All',
  OTHER: 'Other'
}

export function trField(key, zh) {
  if (getLocale() !== 'en-US') return zh
  return FIELD_LABEL_EN[key] || zh
}

export function trEnum(value, zh) {
  if (getLocale() !== 'en-US') return zh
  return ENUM_LABEL_EN[String(value)] || zh
}
