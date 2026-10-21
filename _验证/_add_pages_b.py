# -*- coding: utf-8 -*-
"""补齐 7 个页面的 JS 逻辑"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'function createPublicity' in s:
    print('已存在，跳过')
    raise SystemExit

anchor = '// ---------- 配租 ----------'
assert anchor in s

js = '''// ---------- 合同：同住人 ----------
function chContractId() { return $('chContract').value.trim(); }
function addCohabitant() {
  const cid = chContractId();
  if (!cid) { out.innerHTML = '<span class="err">请填合同 ID</span>'; return; }
  const b = { memberName: $('chName').value.trim(), relation: $('chRel').value };
  if ($('chMask').value.trim()) b.idCardMask = $('chMask').value.trim();
  return req('POST', '/api/v1/contracts/' + cid + '/cohabitants', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('chId').value = d.id;
  });
}
function listCohabitant() {
  const cid = chContractId();
  if (!cid) { out.innerHTML = '<span class="err">请填合同 ID</span>'; return; }
  return req('GET', '/api/v1/contracts/' + cid + '/cohabitants');
}
function householdSize() {
  const cid = chContractId();
  if (!cid) { out.innerHTML = '<span class="err">请填合同 ID</span>'; return; }
  return req('GET', '/api/v1/contracts/' + cid + '/cohabitants/household-size');
}
function grantCohabitant(on) {
  const cid = chContractId(), id = $('chId').value.trim();
  if (!cid || !id) { out.innerHTML = '<span class="err">请填合同ID与同住人ID</span>'; return; }
  return req('POST', '/api/v1/contracts/' + cid + '/cohabitants/' + id + '/grant',
             { granted: on });
}
function removeCohabitant() {
  const cid = chContractId(), id = $('chId').value.trim();
  if (!cid || !id) { out.innerHTML = '<span class="err">请填合同ID与同住人ID</span>'; return; }
  return req('DELETE', '/api/v1/contracts/' + cid + '/cohabitants/' + id);
}

// ---------- 合同：变更 ----------
function createChange() {
  const cid = $('cgContract').value.trim();
  if (!cid) { out.innerHTML = '<span class="err">请填合同 ID</span>'; return; }
  const b = { changeType: $('cgType').value, changeReason: $('cgReason').value.trim() };
  if ($('cgRent').value.trim()) b.newMonthlyRent = $('cgRent').value.trim();
  if ($('cgEnd').value.trim()) b.newLeaseEnd = $('cgEnd').value.trim();
  return req('POST', '/api/v1/contracts/' + cid + '/changes', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('cgId').value = d.id;
  });
}
function cgAction(act) {
  const id = $('cgId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填变更单 ID</span>'; return; }
  if (act === 'reject') {
    return req('POST', '/api/v1/contract-changes/' + id + '/reject', { reason: '无政策依据' });
  }
  return req('POST', '/api/v1/contract-changes/' + id + '/approve', {});
}
function listChange() {
  const cid = $('cgContract').value.trim();
  let q = 'pageNum=1&pageSize=20';
  if (cid) q += '&contractId=' + cid;
  return req('GET', '/api/v1/contract-changes?' + q);
}

// ---------- 合同：换房 ----------
function applyExchange() {
  const b = { personId: Number($('exPerson').value),
              oldContractId: Number($('exOldContract').value),
              oldHouseId: Number($('exOldHouse').value),
              newHouseId: Number($('exNewHouse').value),
              exchangeType: $('exType').value,
              exchangeReason: '家庭人口变化需换房',
              exchangeReasonCode: 'COHABIT',
              forceExchange: $('exForced').value === '1' };
  return req('POST', '/api/v1/exchanges', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('exId').value = d.id;
  });
}
function exAction(act) {
  const id = $('exId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填换房单 ID</span>'; return; }
  if (act === 'reject') {
    return req('POST', '/api/v1/exchanges/' + id + '/reject', { reason: '不符合换房条件' });
  }
  if (act === 'approve') {
    return req('POST', '/api/v1/exchanges/' + id + '/approve', { reason: '符合换房条件' });
  }
  return req('POST', '/api/v1/exchanges/' + id + '/submit', {});
}
function exComplete() {
  const id = $('exId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填换房单 ID</span>'; return; }
  return req('POST', '/api/v1/exchanges/' + id + '/complete', {});
}
function exNoExchange() {
  const id = $('exId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填换房单 ID</span>'; return; }
  return req('POST', '/api/v1/exchanges/' + id + '/no-exchange',
             { reason: '住户拒绝换房，继续占用大户型' });
}

// ---------- 公示 ----------
function createPublicity() {
  const b = { publicityType: $('pbType').value, title: $('pbTitle').value.trim(),
              content: $('pbContent').value.trim(),
              startDate: $('pbStart').value.trim(), endDate: $('pbEnd').value.trim() };
  if ($('pbOrg').value.trim()) b.orgId = Number($('pbOrg').value);
  return req('POST', '/api/v1/publicities', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('pbId').value = d.id;
  });
}
function pbAction(act) {
  const id = $('pbId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填公示 ID</span>'; return; }
  if (act === 'close') {
    return req('POST', '/api/v1/publicities/' + id + '/close', { remark: '公示期满无异议' });
  }
  return req('POST', '/api/v1/publicities/' + id + '/publish', {});
}
function listPublicity() {
  let q = 'pageNum=1&pageSize=20';
  if ($('pbType').value) q += '&type=' + $('pbType').value;
  return req('GET', '/api/v1/publicities?' + q);
}
function checkAllocPub() {
  const org = $('pbOrg').value.trim();
  return req('GET', '/api/v1/publicities/allocation-check' + (org ? '?orgId=' + org : ''));
}

// ---------- 年审 ----------
function createReview() {
  const b = { personId: Number($('rvPerson').value), reviewYear: $('rvYear').value.trim(),
              reviewType: $('rvType').value };
  if ($('rvContract').value.trim()) b.contractId = Number($('rvContract').value);
  if ($('rvHouse').value.trim()) b.houseId = Number($('rvHouse').value);
  return req('POST', '/api/v1/annual-reviews', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('rvId').value = d.id;
  });
}
function reviewAction(act) {
  const id = $('rvId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填复核单 ID</span>'; return; }
  return req('POST', '/api/v1/annual-reviews/' + id + '/' + act, {});
}
function finishReview() {
  const id = $('rvId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填复核单 ID</span>'; return; }
  const b = { reviewResult: $('rvResult').value,
              checkResult: JSON.stringify({ income: 9000, limit: 6000 }) };
  const adj = $('rvAdjust').value.trim();
  if (adj) b.adjustContent = adj;
  return req('POST', '/api/v1/annual-reviews/' + id + '/finish', b);
}
function reviewBatch() {
  return req('POST', '/api/v1/annual-reviews/batch', {
    reviewYear: $('rvYear').value.trim(), dryRun: true });
}

// ---------- 复议 ----------
function submitAppeal() {
  const b = { bizType: $('apBizType').value, bizId: Number($('apBizId').value),
              personId: Number($('apPerson').value), appealType: $('apType').value,
              appealReason: $('apReason').value.trim() };
  if ($('apDays').value.trim()) b.daysFromNow = Number($('apDays').value);
  return req('POST', '/api/v1/appeals', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('apId').value = d.id;
  });
}
function apAction(act) {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填申诉单 ID</span>'; return; }
  if (act === 'withdraw') {
    return req('POST', '/api/v1/appeals/' + id + '/withdraw', { reason: '已线下沟通解决' });
  }
  return req('POST', '/api/v1/appeals/' + id + '/' + act, { userId: 9001 });
}
function decideAppeal() {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填申诉单 ID</span>'; return; }
  return req('POST', '/api/v1/appeals/' + id + '/decide', {
    decision: $('apDecision').value, resultEffect: $('apEffect').value,
    reviewOpinion: $('apOpinion').value.trim(), handleResult: '经核实相关材料',
    handleUserId: 9003 });
}
function apNotify() {
  const id = $('apId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填申诉单 ID</span>'; return; }
  return req('POST', '/api/v1/appeals/' + id + '/notify', {});
}
function listAppeal() {
  let q = 'pageNum=1&pageSize=20';
  if ($('apPerson').value.trim()) q += '&personId=' + $('apPerson').value.trim();
  return req('GET', '/api/v1/appeals?' + q);
}

// ---------- 信用 ----------
function recordCredit() {
  const b = { personId: Number($('ctPerson').value), violationType: $('ctViolation').value,
              sanctionType: $('ctSanction').value, violationDesc: $('ctDesc').value.trim(),
              decideUserId: 9003 };
  if ($('ctYears').value.trim()) b.banYears = Number($('ctYears').value);
  if ($('ctDoc').value.trim()) b.legalDocNo = $('ctDoc').value.trim();
  if ($('ctPlatform').value.trim()) {
    b.pushPlatform = $('ctPlatform').value.trim();
    b.pushToPlatform = true;
  }
  return req('POST', '/api/v1/credits', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('ctId').value = d.id;
  });
}
function ctAction(act) {
  const id = $('ctId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填信用记录 ID</span>'; return; }
  if (act === 'revoke') {
    return req('POST', '/api/v1/credits/' + id + '/revoke', { reason: '复议认定证据不足' });
  }
  return req('POST', '/api/v1/credits/' + id + '/expire', {});
}
function ctPush() {
  const id = $('ctId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请填信用记录 ID</span>'; return; }
  return req('POST', '/api/v1/credits/' + id + '/push',
             { success: true, platform: $('ctPlatform').value.trim() });
}
function listCredit() {
  const p = $('ctPerson').value.trim();
  return req('GET', '/api/v1/credits/by-person/' + p);
}
function checkBan() {
  const p = $('ctCheck').value.trim();
  if (!p) { out.innerHTML = '<span class="err">请填人员 ID</span>'; return; }
  return req('GET', '/api/v1/credits/check-ban?personId=' + p);
}
function scanCreditExpired() {
  return req('POST', '/api/v1/credits/scan-expired', {});
}

// ---------- 配租 ----------'''
s = s.replace(anchor, js, 1)

# 接口清单补充
s = s.replace('<b>配租</b>　POST /api/v1/allocation/waiting',
              '<b>公示</b>　POST /api/v1/publicities ｜ GET /api/v1/publicities ｜ .../publish ｜ .../close ｜ GET .../allocation-check<br>\n'
              '        <b>年审</b>　POST /api/v1/annual-reviews ｜ GET .../annual-reviews ｜ .../start ｜ .../finish ｜ .../batch ｜ .../mark-overdue ｜ POST .../rent-change<br>\n'
              '        <b>复议</b>　POST /api/v1/appeals ｜ GET /api/v1/appeals ｜ .../by-biz ｜ .../accept ｜ .../investigate ｜ .../decide ｜ .../withdraw ｜ .../notify<br>\n'
              '        <b>信用</b>　POST /api/v1/credits ｜ GET /api/v1/credits ｜ .../by-person/{id} ｜ .../check-ban ｜ .../revoke ｜ .../expire ｜ .../push<br>\n'
              '        <b>同住人</b>　POST /api/v1/contracts/{id}/cohabitants ｜ GET ... ｜ .../household-size ｜ .../grant ｜ DELETE .../{id}<br>\n'
              '        <b>变更</b>　POST /api/v1/contracts/{id}/changes ｜ GET /api/v1/contract-changes ｜ .../approve ｜ .../reject<br>\n'
              '        <b>换房</b>　POST /api/v1/exchanges ｜ GET /api/v1/exchanges ｜ .../submit ｜ .../approve ｜ .../complete ｜ .../no-exchange ｜ GET .../count<br>\n'
              '        <b>配租</b>　POST /api/v1/allocation/waiting', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('JS 已加，当前长度', len(s))
