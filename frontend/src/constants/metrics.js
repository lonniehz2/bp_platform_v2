/**
 * 指标编码 → 中文名称。
 * 编码来源：后端 MetricServiceImpl（13 个指标）。
 * 前端只做展示映射，不参与计算。
 */
export const METRIC_LABEL = {
  HOUSE_TOTAL: '房源总数',
  HOUSE_OCCUPIED: '已租房源',
  HOUSE_VACANT: '空置房源',
  OCCUPANCY_RATE: '出租率',
  BILL_UNPAID_AMOUNT: '欠费金额',
  BILL_UNPAID_COUNT: '欠费账单数',
  PAYMENT_TOTAL_AMOUNT: '累计收款',
  ACCESS_TODAY_COUNT: '今日开门',
  ACCESS_ABNORMAL_COUNT: '今日异常开门',
  ALLOCATED: '已配租',
  PENDING_ALLOC: '待配租',
  OCCUPIED: '占用',
  VACANT: '空置'
}

/** 图表类型 → 中文（大屏/驾驶舱卡片副标题用） */
export const CHART_LABEL = {
  NUMBER: '数值',
  GAUGE: '仪表盘',
  LINE: '折线',
  BAR: '柱状',
  PIE: '饼图'
}

/** 单位 */
export const METRIC_UNIT = {
  OCCUPANCY_RATE: '%',
  BILL_UNPAID_AMOUNT: '元',
  PAYMENT_TOTAL_AMOUNT: '元'
}

export function metricLabel(code) {
  return METRIC_LABEL[code] || code
}

export function chartLabel(type) {
  return CHART_LABEL[type] || type || ''
}

export function metricUnit(code) {
  return METRIC_UNIT[code] || ''
}
