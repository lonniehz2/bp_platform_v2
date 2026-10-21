# -*- coding: utf-8 -*-
"""给验证台加「财务」标签页（账单/收款/押金/退款）"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'id="p-fin"' in s:
    print('已存在，跳过')
    raise SystemExit

s = s.replace('    <button data-t="p-app">申请</button>',
              '    <button data-t="p-fin">财务</button>\n'
              '    <button data-t="p-app">申请</button>', 1)

anchor = '  <!-- ==================== 申请 ==================== -->'
assert anchor in s

panel = '''  <!-- ==================== 财务 ==================== -->
  <div class="panel" id="p-fin">
    <div class="card">
      <h3>生成账单 <span class="m post">POST</span> /api/v1/fin/bills</h3>
      <div class="row">
        <div class="fld"><label>收费项目ID *</label><input id="fbItem" value="1"></div>
        <div class="fld"><label>组织ID *</label><input id="fbOrg" value="7001"></div>
        <div class="fld"><label>合同ID</label><input id="fbContract" value="2001"></div>
        <div class="fld"><label>房源ID</label><input id="fbHouse" value="5001"></div>
        <div class="fld"><label>缴费人</label><input id="fbPayer" value="张三"></div>
        <div class="fld"><label>账期</label><input id="fbPeriod" value="2026-10"></div>
      </div>
      <div class="row">
        <div class="fld"><label>费用起始日 *</label><input id="fbStart" value="2026-10-01"></div>
        <div class="fld"><label>费用截止日 *</label><input id="fbEnd" value="2026-10-31"></div>
        <div class="fld"><label>应收金额 *</label><input id="fbAmount" value="1000"></div>
        <div class="fld"><label>减免</label><input id="fbDiscount" value="0"></div>
        <div class="fld"><label>滞纳金</label><input id="fbLate" value="0"></div>
        <div class="fld"><label>缴费截止日</label><input id="fbDue" value="2026-12-31"></div>
        <button class="act" onclick="createBill()">生成</button>
        <button class="act gray" onclick="scanOverdue()">逾期扫描</button>
      </div>
      <div class="hint">
        <b>应付 = 应收 - 减免 + 滞纳金 - 已收 - 已免</b>（后端算）。减免超应收会被拒。<br>
        VO 派生 <code>overdueNow</code> 实时判断是否逾期。
      </div>
    </div>

    <div class="card">
      <h3>登记收款 + 核销</h3>
      <div class="row">
        <div class="fld"><label>组织ID *</label><input id="fpOrg" value="7001"></div>
        <div class="fld"><label>缴费人</label><input id="fpPayer" value="张三"></div>
        <div class="fld"><label>收款金额 *</label><input id="fpAmount" value="600"></div>
        <div class="fld"><label>渠道 *</label>
          <select id="fpChannel"><option value="WECHAT">微信</option><option value="ALIPAY">支付宝</option>
            <option value="BANK_TRANSFER">银行转账</option><option value="CASH">现金</option>
            <option value="POS">刷卡</option><option value="SELF_TERMINAL">自助机</option>
            <option value="OTHER">其他</option></select></div>
        <div class="fld"><label>第三方交易号</label><input id="fpTrade" placeholder="可选"></div>
        <button class="act" onclick="createPayment()">登记收款</button>
      </div>
      <div class="row">
        <div class="fld"><label>收款单ID *</label><input id="fpId" placeholder="登记后自动填" style="min-width:190px"></div>
        <div class="fld"><label>账单ID *</label><input id="fpaBill" placeholder="要核销的账单" style="min-width:190px"></div>
        <div class="fld"><label>核销金额</label><input id="fpaAmount" placeholder="留空=全额"></div>
        <button class="act" onclick="allocate()">⭐ 核销</button>
        <button class="act gray" onclick="listBill()">账单列表</button>
        <button class="act gray" onclick="listPayment()">收款列表</button>
      </div>
      <div class="hint">
        核销受<b>三重上限</b>保护：不超收款单余额、不超账单应付、已缴账单不可再核。核销后账单自动 UNPAID→PARTIAL→PAID。
      </div>
    </div>

    <div class="card">
      <h3>押金台账</h3>
      <div class="row">
        <div class="fld"><label>合同ID *</label><input id="fdContract" value="2001"></div>
        <div class="fld"><label>人员ID *</label><input id="fdPerson" value="4001"></div>
        <div class="fld"><label>应收押金 *</label><input id="fdDue" value="2000"></div>
        <div class="fld"><label>已收押金</label><input id="fdPaid" value="2000"></div>
        <div class="fld"><label>政策上限(成都1000)</label><input id="fdCap" value="1000"></div>
        <div class="fld"><label>免收</label>
          <select id="fdExempt"><option value="0">否</option><option value="1">是（廉租免收）</option></select></div>
        <button class="act" onclick="createDeposit()">建台账</button>
      </div>
      <div class="row">
        <div class="fld"><label>台账ID *</label><input id="fdId" placeholder="建立后自动填" style="min-width:190px"></div>
        <div class="fld"><label>抵扣金额</label><input id="fdDeduct" value="300"></div>
        <div class="fld"><label>抵扣原因</label><input id="fdReason" value="墙面损坏赔偿" style="min-width:150px"></div>
        <button class="act" onclick="deductDeposit()">押金抵扣</button>
        <button class="act gray" onclick="getDepositByContract()">按合同查台账</button>
      </div>
      <div class="hint">
        <b>余额 = 已收 - 已抵扣 - 已退还</b>。押金超政策上限会标 <code>overCap=true</code>（不阻断，留人工复核）。<br>
        状态：已收取 → 部分退还 → 已退还 / 已抵扣（全额扣留）。
      </div>
    </div>

    <div class="card">
      <h3>退款单（退租结算落地）</h3>
      <div class="row">
        <div class="fld"><label>合同ID *</label><input id="frContract" value="2001"></div>
        <div class="fld"><label>人员ID</label><input id="frPerson" value="4001"></div>
        <div class="fld"><label>退款金额 *</label><input id="frAmount" value="1700"></div>
        <div class="fld"><label>退款类型 *</label>
          <select id="frType"><option value="DEPOSIT">DEPOSIT 押金退还</option>
            <option value="OVERPAY">OVERPAY 多缴退还</option>
            <option value="OTHER">OTHER 其他</option></select></div>
        <div class="fld"><label>退款渠道</label>
          <select id="frChannel"><option value="ORIGINAL">原路退回</option>
            <option value="BANK">银行转账</option><option value="CASH">现金</option></select></div>
        <button class="act" onclick="createRefund()">申请退款</button>
      </div>
      <div class="row">
        <div class="fld"><label>退款单ID *</label><input id="frId" placeholder="申请后自动填" style="min-width:190px"></div>
        <button class="act" onclick="frAction('approve')">审批通过</button>
        <button class="act" onclick="frAction('complete')">⭐ 打款完成</button>
        <button class="act red" onclick="frAction('reject')">驳回</button>
        <button class="act gray" onclick="listRefund()">退款列表</button>
      </div>
      <div class="hint">
        <code>待审批 → 已批准 → 已退款</code>，不可跳步。<b>押金退还会自动扣减台账余额</b>，余额归零后台账变「已退还」。<br>
        退款金额不能超过押金台账余额。
      </div>
    </div>
  </div>

'''
s = s.replace(anchor, panel + anchor, 1)

# JS
anchor_js = '// ---------- 申请 ----------'
assert anchor_js in s
js = '''// ---------- 财务：账单 ----------
function createBill() {
  const b = { feeItemId: Number($('fbItem').value), orgId: Number($('fbOrg').value),
              periodStart: $('fbStart').value, periodEnd: $('fbEnd').value,
              billAmount: $('fbAmount').value, discountAmount: $('fbDiscount').value,
              lateFee: $('fbLate').value, dueDate: $('fbDue').value,
              generateType: 'MANUAL' };
  if ($('fbContract').value.trim()) b.contractId = Number($('fbContract').value);
  if ($('fbHouse').value.trim()) b.houseId = Number($('fbHouse').value);
  if ($('fbPayer').value.trim()) b.payerName = $('fbPayer').value.trim();
  if ($('fbPeriod').value.trim()) b.billPeriod = $('fbPeriod').value.trim();
  return req('POST', '/api/v1/fin/bills', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('fpaBill').value = id;
  });
}
function scanOverdue() { return req('POST', '/api/v1/fin/bills/scan-overdue', {}); }
function listBill() {
  const c = $('fbContract').value.trim();
  let q = 'pageNum=1&pageSize=20';
  if (c) q += '&contractId=' + c;
  return req('GET', '/api/v1/fin/bills?' + q);
}

// ---------- 财务：收款 ----------
function createPayment() {
  const b = { orgId: Number($('fpOrg').value), payAmount: $('fpAmount').value,
              payChannel: $('fpChannel').value };
  if ($('fpPayer').value.trim()) b.payerName = $('fpPayer').value.trim();
  if ($('fpTrade').value.trim()) b.tradeNo = $('fpTrade').value.trim();
  return req('POST', '/api/v1/fin/payments', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('fpId').value = id;
  });
}
function allocate() {
  const pid = $('fpId').value.trim();
  const bid = $('fpaBill').value.trim();
  if (!pid || !bid) { out.innerHTML = '<span class="err">请填收款单ID与账单ID</span>'; return; }
  const b = { billId: Number(bid) };
  if ($('fpaAmount').value.trim()) b.amount = $('fpaAmount').value.trim();
  return req('POST', '/api/v1/fin/payments/' + pid + '/allocate', b);
}
function listPayment() { return req('GET', '/api/v1/fin/payments?pageNum=1&pageSize=20'); }

// ---------- 财务：押金 ----------
function createDeposit() {
  const b = { contractId: Number($('fdContract').value), personId: Number($('fdPerson').value),
              depositAmount: $('fdDue').value, paidAmount: $('fdPaid').value,
              isExempt: Number($('fdExempt').value) };
  if ($('fdCap').value.trim()) b.capAmount = $('fdCap').value.trim();
  if ($('fdExempt').value === '1') b.exemptReason = '廉租标准免收押金';
  return req('POST', '/api/v1/fin/deposits', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('fdId').value = id;
  });
}
function deductDeposit() {
  const id = $('fdId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填押金台账 ID</span>'; return; }
  return req('POST', '/api/v1/fin/deposits/' + id + '/deduct',
             { amount: $('fdDeduct').value, reason: $('fdReason').value.trim() });
}
function getDepositByContract() {
  const c = $('fdContract').value.trim();
  return req('GET', '/api/v1/fin/deposits/by-contract/' + c);
}

// ---------- 财务：退款 ----------
function createRefund() {
  const b = { contractId: Number($('frContract').value), personId: Number($('frPerson').value),
              refundAmount: $('frAmount').value, refundType: $('frType').value,
              refundChannel: $('frChannel').value, refundReason: '退租退还押金' };
  return req('POST', '/api/v1/fin/refunds', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('frId').value = id;
  });
}
function frAction(act) {
  const id = $('frId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退款单 ID</span>'; return; }
  if (act === 'reject') {
    return req('POST', '/api/v1/fin/refunds/' + id + '/reject',
               { approveById: 9003, reason: '账户信息有误' });
  }
  if (act === 'approve') {
    return req('POST', '/api/v1/fin/refunds/' + id + '/approve', { approveById: 9003 });
  }
  return req('POST', '/api/v1/fin/refunds/' + id + '/complete', {});
}
function listRefund() {
  const c = $('frContract').value.trim();
  let q = 'pageNum=1&pageSize=20';
  if (c) q += '&contractId=' + c;
  return req('GET', '/api/v1/fin/refunds?' + q);
}

// ---------- 申请 ----------'''
s = s.replace(anchor_js, js, 1)

# 接口清单
s = s.replace('<b>申请</b>　POST /api/v1/applications',
              '<b>财务</b>　POST /api/v1/fin/bills ｜ GET /api/v1/fin/bills ｜ POST /api/v1/fin/bills/scan-overdue ｜ .../waive ｜ .../cancel ｜ '
              'POST /api/v1/fin/payments ｜ GET /api/v1/fin/payments ｜ POST .../payments/{id}/allocate ｜ '
              'POST /api/v1/fin/deposits ｜ GET /api/v1/fin/deposits ｜ .../deduct ｜ .../receive ｜ GET .../by-contract/{id} ｜ '
              'POST /api/v1/fin/refunds ｜ GET /api/v1/fin/refunds ｜ .../approve ｜ .../reject ｜ .../complete<br>\n'
              '        <b>申请</b>　POST /api/v1/applications', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已加财务页，文件长度', len(s))
