# -*- coding: utf-8 -*-
"""短租订单：补齐前台日常动作（确认/入住/退房/未到/收款）。

后端接口已具备，仅缺前端按钮与 API 封装。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
F = os.path.join(ROOT, 'frontend', 'src')

# ---------- 1) API 封装 ----------
M = os.path.join(F, 'api', 'modules.js')
s = io.open(M, encoding='utf-8').read()
if 'checkIn:' not in s:
    s = s.replace("""  cancel: (id, reason) =>
    req.post(`/short-rent-orders/${id}/cancel`, null, { params: { reason } })
}""",
                  """  cancel: (id, reason) =>
    req.post(`/short-rent-orders/${id}/cancel`, null, { params: { reason } }),
  create: (data) => req.post('/short-rent-orders', data),
  confirm: (id) => req.post(`/short-rent-orders/${id}/confirm`),
  checkIn: (id) => req.post(`/short-rent-orders/${id}/check-in`),
  checkOut: (id, extraAmount) =>
    req.post(`/short-rent-orders/${id}/check-out`, { extraAmount: extraAmount || 0 }),
  noShow: (id) => req.post(`/short-rent-orders/${id}/no-show`),
  pay: (id, amount) => req.post(`/short-rent-orders/${id}/pay`, { amount })
}""", 1)
    io.open(M, 'w', encoding='utf-8', newline='').write(s)
    print('shortRentApi：已补 confirm/checkIn/checkOut/noShow/pay/create')

# ---------- 2) 页面操作列 ----------
P = os.path.join(F, 'views', 'ShortRent.vue')
s = io.open(P, encoding='utf-8').read()

if 'doConfirm' not in s:
    # 操作列加按钮
    s = re.sub(
        r'(<el-button link type="danger" @click="cancel\(row\)">取消</el-button>)',
        r'''<el-button v-if="row.orderStatus === 'PENDING'" link type="primary"
                       @click="doConfirm(row)" data-testid="sr-confirm">确认</el-button>
            <el-button v-if="row.orderStatus === 'CONFIRMED'" link type="success"
                       @click="doCheckIn(row)" data-testid="sr-checkin">入住</el-button>
            <el-button v-if="row.orderStatus === 'CHECKED_IN'" link type="warning"
                       @click="doCheckOut(row)" data-testid="sr-checkout">退房</el-button>
            <el-button v-if="row.orderStatus === 'CONFIRMED'" link
                       @click="doNoShow(row)">未到</el-button>
            <el-button v-if="row.orderStatus === 'CHECKED_OUT'" link type="primary"
                       @click="doPay(row)">收款</el-button>
            \1''', s, count=1)

    script = '''
/** 前台动作：确认 / 入住 / 退房 / 未到 / 收款 */
async function doConfirm(row) {
  await shortRentApi.confirm(row.id)
  ElMessage.success('订单已确认')
  load()
}

async function doCheckIn(row) {
  await shortRentApi.checkIn(row.id)
  ElMessage.success('已办理入住')
  load()
}

async function doCheckOut(row) {
  let extra = '0'
  try {
    const r = await ElMessageBox.prompt('额外费用（如超时、损坏，无则填 0）', '办理退房', {
      inputValue: '0', inputPattern: /^\\d+(\\.\\d{1,2})?$/,
      inputErrorMessage: '请输入数字'
    })
    extra = r.value
  } catch (e) { return }
  await shortRentApi.checkOut(row.id, Number(extra))
  ElMessage.success('已办理退房，房态已释放')
  load()
}

async function doNoShow(row) {
  await shortRentApi.noShow(row.id)
  ElMessage.success('已标记未到')
  load()
}

async function doPay(row) {
  let amount = String(row.payableAmount || row.roomAmount || 0)
  try {
    const r = await ElMessageBox.prompt('收款金额', '登记收款', {
      inputValue: amount, inputPattern: /^\\d+(\\.\\d{1,2})?$/,
      inputErrorMessage: '请输入数字'
    })
    amount = r.value
  } catch (e) { return }
  await shortRentApi.pay(row.id, Number(amount))
  ElMessage.success('收款已登记')
  load()
}
'''
    anchor = 'onMounted('
    i = s.find(anchor)
    s = s[:i] + script + '\n' + s[i:]

    # 确保 ElMessageBox 已引入
    if 'ElMessageBox' not in s.split('</script>')[0]:
        s = s.replace("import { ElMessage } from 'element-plus'",
                      "import { ElMessage, ElMessageBox } from 'element-plus'", 1)

    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('ShortRent.vue：已加 确认/入住/退房/未到/收款')
else:
    print('ShortRent.vue：已存在')
