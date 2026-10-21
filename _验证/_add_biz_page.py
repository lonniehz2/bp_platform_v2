# -*- coding: utf-8 -*-
"""给验证台加「申请」「合同」「退租」三个标签页"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'id="p-app"' in s:
    print('已存在，跳过')
    raise SystemExit

# 1) 标签
s = s.replace('    <button data-t="p-dash">驾驶舱</button>',
              '    <button data-t="p-app">申请</button>\n'
              '    <button data-t="p-contract">合同</button>\n'
              '    <button data-t="p-term">退租</button>\n'
              '    <button data-t="p-dash">驾驶舱</button>', 1)

anchor = '  <!-- ==================== 驾驶舱 ==================== -->'
assert anchor in s

panels = '''  <!-- ==================== 申请 ==================== -->
  <div class="panel" id="p-app">
    <div class="card">
      <h3>提交保障房申请 <span class="m post">POST</span> /api/v1/applications</h3>
      <div class="row">
        <div class="fld"><label>保障类型 *</label>
          <select id="apType"><option value="PUBLIC">PUBLIC 公租房</option>
            <option value="AFFORDABLE">AFFORDABLE 保租房</option>
            <option value="TALENT">TALENT 人才公寓</option>
            <option value="LOW_RENT">LOW_RENT 廉租</option></select></div>
        <div class="fld"><label>保障方式</label>
          <select id="apMode"><option value="HOUSE">HOUSE 实物配租</option>
            <option value="SUBSIDY">SUBSIDY 租赁补贴</option></select></div>
        <div class="fld"><label>组织ID *</label><input id="apOrg" value="7001"></div>
        <div class="fld"><label>人员ID *</label><input id="apPerson" value="4001"></div>
        <div class="fld"><label>家庭人口 *</label><input id="apFamily" value="3"></div>
      </div>
      <div class="row">
        <div class="fld"><label>月收入(元)</label><input id="apIncome" value="6000"></div>
        <div class="fld"><label>意向区域</label><input id="apDistrict" value="漳州市芗城区"></div>
        <div class="fld"><label>意向户型</label><input id="apLayout" value="2居"></div>
        <div class="fld"><label>意向面积下限</label><input id="apAmin" value="50"></div>
        <div class="fld"><label>意向面积上限</label><input id="apAmax" value="70"></div>
      </div>
      <div class="row">
        <button class="act" onclick="createApp()">提交申请</button>
        <button class="act gray" onclick="listApp()">查询列表</button>
      </div>
      <div class="hint">
        ⚠️ 保障房必备：<b>真实性承诺书 + 同意核实</b>（页面自动置 1）。<br>
        提交后状态 <code>SUBMITTED</code>，需先<b>受理</b>才能审核。人均收入由后端自动派生。
      </div>
    </div>

    <div class="card">
      <h3>受理与多阶段审核</h3>
      <div class="row">
        <div class="fld"><label>申请ID *</label><input id="apId" placeholder="提交后自动填" style="min-width:190px"></div>
        <div class="fld"><label>审核阶段</label>
          <select id="apStage"><option value="ACCEPT">ACCEPT 受理初审</option>
            <option value="FORM">FORM 形式审查</option>
            <option value="JOINT">JOINT 多部门联审</option>
            <option value="FINAL">FINAL 终审</option></select></div>
        <div class="fld"><label>审核结果</label>
          <select id="apResult"><option value="PASS">PASS 通过</option>
            <option value="REJECT">REJECT 不通过</option>
            <option value="SUPPLEMENT">SUPPLEMENT 需补件</option></select></div>
        <div class="fld"><label>审核部门(联审)</label><input id="apDept" placeholder="REAL_ESTATE" style="min-width:130px"></div>
        <div class="fld"><label>意见</label><input id="apOpinion" value="核验通过" style="min-width:170px"></div>
      </div>
      <div class="row">
        <button class="act" onclick="acceptApp()">受理</button>
        <button class="act" onclick="reviewApp()">提交审核</button>
        <button class="act gray" onclick="resubmitApp()">补件后重提</button>
        <button class="act red" onclick="cancelApp()">撤回</button>
        <button class="act gray" onclick="appReviews()">审核轨迹</button>
      </div>
      <div class="hint">
        <b>关键：初审/形式审查通过只推进阶段，仍是"审核中"</b>；只有 <code>FINAL</code> 阶段 <code>PASS</code> 才变 <code>APPROVED</code>。<br>
        未受理不能审核；待补件不能直接审核（需先重提）；审核中不可撤回。
      </div>
    </div>

    <div class="card">
      <h3>申请列表 <span class="m get">GET</span> /api/v1/applications</h3>
      <div class="row">
        <div class="fld"><label>状态</label>
          <select id="apFSt"><option value="">全部</option>
            <option value="SUBMITTED">已提交</option><option value="REVIEWING">审核中</option>
            <option value="SUPPLEMENT">待补件</option><option value="APPROVED">已通过</option>
            <option value="REJECTED">不通过</option><option value="CANCELLED">已取消</option></select></div>
        <button class="act" onclick="listApp()">查询</button>
      </div>
    </div>
  </div>

  <!-- ==================== 合同 ==================== -->
  <div class="panel" id="p-contract">
    <div class="card">
      <h3>起草合同 <span class="m post">POST</span> /api/v1/contracts</h3>
      <div class="row">
        <div class="fld"><label>合同类型 *</label>
          <select id="ctType"><option value="PUBLIC_RENTAL">PUBLIC_RENTAL 公租房</option>
            <option value="AFFORDABLE">AFFORDABLE 保租房</option>
            <option value="TALENT">TALENT 人才公寓</option>
            <option value="LEASE">LEASE 租赁</option></select></div>
        <div class="fld"><label>签约组织 *</label><input id="ctOrg" value="7001"></div>
        <div class="fld"><label>出租方 *</label><input id="ctLessor" value="7100"></div>
        <div class="fld"><label>承租人 *</label><input id="ctLessee" value="4001"></div>
        <div class="fld"><label>承租人姓名</label><input id="ctName" value="张三"></div>
      </div>
      <div class="row">
        <div class="fld"><label>房源ID *</label><input id="ctHouse" value="5001"></div>
        <div class="fld"><label>空间ID *</label><input id="ctSpace" value="6001"></div>
        <div class="fld"><label>起租日 *</label><input id="ctStart" value="2026-01-01"></div>
        <div class="fld"><label>止租日 *</label><input id="ctEnd" value="2027-01-01"></div>
        <div class="fld"><label>月租金 *</label><input id="ctRent" value="1000"></div>
      </div>
      <div class="row">
        <div class="fld"><label>租金单价</label><input id="ctPrice" value="12.50"></div>
        <div class="fld"><label>押金</label><input id="ctDeposit" value="1000"></div>
        <div class="fld"><label>月补贴</label><input id="ctSubsidy" value="300"></div>
        <div class="fld"><label>签署方式</label>
          <select id="ctSign"><option value="ELECTRONIC">ELECTRONIC 电子签章</option>
            <option value="PAPER">PAPER 纸质</option><option value="FACE">FACE 人脸确认</option></select></div>
        <button class="act" onclick="createContract()">起草</button>
      </div>
      <div class="hint">
        <b>实付 = 月租金 - 补贴</b>（后端算，补贴超租金会被拒）。租期按自然月计算（1 年 = 12 个月）。
        面积/地址可用默认值。
      </div>
    </div>

    <div class="card">
      <h3>合同流转</h3>
      <div class="row">
        <div class="fld"><label>合同ID *</label><input id="ctId" placeholder="起草后自动填" style="min-width:190px"></div>
        <div class="fld"><label>新止租日(续签)</label><input id="ctNewEnd" placeholder="2028-01-01"></div>
        <div class="fld"><label>新月租金(续签)</label><input id="ctNewRent" placeholder="1200"></div>
        <div class="fld"><label>终止原因</label><input id="ctReason" value="承租人退租" style="min-width:170px"></div>
      </div>
      <div class="row">
        <button class="act" onclick="ctAction('submit-sign')">提交签约</button>
        <button class="act" onclick="ctAction('start-signing')">发起签署</button>
        <button class="act" onclick="ctSignContract()">⭐ 签署生效</button>
        <button class="act" onclick="ctRenew()">续签</button>
        <button class="act red" onclick="ctAction('terminate')">终止</button>
        <button class="act red" onclick="ctAction('cancel')">作废</button>
        <button class="act gray" onclick="ctExpire()">到期扫描</button>
      </div>
      <div class="hint">
        <code>草稿 → 待签约 → 签约中 → 履约中 →（续签/到期/终止）</code>，不可跳步。<br>
        <b>纸质合同可从"待签约"直接生效</b>。履约中不能作废，只能终止。
      </div>
    </div>

    <div class="card">
      <h3>合同列表 <span class="m get">GET</span> /api/v1/contracts</h3>
      <div class="row">
        <div class="fld"><label>状态</label>
          <select id="ctFSt"><option value="">全部</option>
            <option value="DRAFT">草稿</option><option value="PENDING_SIGN">待签约</option>
            <option value="SIGNING">签约中</option><option value="EFFECTIVE">履约中</option>
            <option value="RENEWING">续签中</option><option value="EXPIRED">已到期</option>
            <option value="TERMINATED">已终止</option><option value="CANCELLED">已作废</option></select></div>
        <div class="fld"><label>房源ID</label><input id="ctFHouse" placeholder="可选"></div>
        <button class="act" onclick="listContract()">查询</button>
      </div>
      <div class="hint">VO 含派生 <code>daysToExpire</code> / <code>expiringSoon</code>（30 天内到期预警）/ <code>occupying</code>（是否占房）。</div>
    </div>
  </div>

  <!-- ==================== 退租 ==================== -->
  <div class="panel" id="p-term">
    <div class="card">
      <h3>申请退租 <span class="m post">POST</span> /api/v1/terminations</h3>
      <div class="row">
        <div class="fld"><label>合同ID *</label><input id="tmContract" value="2001"></div>
        <div class="fld"><label>房源ID *</label><input id="tmHouse" value="5001"></div>
        <div class="fld"><label>承租人 *</label><input id="tmPerson" value="4001"></div>
        <div class="fld"><label>退租类型 *</label>
          <select id="tmType"><option value="NORMAL">NORMAL 正常退租</option>
            <option value="EXPEL">EXPEL 违规清退（5年禁申）</option>
            <option value="EXPIRE">EXPIRE 到期不续</option>
            <option value="EXCHANGE">EXCHANGE 换房退出</option>
            <option value="OTHER">OTHER 其他</option></select></div>
        <div class="fld"><label>计划退房日</label><input id="tmPlan" value="2026-11-30"></div>
        <div class="fld"><label>搬迁期(月)</label><input id="tmReloc" placeholder="成都≤6"></div>
        <button class="act" onclick="createTerm()">申请</button>
      </div>
      <div class="hint">
        重庆：腾退自动给 <b>3 个月过渡期</b>、租金 <b>1.5 倍</b>。成都：搬迁期可选，<b>上限 6 个月</b>。
      </div>
    </div>

    <div class="card">
      <h3>退租流程</h3>
      <div class="row">
        <div class="fld"><label>退租单ID *</label><input id="tmId" placeholder="申请后自动填" style="min-width:190px"></div>
        <div class="fld"><label>验房状态</label>
          <select id="tmInspect"><option value="PASSED">PASSED 通过</option>
            <option value="ABNORMAL">ABNORMAL 有异常</option>
            <option value="PENDING">PENDING 待验房</option></select></div>
        <div class="fld"><label>损坏赔偿</label><input id="tmDamage" value="0"></div>
        <div class="fld"><label>押金退还</label><input id="tmRefund" value="2000"></div>
        <div class="fld"><label>欠费</label><input id="tmArrears" value="0"></div>
        <div class="fld"><label>实际退房日</label><input id="tmActual" placeholder="2026-11-28"></div>
      </div>
      <div class="row">
        <button class="act" onclick="tmAction('submit')">提交审批</button>
        <button class="act" onclick="tmApprove()">批准</button>
        <button class="act red" onclick="tmReject()">驳回</button>
        <button class="act" onclick="tmInspectIt()">验房</button>
        <button class="act" onclick="tmSettle()">结算</button>
      </div>
      <div class="row">
        <button class="act" onclick="tmRelease(true, true)">标记房源已释放+授权已回收</button>
        <button class="act" onclick="tmComplete()">⭐ 办结</button>
      </div>
      <div class="hint">
        <b>办结四前置（缺一不可）</b>：验房通过 + 结算完成 + 房源已释放 + 授权已回收。<br>
        结算公式：<code>押金退还 - 欠费 - 损坏赔偿</code>（正数退还，负数补缴）。
      </div>
    </div>

    <div class="card">
      <h3>退租列表 <span class="m get">GET</span> /api/v1/terminations</h3>
      <div class="row">
        <div class="fld"><label>状态</label>
          <select id="tmFSt"><option value="">全部</option>
            <option value="APPLYING">申请中</option><option value="APPROVING">审批中</option>
            <option value="APPROVED">已批准</option><option value="COMPLETED">已完成</option>
            <option value="REJECTED">已驳回</option><option value="CANCELLED">已取消</option></select></div>
        <div class="fld"><label>类型</label>
          <select id="tmFType"><option value="">全部</option><option value="NORMAL">正常退租</option>
            <option value="EXPEL">违规清退</option><option value="EXPIRE">到期不续</option>
            <option value="EXCHANGE">换房退出</option></select></div>
        <button class="act" onclick="listTerm()">查询</button>
      </div>
      <div class="hint">VO 含派生 <code>readyToComplete</code>（四前置是否齐备）与 <code>overdueExit</code>（逾期未退房）。</div>
    </div>
  </div>

'''
s = s.replace(anchor, panels + anchor, 1)

# 3) JS
anchor_js = '// ---------- 驾驶舱 ----------'
assert anchor_js in s
js = '''// ---------- 申请 ----------
function createApp() {
  const b = { orgId: Number($('apOrg').value), personId: Number($('apPerson').value),
              securityType: $('apType').value, securityMode: $('apMode').value,
              applyChannel: 'ONLINE', familySize: Number($('apFamily').value),
              complianceCommitFlag: 1, dataShareAgreeFlag: 1 };
  if ($('apIncome').value.trim()) b.declaredIncome = $('apIncome').value.trim();
  if ($('apDistrict').value.trim()) b.intentDistrict = $('apDistrict').value.trim();
  if ($('apLayout').value.trim()) b.intentLayout = $('apLayout').value.trim();
  if ($('apAmin').value.trim()) b.intentAreaMin = $('apAmin').value.trim();
  if ($('apAmax').value.trim()) b.intentAreaMax = $('apAmax').value.trim();
  return req('POST', '/api/v1/applications', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('apId').value = id;
  });
}

function acceptApp() {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填申请 ID</span>'; return; }
  return req('POST', '/api/v1/applications/' + id + '/accept', { userId: 9002 });
}

function reviewApp() {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填申请 ID</span>'; return; }
  const b = { stage: $('apStage').value, result: $('apResult').value,
              opinion: $('apOpinion').value.trim() };
  if ($('apDept').value.trim()) b.dept = $('apDept').value.trim();
  if ($('apResult').value === 'SUPPLEMENT') b.supplementDemand = $('apOpinion').value.trim();
  if ($('apResult').value === 'REJECT') b.rejectReason = $('apOpinion').value.trim();
  const q = '?userId=9001&userName=' + encodeURIComponent('审核员');
  return req('POST', '/api/v1/applications/' + id + '/review' + q, b);
}

function resubmitApp() {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填申请 ID</span>'; return; }
  return req('POST', '/api/v1/applications/' + id + '/resubmit');
}

function cancelApp() {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填申请 ID</span>'; return; }
  return req('POST', '/api/v1/applications/' + id + '/cancel', { reason: '申请人撤回' });
}

function appReviews() {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填申请 ID</span>'; return; }
  return req('GET', '/api/v1/applications/' + id + '/reviews');
}

function listApp() {
  let q = 'pageNum=1&pageSize=20';
  if ($('apFSt').value) q += '&status=' + $('apFSt').value;
  return req('GET', '/api/v1/applications?' + q);
}

// ---------- 合同 ----------
function createContract() {
  const b = { contractType: $('ctType').value,
              orgId: Number($('ctOrg').value), lessorOrgId: Number($('ctLessor').value),
              lesseePersonId: Number($('ctLessee').value),
              lesseeName: $('ctName').value.trim(),
              houseId: Number($('ctHouse').value), spaceId: Number($('ctSpace').value),
              houseAddress: '1幢1单元1层101室', houseArea: '89.50',
              leaseStart: $('ctStart').value, leaseEnd: $('ctEnd').value,
              rentPrice: $('ctPrice').value, rentUnit: 'HOUSE_MONTH',
              monthlyRent: $('ctRent').value, depositAmount: $('ctDeposit').value,
              subsidyAmount: $('ctSubsidy').value,
              payCycle: 'MONTH', payDay: 5, signType: $('ctSign').value };
  return req('POST', '/api/v1/contracts', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('ctId').value = id;
  });
}

function ctAction(act) {
  const id = $('ctId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填合同 ID</span>'; return; }
  if (act === 'terminate') {
    return req('POST', '/api/v1/contracts/' + id + '/terminate',
               { reason: $('ctReason').value.trim() });
  }
  if (act === 'cancel') {
    return req('POST', '/api/v1/contracts/' + id + '/cancel',
               { reason: $('ctReason').value.trim() });
  }
  if (act === 'start-signing') {
    return req('POST', '/api/v1/contracts/' + id + '/start-signing', { signVendor: 'QYS' });
  }
  return req('POST', '/api/v1/contracts/' + id + '/' + act, {});
}

function ctSignContract() {
  const id = $('ctId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填合同 ID</span>'; return; }
  return req('POST', '/api/v1/contracts/' + id + '/sign',
             { signFileUrl: 'https://x/contract.pdf', signFlowId: 'FLOW-1' });
}

function ctRenew() {
  const id = $('ctId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填合同 ID</span>'; return; }
  const b = {};
  if ($('ctNewEnd').value.trim()) b.newLeaseEnd = $('ctNewEnd').value.trim();
  if ($('ctNewRent').value.trim()) b.newMonthlyRent = $('ctNewRent').value.trim();
  return req('POST', '/api/v1/contracts/' + id + '/renew', b);
}

function ctExpire() {
  return req('POST', '/api/v1/contracts/expire-due', {});
}

function listContract() {
  let q = 'pageNum=1&pageSize=20';
  if ($('ctFSt').value) q += '&status=' + $('ctFSt').value;
  if ($('ctFHouse').value.trim()) q += '&houseId=' + $('ctFHouse').value.trim();
  return req('GET', '/api/v1/contracts?' + q);
}

// ---------- 退租 ----------
function createTerm() {
  const b = { contractId: Number($('tmContract').value),
              houseId: Number($('tmHouse').value),
              personId: Number($('tmPerson').value),
              terminationType: $('tmType').value,
              exitReason: '承租人申请退租' };
  if ($('tmPlan').value.trim()) b.planExitDate = $('tmPlan').value.trim();
  if ($('tmReloc').value.trim()) b.relocationMonths = Number($('tmReloc').value);
  return req('POST', '/api/v1/terminations', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('tmId').value = id;
  });
}

function tmAction(act) {
  const id = $('tmId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退租单 ID</span>'; return; }
  return req('POST', '/api/v1/terminations/' + id + '/' + act, {});
}

function tmApprove() {
  const id = $('tmId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退租单 ID</span>'; return; }
  return req('POST', '/api/v1/terminations/' + id + '/approve', { reason: '同意退租' });
}

function tmReject() {
  const id = $('tmId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退租单 ID</span>'; return; }
  return req('POST', '/api/v1/terminations/' + id + '/reject', { reason: '材料不全' });
}

function tmInspectIt() {
  const id = $('tmId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退租单 ID</span>'; return; }
  return req('POST', '/api/v1/terminations/' + id + '/inspect',
             { inspectStatus: $('tmInspect').value, inspectResult: '验收记录',
               damageAmount: $('tmDamage').value });
}

function tmSettle() {
  const id = $('tmId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退租单 ID</span>'; return; }
  return req('POST', '/api/v1/terminations/' + id + '/settle',
             { depositRefund: $('tmRefund').value, arrearsAmount: $('tmArrears').value });
}

function tmRelease(house, grant) {
  const id = $('tmId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退租单 ID</span>'; return; }
  return req('POST', '/api/v1/terminations/' + id + '/mark-released',
             { houseReleased: house, grantRevoked: grant });
}

function tmComplete() {
  const id = $('tmId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填退租单 ID</span>'; return; }
  const b = {};
  if ($('tmActual').value.trim()) b.actualExitDate = $('tmActual').value.trim();
  return req('POST', '/api/v1/terminations/' + id + '/complete', b);
}

function listTerm() {
  let q = 'pageNum=1&pageSize=20';
  if ($('tmFSt').value) q += '&status=' + $('tmFSt').value;
  if ($('tmFType').value) q += '&type=' + $('tmFType').value;
  return req('GET', '/api/v1/terminations?' + q);
}

// ---------- 驾驶舱 ----------'''
s = s.replace(anchor_js, js, 1)

# 4) 接口清单
s = s.replace('<b>投诉</b>　POST /api/v1/complaints',
              '<b>申请</b>　POST /api/v1/applications ｜ GET /api/v1/applications ｜ POST .../accept ｜ .../review ｜ .../resubmit ｜ .../cancel ｜ GET .../reviews<br>\n'
              '        <b>合同</b>　POST /api/v1/contracts ｜ GET /api/v1/contracts ｜ POST .../submit-sign ｜ .../start-signing ｜ .../sign ｜ .../renew ｜ .../terminate ｜ .../cancel ｜ POST /api/v1/contracts/expire-due<br>\n'
              '        <b>退租</b>　POST /api/v1/terminations ｜ GET /api/v1/terminations ｜ POST .../submit ｜ .../approve ｜ .../reject ｜ .../cancel ｜ .../inspect ｜ .../settle ｜ .../mark-released ｜ .../complete ｜ .../register-enforce<br>\n'
              '        <b>投诉</b>　POST /api/v1/complaints', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已加申请/合同/退租页，文件长度', len(s))
