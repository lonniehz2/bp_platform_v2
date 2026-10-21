# -*- coding: utf-8 -*-
"""给验证台加「投诉」+「走访」标签页"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'id="p-complaint"' in s:
    print('已存在，跳过')
    raise SystemExit

# 1) 标签
s = s.replace('    <button data-t="p-wo">工单</button>',
              '    <button data-t="p-wo">工单</button>\n'
              '    <button data-t="p-complaint">投诉</button>\n'
              '    <button data-t="p-visit">走访</button>', 1)

# 2) 面板
anchor = '  <!-- ==================== 健康 ==================== -->'
assert anchor in s

panels = '''  <!-- ==================== 投诉 ==================== -->
  <div class="panel" id="p-complaint">
    <div class="card">
      <h3>提交投诉/建议 <span class="m post">POST</span> /api/v1/complaints</h3>
      <div class="row">
        <div class="fld"><label>类型 *</label>
          <select id="cpType">
            <option value="COMPLAINT">COMPLAINT 投诉（48h未处理算超时）</option>
            <option value="SUGGEST">SUGGEST 建议</option>
            <option value="CONSULT">CONSULT 咨询</option>
            <option value="PRAISE">PRAISE 表扬</option>
          </select></div>
        <div class="fld"><label>来源</label>
          <select id="cpSrc"><option value="MINIAPP">小程序</option><option value="APP">APP</option>
            <option value="PHONE">电话</option><option value="WALKIN">现场</option>
            <option value="OTHER">其他</option></select></div>
        <div class="fld"><label>标题 *</label>
          <input id="cpTitle" value="楼道灯不亮" style="min-width:200px"></div>
        <div class="fld"><label>提交人</label><input id="cpName" value="张三"></div>
        <div class="fld"><label>电话</label><input id="cpPhone" value="13800138000"></div>
      </div>
      <div class="row">
        <div class="fld"><label>内容</label>
          <input id="cpContent" value="已经坏了三天，无人处理" style="min-width:300px"></div>
        <button class="act" onclick="createComplaint()">提交</button>
        <button class="act gray" onclick="listComplaint()">查询列表</button>
      </div>
      <div class="hint">只有 <code>COMPLAINT</code> 类型参与 48 小时超时判定；建议/咨询/表扬不算超时。</div>
    </div>

    <div class="card">
      <h3>处理流程</h3>
      <div class="row">
        <div class="fld"><label>投诉 ID *</label><input id="cpId" placeholder="提交后自动填" style="min-width:190px"></div>
        <div class="fld"><label>处理人ID</label><input id="cpUid" value="9001"></div>
        <div class="fld"><label>处理结果</label><input id="cpResult" value="已更换灯泡" style="min-width:200px"></div>
        <div class="fld"><label>满意度(1-5)</label><input id="cpSat" value="5"></div>
      </div>
      <div class="row">
        <button class="act" onclick="cpAction('handle')">开始处理</button>
        <button class="act" onclick="cpAction('resolve')">处理完成</button>
        <button class="act" onclick="cpAction('close')">归档</button>
        <button class="act gray" onclick="cpEvaluate()">评价</button>
        <button class="act" onclick="cpToWo()">⭐ 转工单</button>
      </div>
      <div class="hint">
        <code>待处理 → 处理中 → 已处理 → 已归档</code>，不可跳步。
        未处理不能评价；已归档是终态。转工单会生成 <code>COMPLAINT</code> 类型工单（60 分钟响应），同一投诉只能转一次。
      </div>
    </div>

    <div class="card">
      <h3>投诉列表 <span class="m get">GET</span> /api/v1/complaints</h3>
      <div class="row">
        <div class="fld"><label>类型</label>
          <select id="cpFType"><option value="">全部</option><option value="COMPLAINT">投诉</option>
            <option value="SUGGEST">建议</option><option value="CONSULT">咨询</option>
            <option value="PRAISE">表扬</option></select></div>
        <div class="fld"><label>状态</label>
          <select id="cpFSt"><option value="">全部</option><option value="PENDING">待处理</option>
            <option value="HANDLING">处理中</option><option value="HANDLED">已处理</option>
            <option value="CLOSED">已归档</option></select></div>
        <div class="fld"><label>关键词</label><input id="cpKw" placeholder="标题/单号"></div>
        <button class="act" onclick="listComplaint()">查询</button>
      </div>
    </div>
  </div>

  <!-- ==================== 走访 ==================== -->
  <div class="panel" id="p-visit">
    <div class="card">
      <h3>创建走访任务 <span class="m post">POST</span> /api/v1/visits</h3>
      <div class="row">
        <div class="fld"><label>走访类型 *</label>
          <select id="vsType">
            <option value="VERIFY">VERIFY 使用情况核查</option>
            <option value="ROUTINE">ROUTINE 例行巡房</option>
            <option value="ALERT">ALERT 预警核查</option>
            <option value="COMPLAINT">COMPLAINT 投诉核查</option>
            <option value="VACANCY">VACANCY 空置核查</option>
          </select></div>
        <div class="fld"><label>房源ID *</label><input id="vsHouse" value="5001" style="min-width:170px"></div>
        <div class="fld"><label>空间ID</label><input id="vsSpace" placeholder="可选"></div>
        <div class="fld"><label>走访人</label><input id="vsUser" value="李师傅"></div>
        <div class="fld"><label>走访人ID</label><input id="vsUid" value="9001"></div>
      </div>
      <div class="row">
        <div class="fld"><label>触发原因</label>
          <input id="vsReason" value="系统预警长期未开门" style="min-width:240px"></div>
        <div class="fld"><label>关联告警ID</label><input id="vsAlert" placeholder="可选"></div>
        <button class="act" onclick="createVisit()">创建</button>
        <button class="act gray" onclick="listVisit()">查询列表</button>
      </div>
      <div class="hint">
        保障房"使用情况核查"的落地抓手：核实实际居住人是否与合同一致、有无转租转借、是否长期闲置。
      </div>
    </div>

    <div class="card">
      <h3>回填走访结果</h3>
      <div class="row">
        <div class="fld"><label>走访 ID *</label><input id="vsId" placeholder="创建后自动填" style="min-width:190px"></div>
        <div class="fld"><label>走访状态</label>
          <select id="vsStatus"><option value="DONE">DONE 已完成</option>
            <option value="REFUSED">REFUSED 拒访</option><option value="ABSENT">ABSENT 无人</option>
            <option value="CANCELLED">CANCELLED 已取消</option></select></div>
        <div class="fld"><label>是否有人居住</label>
          <select id="vsOccupied"><option value="1">是</option><option value="0">否</option></select></div>
        <div class="fld"><label>实际居住人数</label><input id="vsResidents" value="3"></div>
        <div class="fld"><label>人房匹配</label>
          <select id="vsMatch"><option value="MISMATCH">MISMATCH 不一致</option>
            <option value="MATCH">MATCH 一致</option><option value="UNKNOWN">UNKNOWN 无法确认</option></select></div>
      </div>
      <div class="row">
        <div class="fld"><label>发现转租转借</label>
          <select id="vsSublease"><option value="0">否</option><option value="1">是</option></select></div>
        <div class="fld"><label>发现闲置</label>
          <select id="vsIdle"><option value="0">否</option><option value="1">是</option></select></div>
        <div class="fld"><label>发现违规使用</label>
          <select id="vsIllegal"><option value="0">否</option><option value="1">是</option></select></div>
        <div class="fld"><label>发现情况</label>
          <input id="vsFindings" value="实际居住人与合同不符，疑似转租" style="min-width:250px"></div>
        <div class="fld"><label>后续建议</label><input id="vsNext" value="建议解除合同"></div>
      </div>
      <div class="row">
        <button class="act" onclick="reportVisit()">回填结果</button>
        <button class="act" onclick="vsToWo()">⭐ 异常转工单</button>
        <button class="act red" onclick="vsCancel()">取消走访</button>
      </div>
      <div class="hint">
        <b>未完成不能转工单</b>；已取消不能转工单。命中异常标记时后端会打 WARN 日志。
        转工单生成 <code>INSPECT</code> 类型工单，内容自动汇总异常项。
      </div>
    </div>

    <div class="card">
      <h3>走访列表 <span class="m get">GET</span> /api/v1/visits</h3>
      <div class="row">
        <div class="fld"><label>类型</label>
          <select id="vsFType"><option value="">全部</option><option value="VERIFY">使用核查</option>
            <option value="ROUTINE">例行巡房</option><option value="ALERT">预警核查</option>
            <option value="COMPLAINT">投诉核查</option><option value="VACANCY">空置核查</option></select></div>
        <div class="fld"><label>状态</label>
          <select id="vsFSt"><option value="">全部</option><option value="PENDING">待走访</option>
            <option value="DONE">已完成</option><option value="REFUSED">拒访</option>
            <option value="ABSENT">无人</option><option value="CANCELLED">已取消</option></select></div>
        <div class="fld"><label>关键词</label><input id="vsKw" placeholder="单号/发现情况"></div>
        <button class="act" onclick="listVisit()">查询</button>
      </div>
    </div>
  </div>

'''
s = s.replace(anchor, panels + anchor, 1)

# 3) JS
anchor_js = '// ---------- 健康 ----------'
assert anchor_js in s
js = '''// ---------- 投诉 ----------
function createComplaint() {
  const b = { complaintType: $('cpType').value, source: $('cpSrc').value,
              title: $('cpTitle').value.trim() };
  if ($('cpContent').value.trim()) b.content = $('cpContent').value.trim();
  if ($('cpName').value.trim()) b.submitterName = $('cpName').value.trim();
  if ($('cpPhone').value.trim()) b.submitterPhone = $('cpPhone').value.trim();
  return req('POST', '/api/v1/complaints', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('cpId').value = id;
  });
}

function cpAction(act) {
  const id = $('cpId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填投诉 ID（或先提交投诉）</span>'; return; }
  const uid = Number($('cpUid').value || 0);
  const b = (act === 'resolve')
    ? { handleUserId: uid, result: $('cpResult').value.trim() }
    : { handleUserId: uid };
  return req('POST', '/api/v1/complaints/' + id + '/' + act, b);
}

function cpEvaluate() {
  const id = $('cpId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填投诉 ID</span>'; return; }
  return req('POST', '/api/v1/complaints/' + id + '/evaluate',
             { satisfaction: Number($('cpSat').value || 0) });
}

function cpToWo() {
  const id = $('cpId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填投诉 ID</span>'; return; }
  return req('POST', '/api/v1/complaints/' + id + '/to-workorder',
             { handleUserId: Number($('cpUid').value || 0), action: '管理员' });
}

function listComplaint() {
  let q = 'pageNum=1&pageSize=20';
  if ($('cpFType').value) q += '&type=' + $('cpFType').value;
  if ($('cpFSt').value) q += '&status=' + $('cpFSt').value;
  if ($('cpKw').value.trim()) q += '&keyword=' + encodeURIComponent($('cpKw').value.trim());
  return req('GET', '/api/v1/complaints?' + q);
}

// ---------- 走访 ----------
function createVisit() {
  const b = { visitType: $('vsType').value, houseId: Number($('vsHouse').value || 0) };
  if ($('vsSpace').value.trim()) b.spaceId = Number($('vsSpace').value);
  if ($('vsUid').value.trim()) b.visitUserId = Number($('vsUid').value);
  if ($('vsUser').value.trim()) b.visitUserName = $('vsUser').value.trim();
  if ($('vsReason').value.trim()) b.triggerReason = $('vsReason').value.trim();
  if ($('vsAlert').value.trim()) b.alertId = Number($('vsAlert').value);
  return req('POST', '/api/v1/visits', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('vsId').value = id;
  });
}

function reportVisit() {
  const id = $('vsId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填走访 ID（或先创建任务）</span>'; return; }
  const b = { visitStatus: $('vsStatus').value,
              isOccupied: Number($('vsOccupied').value),
              actualResidents: Number($('vsResidents').value || 0),
              matchResult: $('vsMatch').value,
              isSublease: Number($('vsSublease').value),
              isIdle: Number($('vsIdle').value),
              isIllegalUse: Number($('vsIllegal').value) };
  if ($('vsFindings').value.trim()) b.findings = $('vsFindings').value.trim();
  if ($('vsNext').value.trim()) b.nextAction = $('vsNext').value.trim();
  return req('POST', '/api/v1/visits/' + id + '/report', b);
}

function vsToWo() {
  const id = $('vsId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填走访 ID</span>'; return; }
  return req('POST', '/api/v1/visits/' + id + '/to-workorder',
             { operatorId: Number($('vsUid').value || 0), operatorName: $('vsUser').value.trim() });
}

function vsCancel() {
  const id = $('vsId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填走访 ID</span>'; return; }
  return req('POST', '/api/v1/visits/' + id + '/cancel', { reason: '住户已搬离' });
}

function listVisit() {
  let q = 'pageNum=1&pageSize=20';
  if ($('vsFType').value) q += '&visitType=' + $('vsFType').value;
  if ($('vsFSt').value) q += '&visitStatus=' + $('vsFSt').value;
  if ($('vsKw').value.trim()) q += '&keyword=' + encodeURIComponent($('vsKw').value.trim());
  return req('GET', '/api/v1/visits?' + q);
}

// ---------- 健康 ----------'''
s = s.replace(anchor_js, js, 1)

# 4) 接口清单
s = s.replace('<b>告警</b>　POST /api/v1/alerts',
              '<b>投诉</b>　POST /api/v1/complaints ｜ GET /api/v1/complaints ｜ POST .../handle ｜ .../resolve ｜ .../close ｜ .../evaluate ｜ .../to-workorder<br>\n'
              '        <b>走访</b>　POST /api/v1/visits ｜ GET /api/v1/visits ｜ POST .../report ｜ .../to-workorder ｜ .../cancel<br>\n'
              '        <b>告警</b>　POST /api/v1/alerts', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已加投诉与走访页，文件长度', len(s))
