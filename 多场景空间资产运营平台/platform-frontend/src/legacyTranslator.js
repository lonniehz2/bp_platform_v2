const phrases = [
  ['保障房','Guarantee Housing'],['列表','List'],['与生命周期','and Lifecycle'],['新建','Create'],['生成租金','Generate Rent'],['编号','No.'],['承租人','Tenant'],['账单日','Bill Day'],['直接生效','Activate'],['提交','Submit'],['支付','Payment'],['收款','Payment'],['账单','Bill'],['合同','Contract'],['房源','House'],['房屋','House'],['人员','Person'],['状态','Status'],['操作','Actions'],['详情','Details'],

  ['演示保障房项目','Demo Guarantee Housing Project'],['保障房验证项目','Guarantee Verification Project'],
  ['新增','Add'],['编辑','Edit'],['删除','Delete'],['保存','Save'],['取消','Cancel'],['关闭','Close'],['查询','Search'],['搜索','Search'],['重置','Reset'],
  ['导出','Export'],['导入','Import'],['详情','Details'],['查看','View'],['返回','Back'],['确定','Confirm'],['提交','Submit'],['审核','Approve'],['通过','Approve'],['驳回','Reject'],['作废','Void'],
  ['启用','Enable'],['停用','Disable'],['状态','Status'],['类型','Type'],['名称','Name'],['编码','Code'],['金额','Amount'],['日期','Date'],['开始','Start'],['结束','End'],
  ['人员','Person'],['房屋','House'],['合同','Contract'],['账单','Bill'],['房源','House'],['项目','Project'],['设备','Device'],['工单','Work Order'],['申请','Application'],['押金','Deposit'],['补贴','Subsidy'],['收款','Payment'],
  ['欠费','Arrears'],['出租率','Occupancy'],['收缴率','Collection Rate'],['应收','Receivable'],['实收','Collected'],['总欠费','Total Arrears'],['本月','This Month'],['本季','This Quarter'],['本年','This Year'],['自定义','Custom'],
  ['全部项目','All Projects'],['全部','All'],['暂无数据','No data'],['暂无','No'],['加载中','Loading'],['操作','Actions'],['备注','Remark'],['地址','Address'],['电话','Phone'],['性别','Gender'],
  ['生效中','Active'],['草稿','Draft'],['已支付','Paid'],['未支付','Unpaid'],['已出租','Rented'],['空置','Vacant'],['已入住','Occupied'],['待处理','Pending'],['处理中','Processing'],['已完成','Done'],['未分配','Unassigned'],
  ['组织','Organization'],['报表','Report'],['订阅','Subscription'],['频率','Frequency'],['接收人','Recipients'],['监管','Regulatory'],['口径','Scope'],['项目数','Projects'],['房源总数','Houses'],['已出租房源','Rented Houses'],
  ['应收实收','Receivable & Collected'],['资金流水','Cash Flow'],['设备台账','Devices'],['工单统计','Work Orders'],['房源台账','Houses'],['欠费清单','Arrears'],['申请受理','Applications'],['合同台账','Contracts'],['项目经营对比','Project Comparison']
]
let observer = null
const originals = new WeakMap()
function translateText(text) {
  if (!/[\u4e00-\u9fa5]/.test(text)) return text
  let out = text
  for (const [zh, en] of phrases) out = out.split(zh).join(en)
  return out
}
function walk(node) {
  if (node.nodeType === 3) {
    if (!originals.has(node)) originals.set(node, node.nodeValue)
    const next = translateText(node.nodeValue)
    if (next !== node.nodeValue) node.nodeValue = next
  } else if (node.nodeType === 1) {
    for (const attr of ['placeholder','title','aria-label']) {
      if (node.hasAttribute(attr)) {
        if (!originals.has(node)) originals.set(node, {})
        const store = originals.get(node)
        if (!(attr in store)) store[attr] = node.getAttribute(attr)
        node.setAttribute(attr, translateText(node.getAttribute(attr)))
      }
    }
    for (const child of node.childNodes) walk(child)
  }
}
export function applyLegacyTranslation(enabled) {
  if (observer) { observer.disconnect(); observer = null }
  if (!enabled) return
  walk(document.body)
  observer = new MutationObserver(muts => {
    for (const m of muts) for (const n of m.addedNodes) walk(n)
  })
  observer.observe(document.body, { childList: true, subtree: true })
}
