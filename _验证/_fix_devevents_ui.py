# -*- coding: utf-8 -*-
"""设备告警页前端：详情 JSON 格式化 + 统计卡片口径。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'DevEvents.vue')
s = io.open(P, encoding='utf-8').read()
n = 0

# 1) 「告警类型」卡片：改成当前类型数 + 系统支持数说明
OLD_CARD = """        <el-card shadow="never"><div class="muted">告警类型</div>
          <div style="font-size:22px;font-weight:600">{{ (stats.alarmTypes || []).length }}</div>
        </el-card>"""
NEW_CARD = """        <el-card shadow="never">
          <el-tooltip placement="bottom">
            <template #content>
              系统支持 {{ (stats.alarmTypes || []).length }} 种告警：<br />
              <span v-for="t in stats.alarmTypes || []" :key="t.code">
                {{ t.label }}<br />
              </span>
            </template>
            <div class="muted">当前告警类型（种）</div>
          </el-tooltip>
          <div style="font-size:22px;font-weight:600">
            {{ stats.typeCount || 0 }}
            <span class="muted" style="font-size:12px;font-weight:400">
              / 系统支持 {{ (stats.alarmTypes || []).length }} 种
            </span>
          </div>
        </el-card>"""
if OLD_CARD in s:
    s = s.replace(OLD_CARD, NEW_CARD, 1)
    n += 1

# 2) 详情列：JSON 格式化
OLD_BODY = """      <el-table-column prop="body" label="详情" min-width="240" show-overflow-tooltip />"""
NEW_BODY = """      <el-table-column prop="body" label="详情" min-width="260" show-overflow-tooltip>
        <template #default="{ row }">{{ fmtBody(row.body) }}</template>
      </el-table-column>"""
if OLD_BODY in s:
    s = s.replace(OLD_BODY, NEW_BODY, 1)
    n += 1

# 3) 统计请求带上与列表相同的筛选
OLD_REQ = """    const st = await req.get('/dev-events/stats',
      { params: query.unhandledOnly ? { unhandledOnly: true } : {} })"""
NEW_REQ = """    // 统计与列表用同一组筛选条件，避免「列表 4 条、卡片 5 条」的口径不一致
    const st = await req.get('/dev-events/stats', { params })
"""
if OLD_REQ in s:
    s = s.replace(OLD_REQ, NEW_REQ, 1)
    n += 1

# 4) 格式化函数
OLD_FN = """function labelOf(code) { return EV_LABEL[code] || code }"""
NEW_FN = """function labelOf(code) { return EV_LABEL[code] || code }

/** 事件 body 是 JSON 字符串，这里转成「中文键：值」便于阅读 */
const BODY_KEY_LABEL = {
  pwdId: '密码/卡号', passwordId: '密码/卡号', cardId: '卡号', userId: '用户',
  reason: '原因', count: '次数', battery: '电量(%)', voltage: '电压(V)',
  power: '功率(W)', current: '电流(A)', method: '开锁方式', type: '类型',
  deviceId: '设备', firmware: '固件版本', timestamp: '上报时间', status: '状态',
  lockId: '门锁', mode: '模式', source: '来源', message: '消息'
}
function fmtBody(body) {
  if (!body) return '—'
  const t = String(body).trim()
  if (!t.startsWith('{') && !t.startsWith('[')) return t
  try {
    const o = JSON.parse(t)
    if (Array.isArray(o)) return o.map((x) => fmtBody(JSON.stringify(x))).join('；')
    return Object.entries(o).map(([k, v]) => {
      const key = BODY_KEY_LABEL[k] || k
      const val = (v !== null && typeof v === 'object')
        ? JSON.stringify(v) : String(v)
      return key + '：' + val
    }).join('；')
  } catch (e) {
    return t
  }
}"""
if OLD_FN in s:
    s = s.replace(OLD_FN, NEW_FN, 1)
    n += 1

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('DevEvents.vue 改动:', n, '/ 4')
