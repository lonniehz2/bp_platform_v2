# -*- coding: utf-8 -*-
"""给验证台加「配租」标签页"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'id="p-alloc"' in s:
    print('已存在，跳过')
    raise SystemExit

# 1) 标签按钮
s = s.replace('    <button data-t="p-fin">财务</button>',
              '    <button data-t="p-alloc">配租</button>\n'
              '    <button data-t="p-fin">财务</button>', 1)

# 2) 面板
anchor = '  <!-- ==================== 财务 ==================== -->'
assert anchor in s

panel = '''  <!-- ==================== 配租 ==================== -->
  <div class="panel" id="p-alloc">
    <div class="card">
      <h3>① 轮候入库（申请通过后）</h3>
      <div class="row">
        <div class="fld"><label>人员ID *</label><input id="wqPerson" value="4001"></div>
        <div class="fld"><label>申请单ID *</label><input id="wqApp" value="8001"></div>
        <div class="fld"><label>保障类型 *</label>
          <select id="wqType"><option value="PUBLIC">PUBLIC 公租房</option>
            <option value="AFFORDABLE">AFFORDABLE 保租房</option>
            <option value="TALENT">TALENT 人才公寓</option>
            <option value="LOW_RENT">LOW_RENT 廉租</option></select></div>
        <div class="fld"><label>组织ID</label><input id="wqOrg" value="7001"></div>
        <div class="fld"><label>优先分</label><input id="wqPri" value="0"></div>
        <button class="act" onclick="enterQueue()">入轮候</button>
        <button class="act gray" onclick="listWaiting()">轮候名单</button>
        <button class="act gray" onclick="recalcRank()">重算排名</button>
      </div>
      <div class="row">
        <div class="fld"><label>轮候ID *</label><input id="wqId" placeholder="入队后自动填" style="min-width:190px"></div>
        <button class="act" onclick="wqAction('freeze')">冻结</button>
        <button class="act" onclick="wqAction('unfreeze')">解冻</button>
        <button class="act red" onclick="wqAction('exit')">退出轮候</button>
      </div>
      <div class="hint">
        ⭐ <b>总分 = 优先分 + 轮候天数 × 0.1</b>，按总分降序排名。<br>
        权重 0.1 让长期轮候者能逐步追上小幅优先分，避免"优先分一票否决"。
      </div>
    </div>

    <div class="card">
      <h3>② 建配租批次 + 房源入池</h3>
      <div class="row">
        <div class="fld"><label>批次名称 *</label><input id="bthName" value="2026年第一批公租房配租" style="min-width:200px"></div>
        <div class="fld"><label>组织ID *</label><input id="bthOrg" value="7001"></div>
        <div class="fld"><label>保障类型 *</label>
          <select id="bthType"><option value="PUBLIC">PUBLIC 公租房</option>
            <option value="AFFORDABLE">AFFORDABLE</option><option value="TALENT">TALENT</option>
            <option value="LOW_RENT">LOW_RENT</option></select></div>
        <div class="fld"><label>批次类型 *</label>
          <select id="bthMode"><option value="LOTTERY">LOTTERY 摇号</option>
            <option value="SELECT">SELECT 选房</option><option value="DIRECT">DIRECT 直接配租</option>
            <option value="SUPPLEMENT">SUPPLEMENT 递补</option></select></div>
        <div class="fld"><label>房源ID(逗号分隔)</label><input id="bthHouses" placeholder="5001,5002" style="min-width:150px"></div>
        <div class="fld"><label>公证信息</label><input id="bthNotary" placeholder="公证处/公证员/公证书号" style="min-width:180px"></div>
        <button class="act" onclick="createBatch()">建批次</button>
      </div>
      <div class="row">
        <div class="fld"><label>批次ID *</label><input id="bthId" placeholder="建后自动填" style="min-width:190px"></div>
        <button class="act" onclick="bthStatus('PUBLISHED')">发布</button>
        <button class="act" onclick="bthStatus('SIGNUP')">报名中</button>
        <button class="act" onclick="bthStatus('SELECTING')">选房中</button>
        <button class="act red" onclick="bthStatus('CANCELLED')">取消</button>
        <button class="act gray" onclick="addHouses()">加房源</button>
        <button class="act gray" onclick="listBatchHouses()">房源池</button>
      </div>
      <div class="hint">
        状态机：<code>草稿 → 已发布 → 报名中 → 摇号 → 摇号完成 → 选房中 → 已配租 → 已结束</code>，不可跳步。<br>
        <b>房源池</b>四种状态：<code>AVAILABLE 可选 / LOCKED 已锁定 / SELECTED 已选中 / REMOVED 已移出</code>
      </div>
    </div>

    <div class="card">
      <h3>③ 摇号 <span class="m post">POST</span> /api/v1/allocation/lottery</h3>
      <div class="row">
        <div class="fld"><label>批次ID *</label><input id="lotBatch" placeholder="同步批次ID" style="min-width:190px"></div>
        <div class="fld"><label>随机种子</label><input id="lotSeed" value="SEED-2026-001" style="min-width:170px"></div>
        <div class="fld"><label>公证信息</label><input id="lotNotary" placeholder="可留空" style="min-width:170px"></div>
        <button class="act" onclick="runLottery()">⭐ 执行摇号</button>
        <button class="act gray" onclick="listLottery()">查看结果</button>
      </div>
      <div class="hint">
        ⭐ 排序：<b>总分降序 → 入队时间升序 → 种子伪随机</b>。中签数 = 房源数，其后 <b>3 名为「递补」</b>。<br>
        种子落库<b>可复现、可公证</b>；已摇过的批次<b>不可重复摇号</b>（幂等）。
      </div>
    </div>

    <div class="card">
      <h3>④ 配租与签约</h3>
      <div class="row">
        <div class="fld"><label>批次ID *</label><input id="alBatch" placeholder="同步批次ID" style="min-width:190px"></div>
        <div class="fld"><label>房源ID *</label><input id="alHouse" placeholder="批次内房源" style="min-width:150px"></div>
        <div class="fld"><label>承租人 *</label><input id="alPerson" placeholder="中签人personId" style="min-width:150px"></div>
        <div class="fld"><label>计划起租日</label><input id="alStart" value="2026-12-01"></div>
        <div class="fld"><label>计划止租日</label><input id="alEnd" value="2027-11-30"></div>
        <div class="fld"><label>锁定小时</label><input id="alLock" placeholder="默认72"></div>
        <button class="act" onclick="allocate()">生成配租单</button>
      </div>
      <div class="row">
        <div class="fld"><label>配租单ID *</label><input id="alId" placeholder="生成后自动填" style="min-width:190px"></div>
        <button class="act" onclick="alAction('sign')">⭐ 签约</button>
        <button class="act red" onclick="alAction('give-up')">放弃（房源回池）</button>
        <button class="act gray" onclick="releaseExpired()">超时释放扫描</button>
        <button class="act gray" onclick="listAllocations()">配租列表</button>
      </div>
      <div class="hint">
        <b>锁定机制</b>：配租单生成即锁定房源，默认 <b>72 小时</b>未签约自动释放（解决"占房不签"）。<br>
        <code>待签约 PENDING_SIGN → 已签约 SIGNED</code>；放弃/超时 → 房源回到 <code>AVAILABLE</code>，递补者可补位。<br>
        VO 派生 <code>lockRemainHours</code>（剩余锁定小时）、<code>lockOverdue</code>（是否已超时）。
      </div>
    </div>
  </div>

'''
s = s.replace(anchor, panel + anchor, 1)

# 3) JS
js_anchor = '// ---------- 财务：账单 ----------'
assert js_anchor in s
js = '''// ---------- 配租 ----------
function enterQueue() {
  const b = { personId: Number($('wqPerson').value), applicationId: Number($('wqApp').value),
              securityType: $('wqType').value, priorityScore: $('wqPri').value };
  if ($('wqOrg').value.trim()) b.orgId = Number($('wqOrg').value);
  return req('POST', '/api/v1/allocation/waiting', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('wqId').value = d.id;
  });
}
function listWaiting() {
  let q = 'pageNum=1&pageSize=20';
  if ($('wqType').value) q += '&securityType=' + $('wqType').value;
  if ($('wqOrg').value.trim()) q += '&orgId=' + $('wqOrg').value.trim();
  return req('GET', '/api/v1/allocation/waiting?' + q);
}
function recalcRank() {
  let q = '';
  if ($('wqType').value) q += 'securityType=' + $('wqType').value + '&';
  if ($('wqOrg').value.trim()) q += 'orgId=' + $('wqOrg').value.trim();
  return req('POST', '/api/v1/allocation/waiting/recalc?' + q, {});
}
function wqAction(act) {
  const id = $('wqId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填轮候 ID</span>'; return; }
  if (act === 'unfreeze') return req('POST', '/api/v1/allocation/waiting/' + id + '/unfreeze', {});
  return req('POST', '/api/v1/allocation/waiting/' + id + '/' + act,
             { reason: act === 'exit' ? '主动退出轮候' : '材料待核' });
}

function createBatch() {
  const b = { batchName: $('bthName').value.trim(), orgId: Number($('bthOrg').value),
              securityType: $('bthType').value, batchType: $('bthMode').value };
  const hs = $('bthHouses').value.trim();
  if (hs) b.houseIds = hs.split(',').map(x => Number(x.trim())).filter(x => x > 0);
  if ($('bthNotary').value.trim()) b.notaryInfo = $('bthNotary').value.trim();
  return req('POST', '/api/v1/allocation/batches', b).then(j => {
    const d = j && j.data;
    if (d && d.id) {
      $('bthId').value = d.id; $('lotBatch').value = d.id; $('alBatch').value = d.id;
    }
  });
}
function bthStatus(st) {
  const id = $('bthId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填批次 ID</span>'; return; }
  return req('POST', '/api/v1/allocation/batches/' + id + '/status', { batchStatus: st });
}
function addHouses() {
  const id = $('bthId').value.trim();
  const hs = $('bthHouses').value.trim();
  if (!id || !hs) { out.innerHTML = '<span class="err">请填批次 ID 与房源 ID</span>'; return; }
  return req('POST', '/api/v1/allocation/batches/' + id + '/houses',
             { houseIds: hs.split(',').map(x => Number(x.trim())).filter(x => x > 0) });
}
function listBatchHouses() {
  const id = $('bthId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填批次 ID</span>'; return; }
  return req('GET', '/api/v1/allocation/batches/' + id + '/houses');
}

function runLottery() {
  const id = $('lotBatch').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填批次 ID</span>'; return; }
  const b = { batchId: Number(id) };
  if ($('lotSeed').value.trim()) b.seed = $('lotSeed').value.trim();
  if ($('lotNotary').value.trim()) b.notaryInfo = $('lotNotary').value.trim();
  return req('POST', '/api/v1/allocation/lottery', b);
}
function listLottery() {
  const id = $('lotBatch').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填批次 ID</span>'; return; }
  return req('GET', '/api/v1/allocation/lottery/' + id);
}

function allocate() {
  const b = { batchId: Number($('alBatch').value), houseId: Number($('alHouse').value),
              personId: Number($('alPerson').value) };
  if ($('alStart').value.trim()) b.planRentStart = $('alStart').value.trim();
  if ($('alEnd').value.trim()) b.planRentEnd = $('alEnd').value.trim();
  if ($('alLock').value.trim()) b.lockHours = Number($('alLock').value);
  return req('POST', '/api/v1/allocation/allocations', b).then(j => {
    const d = j && j.data;
    if (d && d.id) $('alId').value = d.id;
  });
}
function alAction(act) {
  const id = $('alId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填配租单 ID</span>'; return; }
  if (act === 'sign') return req('POST', '/api/v1/allocation/allocations/' + id + '/sign', {});
  return req('POST', '/api/v1/allocation/allocations/' + id + '/give-up',
             { reason: '承租人放弃' });
}
function releaseExpired() {
  return req('POST', '/api/v1/allocation/allocations/release-expired', {});
}
function listAllocations() {
  let q = 'pageNum=1&pageSize=20';
  if ($('alBatch').value.trim()) q += '&batchId=' + $('alBatch').value.trim();
  if ($('alPerson').value.trim()) q += '&personId=' + $('alPerson').value.trim();
  return req('GET', '/api/v1/allocation/allocations?' + q);
}

// ---------- 财务：账单 ----------'''
s = s.replace(js_anchor, js, 1)

# 4) 接口清单
s = s.replace('<b>财务</b>　POST /api/v1/fin/bills',
              '<b>配租</b>　POST /api/v1/allocation/waiting ｜ GET .../waiting ｜ .../recalc ｜ .../freeze ｜ .../unfreeze ｜ .../exit ｜ '
              'POST /api/v1/allocation/batches ｜ GET .../batches ｜ .../houses ｜ .../status ｜ '
              'POST /api/v1/allocation/lottery ｜ GET .../lottery/{batchId} ｜ '
              'POST /api/v1/allocation/allocations ｜ GET .../allocations ｜ .../sign ｜ .../give-up ｜ .../release-expired<br>\n'
              '        <b>财务</b>　POST /api/v1/fin/bills', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已加配租页，文件长度', len(s))
