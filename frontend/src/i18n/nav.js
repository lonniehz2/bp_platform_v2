import { getLocale } from './index'

export const GROUP_EN = {
  工作台: 'Workspace',
  保障与资格: 'Eligibility',
  合同与租赁: 'Contracts & Leasing',
  收费与账务: 'Billing & Finance',
  计量与能耗: 'Metering & Energy',
  房源与空间: 'Housing & Space',
  设备与通行: 'Devices & Access',
  服务与监督: 'Service & Supervision',
  系统与数据: 'System & Data',
  其他: 'Other'
}

export const PAGE_EN = {
  运营驾驶舱: 'Operations Dashboard',
  申请受理: 'Applications',
  配租摇号: 'Allocation & Lottery',
  合同台账: 'Contracts',
  抄表管理: 'Meter Readings',
  能耗分析: 'Energy Analysis',
  能耗分摊: 'Utility Allocation',
  账单与缴费: 'Bills & Payments',
  报表导出: 'Reports',
  设备管理: 'Devices',
  设备绑定: 'Device Binding',
  设备告警: 'Device Alerts',
  IoT日对账: 'IoT Daily Reconciliation',
  IoT监控: 'IoT Monitoring',
  IoT联调工具: 'IoT Tools',
  设备指令: 'Device Commands',
  通行记录: 'Access Records',
  组织机构: 'Organizations',
  房源台账: 'Housing',
  我的待办: 'My Todos',
  消息中心: 'Messages',
  工单维保: 'Work Orders',
  告警处理: 'Alert Handling',
  钥匙包: 'Key Packages',
  通行授权: 'Access Grants',
  人员档案: 'Persons',
  空间层级: 'Spaces',
  退租管理: 'Terminations',
  申诉管理: 'Appeals',
  信用惩戒: 'Credit Actions',
  换房管理: 'Exchanges',
  投诉管理: 'Complaints',
  入户走访: 'Home Visits',
  短租订单: 'Short-term Orders',
  日房态: 'Daily Availability',
  监管报送: 'Regulatory Reporting',
  开放平台: 'Open Platform',
  用户与权限: 'Users & Permissions',
  系统支撑: 'System Support',
  业务数据翻译: 'Data Translations',
  补贴管理: 'Subsidies',
  押金与退款: 'Deposits & Refunds',
  公示管理: 'Publicity',
  轮候管理: 'Waitlist',
  计费项目: 'Fee Items',
  催缴管理: 'Dunning',
  资金流水: 'Cash Flow',
  合同变更: 'Contract Changes',
  年审复核: 'Annual Review',
  运维操作台: 'Operations Console',
  平台信息: 'Platform Info',
  使用帮助: 'Help',
  扩展操作台: 'Extended Console',
  用户管理: 'Users',
  角色管理: 'Roles',
  权限清单: 'Permissions',
  审计日志: 'Audit Logs',
  数据字典: 'Dictionaries',
  系统参数: 'System Config',
  人员状态: 'Person Status',
  房源状态: 'Housing Status',
  工单流程: 'Work Order Flow',
  保障档案: 'Eligibility Profile',
  实名核验: 'Identity Verification',
  消息待办: 'Message Todos',
  告警规则: 'Alert Rules',
  权限管理: 'Permissions',
  授权撤销: 'Grant Revocation'
}

export const PAGE_DESC_EN = {
  '/dashboard': 'Live overview of housing, billing, applications and devices',
  '/contracts': 'Sign, change, exchange and terminate contracts',
  '/bills': 'Generate bills, record payments and handle arrears',
  '/energy': 'Monthly utility usage, allocation and variance alerts'
}

export function trGroup(zh) {
  return getLocale() === 'en-US' ? (GROUP_EN[zh] || zh) : zh
}

export function trPage(zh) {
  return getLocale() === 'en-US' ? (PAGE_EN[zh] || zh) : zh
}

export function trPageDesc(path, zh) {
  return getLocale() === 'en-US' ? (PAGE_DESC_EN[path] || zh) : zh
}
