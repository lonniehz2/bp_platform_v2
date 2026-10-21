# -*- coding: utf-8 -*-
"""给财务页补齐：补贴 / 催缴 / 对账 / 资金流水"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'createSubsidy' in s:
    print('已存在，跳过')
    raise SystemExit

# ---------- 1) 面板 ----------
anchor = '  <!-- ==================== 申请 ==================== -->'
assert anchor in s

panels = '''    <div class="card">
      <h3>补贴标准与发放（广州双轨）</h3>
      <div class="row">
        <div class="fld"><label>标准编码 *</label><input id="sbCode" placeholder="SUB-AREA"></div>
        <div class="fld"><label>标准名称 *</label><input id="sbName" placeholder="按面积补贴"></div>
        <div class="fld"><label>保障类型 *</label>
          <select id="sbSec"><option value="PUBLIC">PUBLIC 公租房</option>
            <option value="AFFORDABLE">AFFORDABLE 保租房</option>
            <option value="TALENT">TALENT 人才公寓</option>
            <option value="LOW_RENT">LOW_RENT 廉租</option></select></div>
        <div class="fld"><label>补贴方式 *</label>
          <select id="sbMode"><option value="FIXED">FIXED 定额</option>
            <option value="BY_AREA">BY_AREA 按面积</option>
            <option value="BY_PERSON">BY_PERSON 按人</option>
            <option value="RATIO">RATIO 按租金比例</option></select></div>
        <div class="fld"><label>补贴值 *</label><input id="sbValue" value="20"></div>
        <div class="fld"><label>月度封顶</label><input id="sbCap" placeholder="可选"></div>
        <button class="act" onclick="createSubsidyStd()">建标准</button>
      </div>
      <div class="row">
        <div class="fld"><label>合同ID *</label><input id="sbContract" value="2001"></div>
        <div class="fld"><label>人员ID *</label><input id="sbPerson" value="4001"></div>
        <div class="fld"><label>补贴期间 *</label><input id="sbPeriod" value="2026-10"></div>
        <div class="fld"><label>发放方式</label>
          <select id="sbPayMode"><option value="FINANCE">财政直发</option>
            <option value="BANK">银行代发</option>
            <option value="OFFSET_RENT">抵扣租金</option></select></div>
        <button class="act" onclick="calcSubsidy()">试算</button>
        <button class="act" onclick="grantSubsidy()">发放</button>
      </div>
      <div class="row">
        <div class="fld"><label>发放记录ID *</label><input id="sbRecordId" placeholder="发放后自动填" style="min-width:190px"></div>
        <button class="act" onclick="sbAction('confirm')">⭐ 确认发放</button>
        <button class="act red" onclick="sbAction('fail')">标记失败</button>
        <button class="act gray" onclick="sbBatch()">批量发放(试运行)</button>
        <button class="act gray" onclick="listSubsidy()">发放列表</button>
      </div>
      <div class="hint">
        补贴 = <b>定额 / 单价×面积 / 人均×人口 / 月租×比例</b>，统一受<b>月度封顶</b>约束。<br>
        ⭐ <b>OFFSET_RENT（抵扣租金）</b>：确认发放时自动冲减当期租金账单，余额不足转「部分缴」。<br>
        同合同同期间<b>只能发一次</b>（幂等）。
      </div>
    </div>

    <div class="card">
      <h3>催缴记录</h3>
      <div class="row">
        <div class="fld"><label>账单ID *</label><input id="dnBill" placeholder="逾期账单ID" style="min-width:190px"></div>
        <div class="fld"><label>催缴方式 *</label>
          <select id="dnType"><option value="SMS">短信</option><option value="WECHAT">微信</option>
            <option value="PHONE">电话</option><option value="VISIT">上门</option>
            <option value="NOTICE">通知书</option><option value="PLATFORM">平台消息</option></select></div>
        <div class="fld"><label>催缴内容</label><input id="dnContent" value="您的租金已逾期，请尽快缴纳" style="min-width:200px"></div>
        <div class="fld"><label>佐证URL(上门/电话)</label><input id="dnEvidence" placeholder="可选"></div>
        <button class="act" onclick="createDunning()">登记催缴</button>
        <button class="act gray" onclick="scanDunning()">催缴建议</button>
        <button class="act gray" onclick="listDunning()">催缴历史</button>
      </div>
      <div class="hint">
        催缴次数<b>自动递增</b>（1、2、3…）。上门/电话建议上传佐证，便于日后举证。<br>
        已缴清账单不可催缴。
      </div>
    </div>

    <div class="card">
      <h3>财务对账</h3>
      <div class="row">
        <div class="fld"><label>对账日期 *</label><input id="rcDate" placeholder="2026-10-19"></div>
        <div class="fld"><label>对账类型 *</label>
          <select id="rcType"><option value="CHANNEL">CHANNEL 渠道对账</option>
            <option value="DAILY">DAILY 日终对账</option>
            <option value="MANUAL">MANUAL 手工对账</option></select></div>
        <div class="fld"><label>渠道</label>
          <select id="rcChannel"><option value="">全部</option><option value="WECHAT">微信</option>
            <option value="ALIPAY">支付宝</option><option value="BANK_TRANSFER">银行转账</option>
            <option value="CASH">现金</option><option value="POS">刷卡</option></select></div>
        <div class="fld"><label>系统金额</label><input id="rcSystem" placeholder="留空自动汇总"></div>
        <div class="fld"><label>渠道金额 *</label><input id="rcChannelAmt" value="0"></div>
        <div class="fld"><label>差异笔数</label><input id="rcDiffCount" value="0"></div>
        <button class="act" onclick="createReconcile()">发起对账</button>
      </div>
      <div class="row">
        <div class="fld"><label>对账ID *</label><input id="rcId" placeholder="对账后自动填" style="min-width:190px"></div>
        <button class="act" onclick="handleReconcile()">处理差异</button>
        <button class="act gray" onclick="listReconcile()">对账列表</button>
      </div>
      <div class="hint">
        系统金额 = 当日该渠道<b>成功收款</b>合计（留空自动汇总）。差异 = 系统 − 渠道。<br>
        状态：<code>一致 MATCHED</code> / <code>有差异 DIFF</code> → 处理 → <code>已处理 HANDLED</code>。账实相符的不能"处理"。
      </div>
    </div>

    <div class="card">
      <h3>资金流水 <span class="m get">GET</span> /api/v1/fin/cash-flows</h3>
      <div class="row">
        <div class="fld"><label>流水类型</label>
          <select id="cfType"><option value="">全部</option><option value="INCOME">收入</option>
            <option value="EXPENSE">支出</option><option value="TRANSFER">转账</option>
            <option value="ADJUST">调整</option></select></div>
        <div class="fld"><label>业务类型</label>
          <select id="cfBizType"><option value="">全部</option><option value="BILL">账单</option>
            <option value="PAYMENT">收款</option><option value="REFUND">退款</option>
            <option value="SUBSIDY">补贴</option><option value="OTHER">其他</option></select></div>
        <div class="fld"><label>起始日</label><input id="cfFrom" placeholder="2026-01-01"></div>
        <div class="fld"><label>截止日</label><input id="cfTo" placeholder="2026-12-31"></div>
        <button class="act" onclick="listFlow()">查询流水</button>
        <button class="act" onclick="netFlow()">⭐ 净流入</button>
      </div>
      <div class="row">
        <div class="fld"><label>手工流水类型</label>
          <select id="cfmType"><option value="ADJUST">调整</option><option value="INCOME">收入</option>
            <option value="EXPENSE">支出</option></select></div>
        <div class="fld"><label>金额</label><input id="cfmAmount" value="-50"></div>
        <div class="fld"><label>备注</label><input id="cfmRemark" value="手续费调整"></div>
        <button class="act" onclick="recordFlow()">手工登记</button>
      </div>
      <div class="hint">
        ⭐ <b>收款/退款/补贴发放会自动写流水</b>，无需手工登记。金额<b>带符号</b>（收入正、支出负），可直接求和。<br>
        净流入 = 期间所有流水金额之和。
      </div>
    </div>
  </div>

'''
# 把新卡片插到财务面板末尾（替换 fin 面板的收尾 </div>）
fin_end_anchor = '''        <code>待审批 → 已批准 → 已退款</code>，不可跳步。<b>押金退还会自动扣减台账余额</b>，余额归零后台账变「已退还」。<br>
        退款金额不能超过押金台账余额。
      </div>
    </div>
  </div>

'''
assert fin_end_anchor in s, '找不到财务面板结尾'
s = s.replace(fin_end_anchor,
              '''        <code>待审批 → 已批准 → 已退款</code>，不可跳步。<b>押金退还会自动扣减台账余额</b>，余额归零后台账变「已退还」。<br>
        退款金额不能超过押金台账余额。
      </div>
    </div>

''' + panels, 1)

# ---------- 2) JS ----------
js_anchor = '// ---------- 申请 ----------'
assert js_anchor in s
js = '''// ---------- 财务：补贴 ----------
function createSubsidyStd() {
  const b = { standardCode: $('sbCode').value.trim() + '-' + Date.now().toString().slice(-5),
              standardName: $('sbName').value.trim(),
              securityType: $('sbSec').value, subsidyMode: $('sbMode').value,
              subsidyValue: $('sbValue').value, effectiveStart: '2026-01-01' };
  if ($('sbCap').value.trim()) b.maxAmount = $('sbCap').value.trim();
  return req('POST', '/api/v1/fin/subsidies/standards', b);
}
function calcSubsidy() {
  const b = { contractId: Number($('sbContract').value) };
  return req('POST', '/api/v1/fin/subsidies/calc', b);
}
function grantSubsidy() {
  const b = { contractId: Number($('sbContract').value), personId: Number($('sbPerson').value),
              subsidyPeriod: $('sbPeriod').value.trim(), payMode: $('sbPayMode').value };
  return req('POST', '/api/v1/fin/subsidies/records', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('sbRecordId').value = id;
  });
}
function sbAction(act) {
  const id = $('sbRecordId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填发放记录 ID</span>'; return; }
  if (act === 'confirm') {
    return req('POST', '/api/v1/fin/subsidies/records/' + id + '/confirm',
               { financeBatchNo: 'WEB-' + Date.now() });
  }
  return req('POST', '/api/v1/fin/subsidies/records/' + id + '/fail',
             { reason: '银行账户异常' });
}
function sbBatch() {
  return req('POST', '/api/v1/fin/subsidies/records/batch',
             { subsidyPeriod: $('sbPeriod').value.trim(), payMode: $('sbPayMode').value,
               dryRun: true });
}
function listSubsidy() {
  const c = $('sbContract').value.trim();
  let q = 'pageNum=1&pageSize=20';
  if (c) q += '&contractId=' + c;
  return req('GET', '/api/v1/fin/subsidies/records?' + q);
}

// ---------- 财务：催缴 ----------
function createDunning() {
  const b = { billId: Number($('dnBill').value), dunningType: $('dnType').value,
              dunningContent: $('dnContent').value.trim(), operatorId: 9001 };
  if ($('dnEvidence').value.trim()) b.evidenceUrl = $('dnEvidence').value.trim();
  return req('POST', '/api/v1/fin/dunnings', b);
}
function scanDunning() {
  return req('GET', '/api/v1/fin/dunnings/scan?minOverdueDays=3&maxDunningTimes=3');
}
function listDunning() {
  const b = $('dnBill').value.trim();
  if (!b) { out.innerHTML = '<span class="err">请先填账单 ID</span>'; return; }
  return req('GET', '/api/v1/fin/dunnings/by-bill/' + b);
}

// ---------- 财务：对账 ----------
function createReconcile() {
  const b = { reconcileDate: $('rcDate').value.trim() || new Date().toISOString().slice(0, 10),
              reconcileType: $('rcType').value,
              channelAmount: $('rcChannelAmt').value,
              diffCount: Number($('rcDiffCount').value || 0) };
  if ($('rcChannel').value) b.payChannel = $('rcChannel').value;
  if ($('rcSystem').value.trim()) b.systemAmount = $('rcSystem').value.trim();
  return req('POST', '/api/v1/fin/reconciles', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('rcId').value = id;
  });
}
function handleReconcile() {
  const id = $('rcId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填对账 ID</span>'; return; }
  return req('POST', '/api/v1/fin/reconciles/' + id + '/handle',
             { remark: '差异已人工核对处理' });
}
function listReconcile() { return req('GET', '/api/v1/fin/reconciles?pageNum=1&pageSize=20'); }

// ---------- 财务：资金流水 ----------
function listFlow() {
  let q = 'pageNum=1&pageSize=30';
  if ($('cfType').value) q += '&flowType=' + $('cfType').value;
  if ($('cfBizType').value) q += '&bizType=' + $('cfBizType').value;
  if ($('cfFrom').value.trim()) q += '&dateFrom=' + $('cfFrom').value.trim();
  if ($('cfTo').value.trim()) q += '&dateTo=' + $('cfTo').value.trim();
  return req('GET', '/api/v1/fin/cash-flows?' + q);
}
function netFlow() {
  let q = '';
  if ($('cfFrom').value.trim()) q += 'dateFrom=' + $('cfFrom').value.trim() + '&';
  if ($('cfTo').value.trim()) q += 'dateTo=' + $('cfTo').value.trim();
  return req('GET', '/api/v1/fin/cash-flows/net?' + q);
}
function recordFlow() {
  return req('POST', '/api/v1/fin/cash-flows', {
    flowType: $('cfmType').value, bizType: 'OTHER',
    amount: $('cfmAmount').value, remark: $('cfmRemark').value.trim() });
}

// ---------- 申请 ----------'''
s = s.replace(js_anchor, js, 1)

# ---------- 3) 接口清单 ----------
old_list = '<b>财务</b>　POST /api/v1/fin/bills'
assert old_list in s
s = s.replace(old_list,
              '<b>财务</b>　POST /api/v1/fin/bills', 1)
s = s.replace('POST /api/v1/fin/refunds ｜ GET /api/v1/fin/refunds ｜ .../approve ｜ .../reject ｜ .../complete<br>',
              'POST /api/v1/fin/refunds ｜ GET /api/v1/fin/refunds ｜ .../approve ｜ .../reject ｜ .../complete<br>\n'
              '        <b>财·补贴</b>　POST /api/v1/fin/subsidies/standards ｜ GET .../standards ｜ POST /api/v1/fin/subsidies/calc ｜ '
              'POST /api/v1/fin/subsidies/records ｜ GET .../records ｜ .../confirm ｜ .../fail ｜ .../records/batch<br>\n'
              '        <b>财·催缴</b>　GET /api/v1/fin/dunnings/scan ｜ POST /api/v1/fin/dunnings ｜ GET /api/v1/fin/dunnings ｜ GET .../by-bill/{id}<br>\n'
              '        <b>财·对账</b>　POST /api/v1/fin/reconciles ｜ GET /api/v1/fin/reconciles ｜ .../handle<br>\n'
              '        <b>财·流水</b>　POST /api/v1/fin/cash-flows ｜ GET /api/v1/fin/cash-flows ｜ GET .../net ｜ .../verify<br>', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('财务页已补齐，文件长度', len(s))
