/**
 * 设备事件/告警的显示转换：级别中文化 + body JSON 可读化。
 */

const LEVEL_LABEL = {
  INFO: '提示',
  WARN: '警告',
  WARNING: '警告',
  MINOR: '轻微',
  MAJOR: '较重',
  SEVERE: '严重',
  CRITICAL: '严重',
  ERROR: '错误'
}

export function levelLabel(code) {
  if (!code) return '—'
  return LEVEL_LABEL[String(code).toUpperCase()] || code
}

export function levelTagType(code) {
  const c = String(code || '').toUpperCase()
  if (c === 'CRITICAL' || c === 'SEVERE' || c === 'ERROR') return 'danger'
  if (c === 'WARN' || c === 'WARNING' || c === 'MAJOR') return 'warning'
  return 'info'
}

const KEY_LABEL = {
  pwdId: '密码/卡号', passwordId: '密码/卡号', cardId: '卡号', userId: '用户',
  lockId: '门锁', deviceId: '设备', spaceId: '空间', houseId: '房源',
  reason: '原因', count: '次数', battery: '电量(%)', voltage: '电压(V)',
  power: '功率(W)', current: '电流(A)', method: '开锁方式', type: '类型',
  firmware: '固件版本', timestamp: '上报时间', status: '状态', mode: '模式',
  source: '来源', message: '消息', msg: '消息', code: '代码', level: '级别',
  detail: '详情', extra: '附加信息', retry: '重试次数', duration: '持续(秒)'
}

function valueText(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return rawText(v)
  return String(v)
}

function rawText(o) {
  // 对象/数组：逐项转成「中文键：值」，嵌套再降一层
  if (Array.isArray(o)) return o.map((x) => valueText(x)).join('、')
  return Object.entries(o).map(([k, v]) => (KEY_LABEL[k] || k) + '：' + valueText(v)).join('；')
}

/** 把 body（可能是 JSON 字符串/对象/普通文本）转成中文可读文本 */
export function fmtEventBody(body) {
  if (body === null || body === undefined || body === '') return '—'
  if (typeof body === 'object') return rawText(body)
  const t = String(body).trim()
  if (!t.startsWith('{') && !t.startsWith('[')) return t
  try {
    return rawText(JSON.parse(t))
  } catch (e) {
    return t
  }
}
