import { watch } from 'vue'
import zh from './legacy-locales/zh-CN'
import en from './legacy-locales/en-US'

/**
 * 过渡层：复用旧保障房系统的中英文词条，对页面静态文案做精确匹配翻译。
 * 仅翻译与旧词条完全一致的中文文本，不翻译人员姓名、编码、金额等业务数据。
 * 后续可逐步替换为显式 t('key')。
 */
function walk(zhNode, enNode, out) {
  if (!zhNode || !enNode || typeof zhNode !== 'object' || typeof enNode !== 'object') return
  for (const key of Object.keys(zhNode)) {
    const zhItem = zhNode[key]
    const enItem = enNode[key]
    if (typeof zhItem === 'string') {
      if (typeof enItem === 'string') {
        const zhText = zhItem.trim()
        const enText = enItem.trim()
        if (zhText && enText && zhText !== enText && !zhText.includes('{') && !out.has(zhText)) {
          out.set(zhText, enText)
        }
      }
    } else if (zhItem && typeof zhItem === 'object') {
      walk(zhItem, enItem, out)
    }
  }
}

const dictionary = new Map()
walk(zh, en, dictionary)

const extra = {
  '项目与资产': 'Projects & Assets',
  '客户与人员': 'Customers & People',
  '申请与轮候': 'Applications & Waitlist',
  '合同与租赁': 'Contracts & Leases',
  '合同变更': 'Contract Changes',
  '资格复核': 'Qualification Review',
  '收费与账务': 'Billing & Finance',
  '押金与补贴': 'Deposits & Subsidies',
  '欠费清单': 'Arrears',
  '资金流水': 'Cash Flow',
  '运营报表': 'Reports',
  '计量与能耗': 'Meters & Energy',
  '服务与工单': 'Service Orders',
  '访客通行': 'Visitor Access',
  '投诉与申诉': 'Complaints & Appeals',
  '设备与授权': 'Devices & Access',
  '审批中心': 'Approval Center',
  '菜单与角色': 'Menus & Roles',
  '迁移异常': 'Migration Exceptions',
  '设为当前': 'Set Current',
  '创建项目': 'Create Project',
  '新增空间': 'Add Space',
  '新增人员': 'Add Person',
  '新增表计': 'Add Meter',
  '保存抄表': 'Save Reading',
  '新增工单': 'New Order',
  '登记访客': 'Register Visitor',
  '新增记录': 'New Record',
  '导出账单 CSV': 'Export Bills CSV',
  '未结清账单': 'Unpaid Bills',
  '欠费金额': 'Outstanding',
  '逾期账单': 'Overdue Bills',
  '收款笔数': 'Payments',
  '收款金额': 'Received',
  '当前项目': 'Current Project',
  '全部收款': 'All Payments',
  '账单状态分布': 'Bill Status Distribution',
  '去收款': 'Collect Payment',
  '处理记录': 'Handle Record',
  '处理结果': 'Result'
}
Object.assign(extra, {
  "项目数": "Projects",
  "当前租户全部项目": "All projects in tenant",
  "保障房申请": "Guarantee Applications",
  "待审": "Pending Review",
  "生效合同": "Active Contracts",
  "合同总数": "Total Contracts",
  "应收账单": "Receivable Bills",
  "未结清": "Unpaid",
  "设备资产": "Device Assets",
  "业务台账": "Business Ledger",
  "当前项目": "Current Project",
  "项目名称": "Project Name",
  "经营模式": "Business Mode",
  "空间模板": "Space Template",
  "最近合同": "Recent Contracts",
  "查看全部": "View All",
  "待处理账单": "Bills to Process",
  "加载中…": "Loading…",
  "暂无项目，请先到“项目与资产”创建项目。": "No project. Create one in Projects & Assets.",
  "新增": "Add",
  "创建": "Create",
  "提交": "Submit",
  "审核通过": "Approve",
  "进入轮候": "Join Waitlist",
  "配租": "Allocate",
  "申请编号": "Application No.",
  "申请人": "Applicant",
  "家庭人数": "Family Size",
  "创建申请": "Create Application",
  "申请列表": "Applications",
  "暂无申请": "No applications",
  "轮候与配租": "Waitlist & Allocation",
  "轮候记录": "Waitlist Record",
  "请选择": "Please select",
  "排队号": "Queue No.",
  "暂无轮候": "No waitlist",
  "账单号": "Bill No.",
  "承租人": "Tenant",
  "周期": "Period",
  "应付": "Payable",
  "已收": "Received",
  "欠费": "Outstanding",
  "欠费清单": "Arrears",
  "去收款": "Collect Payment",
  "未结清账单": "Unpaid Bills",
  "按应付减已收": "Payable minus received",
  "逾期账单": "Overdue Bills",
  "状态 OVERDUE": "Status OVERDUE",
  "暂无欠费": "No arrears",
  "收款": "Payment",
  "按应付金额收款，自动生成收据": "Collect payable amount and issue receipt",
  "账单": "Bill",
  "收款金额": "Payment Amount",
  "方式": "Method",
  "确认收款": "Confirm Payment",
  "账单列表": "Bills",
  "应收": "Receivable",
  "账单金额": "Bill Amount",
  "补贴": "Subsidy",
  "收款记录": "Payments",
  "收据随收款自动生成": "Receipt is generated automatically",
  "暂无收款": "No payments",
  "收款单号": "Payment No.",
  "收据": "Receipt",
  "时间": "Time",
  "收款笔数": "Payments",
  "全部收款": "All Payments",
  "资金流水": "Cash Flow",
  "收款与收据": "Payments & Receipts",
  "保障房合同": "Guarantee Contracts",
  "合同创建与账单生成": "Create contracts and generate bills",
  "合同编号": "Contract No.",
  "开始日期": "Start Date",
  "结束日期": "End Date",
  "月租金": "Monthly Rent",
  "押金": "Deposit",
  "创建合同": "Create Contract",
  "合同列表": "Contracts",
  "生效合同可生成租金账单": "Active contracts can generate rent bills",
  "暂无合同": "No contracts",
  "生成租金账单": "Generate Rent Bill",
  "补贴会在账单生成时自动抵扣": "Subsidy is deducted when the bill is generated",
  "周期开始": "Period Start",
  "周期结束": "Period End",
  "金额": "Amount",
  "生成账单": "Generate Bill",
  "合同": "Contract",
  "合同变更": "Contract Changes",
  "租金/期限/换房/退租": "Rent / Term / Exchange / Terminate",
  "新建变更": "New Change",
  "提交后进入平台审批": "Submit to workflow",
  "类型": "Type",
  "租金变更": "Rent Change",
  "期限变更": "Term Change",
  "换房": "Exchange",
  "退租": "Terminate",
  "新租金": "New Rent",
  "新房屋": "New House",
  "新结束日期": "New End Date",
  "生效日期": "Effective Date",
  "原因": "Reason",
  "创建变更": "Create Change",
  "变更记录": "Change Records",
  "暂无变更": "No changes",
  "押金与补贴": "Deposits & Subsidies",
  "按合同管理押金和租金补贴": "Manage deposit and rent subsidy by contract",
  "已退": "Refunded",
  "收取金额": "Amount to Collect",
  "收取押金": "Collect Deposit",
  "退还金额": "Refund Amount",
  "退还押金": "Refund Deposit",
  "流水": "Transactions",
  "租金补贴": "Rent Subsidy",
  "金额/月": "Amount / Month",
  "开始": "Start",
  "结束": "End",
  "新增补贴": "Add Subsidy",
  "暂无补贴": "No subsidies",
  "设备业务资产": "Device Assets",
  "业务台账，不涉及 IOT 控制": "Business ledger, no IoT control",
  "设备编码": "Device Code",
  "设备名称": "Device Name",
  "设备类型": "Device Type",
  "门锁": "Lock",
  "水电表": "Meter",
  "电梯": "Elevator",
  "门禁": "Access Gate",
  "绑定空间": "Bound Space",
  "新增设备": "Add Device",
  "设备列表": "Devices",
  "设备": "Device",
  "名称": "Name",
  "资产状态": "Asset Status",
  "业务状态": "Business Status",
  "访客通行": "Visitor Access",
  "访客登记与审批": "Visitor registration and approval",
  "访客姓名": "Visitor Name",
  "手机号": "Mobile",
  "事由": "Purpose",
  "被访房屋": "Visited House",
  "被访人": "Host",
  "登记访客": "Register Visitor",
  "通行记录": "Access Records",
  "审批后生效": "Effective after approval",
  "暂无访客记录": "No access records",
  "访客": "Visitor",
  "有效期": "Valid Period",
  "通过": "Approve",
  "拒绝": "Reject",
  "投诉与申诉": "Complaints & Appeals",
  "投诉、申诉、入户走访": "Complaints, appeals and visits",
  "全部": "All",
  "投诉": "Complaint",
  "申诉": "Appeal",
  "走访": "Visit",
  "新增记录": "New Record",
  "记录列表": "Records",
  "暂无记录": "No records",
  "处理": "Handle",
  "处理记录": "Handle Record",
  "处理中": "Processing",
  "已解决": "Resolved",
  "已关闭": "Closed",
  "处理人": "Handler",
  "处理结果": "Result",
  "保存": "Save",
  "服务工单": "Service Orders",
  "报修、投诉、巡检": "Repair, complaint and inspection",
  "标题": "Title",
  "人员": "Person",
  "优先级": "Priority",
  "新建工单": "New Order",
  "工单列表": "Work Orders",
  "处理中 → 完成 / 关闭": "Processing → Done / Closed",
  "暂无工单": "No work orders",
  "工单号": "Order No.",
  "报修": "Repair",
  "巡检": "Inspection",
  "其他": "Other",
  "受理": "Accept",
  "完成": "Complete",
  "关闭": "Close",
  "表计台账": "Meter Ledger",
  "水表/电表/燃气表": "Water / Electricity / Gas",
  "表号": "Meter No.",
  "初始读数": "Initial Reading",
  "新增表计": "Add Meter",
  "表计列表": "Meters",
  "上次读数": "Last Reading",
  "状态": "Status",
  "抄表": "Reading",
  "本次读数": "Current Reading",
  "日期": "Date",
  "保存抄表": "Save Reading",
  "暂无抄表记录": "No readings",
  "用量": "Usage",
  "表计数量": "Meter Count",
  "水/电/气": "Water / Electricity / Gas",
  "项目与空间模板": "Projects & Space Templates",
  "保障房项目选择空间模板，创建后维护空间和房屋": "Create a guarantee project with a space template, then maintain spaces and houses",
  "项目编码": "Project Code",
  "项目列表": "Projects",
  "点击项目切换当前上下文": "Click a project to switch context",
  "暂无项目": "No projects",
  "项目": "Project",
  "模板": "Template",
  "操作": "Actions",
  "设为当前": "Set Current",
  "空间树": "Space Tree",
  "个空间": "spaces",
  "个房源": "houses",
  "上级空间": "Parent Space",
  "根节点": "Root",
  "空间编码": "Space Code",
  "空间名称": "Space Name",
  "资产类型": "Asset Type",
  "可出租": "Rentable",
  "新增空间": "Add Space",
  "暂无空间": "No spaces",
  "层级": "Level",
  "路径": "Path",
  "房屋/房源": "Houses",
  "可出租空间自动生成房源": "Rentable spaces generate houses automatically",
  "暂无房源": "No houses",
  "房源编码": "House Code",
  "面积": "Area",
  "人员档案": "People",
  "保障对象、家庭成员、承租人、同住人、访客、服务人员": "Guarantee tenants, family, tenants, cohabitants, visitors and staff",
  "人员编码": "Person Code",
  "姓名": "Name",
  "证件号掩码": "ID Mask",
  "人员类型": "Person Type",
  "保障对象": "Guarantee Tenant",
  "家庭成员": "Family Member",
  "同住人": "Cohabitant",
  "服务人员": "Staff",
  "新增人员": "Add Person",
  "人员列表": "People",
  "点击查看钥匙包": "Click to view keyring",
  "暂无人员": "No people",
  "钥匙包": "Keyring",
  "请选择人员": "Please select a person",
  "暂无有效授权": "No active grants",
  "长期": "Long-term"
})
for (const [k, v] of Object.entries(extra)) dictionary.set(k, v)

function patternTranslate(text) {
  const patterns = [
    [/^待审\s*(.+)$/, 'Pending $1'],
    [/^合同总数\s*(.+)$/, 'Total Contracts $1'],
    [/^未结清\s*(.+)$/, 'Unpaid $1'],
    [/^共\s*(.+)\s*笔$/, '$1 items'],
    [/^(.+)\s*条$/, '$1 records'],
    [/^(.+)\s*台设备$/, '$1 devices'],
    [/^(.+)\s*个任务$/, '$1 tasks'],
    [/^(.+)\s*个空间\s*·\s*(.+)\s*个房源$/, '$1 spaces · $2 houses']
  ]
  for (const [re, replacement] of patterns) {
    if (re.test(text)) return text.replace(re, replacement)
  }
  return ''
}

const originalText = new Map()
const translated = new Set()
let currentLocale = 'zh-CN'
let observer = null

function translateTextNode(node) {
  if (!node || node.nodeType !== 3) return
  const parent = node.parentElement
  if (!parent || ['SCRIPT', 'STYLE', 'TEXTAREA'].includes(parent.tagName)) return
  const raw = node.nodeValue || ''
  const key = raw.trim()
  if (!key) return
  if (!originalText.has(node)) originalText.set(node, raw)
  if (currentLocale !== 'en-US') {
    if (translated.has(node)) {
      node.nodeValue = originalText.get(node)
      translated.delete(node)
    }
    return
  }
  const target = dictionary.get(key) || patternTranslate(key)
  if (target) {
    const leading = raw.slice(0, raw.indexOf(key))
    const trailing = raw.slice(raw.indexOf(key) + key.length)
    node.nodeValue = leading + target + trailing
    translated.add(node)
  }
}

function translateTree(root) {
  if (!root) return
  if (root.nodeType === 3) return translateTextNode(root)
  if (!root.querySelectorAll) return
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  const nodes = []
  let n
  while ((n = walker.nextNode())) nodes.push(n)
  nodes.forEach(translateTextNode)
}

export function installPageI18n(locale) {
  if (observer) observer.disconnect()
  currentLocale = locale.value
  watch(locale, (value) => {
    currentLocale = value
    translateTree(document.body)
  })
  translateTree(document.body)
  observer = new MutationObserver((mutations) => {
    if (currentLocale !== 'en-US') return
    for (const m of mutations) {
      if (m.type === 'characterData') translateTextNode(m.target)
      else m.addedNodes.forEach(node => translateTree(node))
    }
  })
  observer.observe(document.body, { childList: true, subtree: true, characterData: true })
}
