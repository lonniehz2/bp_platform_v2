# -*- coding: utf-8 -*-
"""给验证台加「告警」+「驾驶舱」标签页"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'id="p-alert"' in s:
    print('告警页已存在，跳过')
    raise SystemExit

# 1) 标签
s = s.replace('    <button data-t="p-wo">工单</button>',
              '    <button data-t="p-dash">驾驶舱</button>\n'
              '    <button data-t="p-alert">告警</button>\n'
              '    <button data-t="p-wo">工单</button>', 1)

# 2) 面板
anchor = '  <!-- ==================== 工单 ==================== -->'
assert anchor in s

dash = '''  <!-- ==================== 驾驶舱 ==================== -->
  <div class="panel" id="p-dash">
    <div class="card">
      <h3>运维驾驶舱（实时统计）</h3>
      <div class="row">
        <div class="fld"><label>组织 ID</label><input id="dashOrg" placeholder="留空=全租户"></div>
        <button class="act" onclick="loadDash()">刷新</button>
      </div>
      <div id="dashBox" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-top:14px"></div>
      <div class="hint">
        数据来自 <code>/api/v1/alerts/stats</code> 与 <code>/api/v1/workorders</code>。
        正式大屏（Vue + ECharts + SSE 推送）尚未开发，这里是<b>数据可用性验证</b>。
      </div>
    </div>
    <div class="card">
      <h3>分布明细</h3>
      <div id="dashDetail" style="font-size:13px;line-height:2"></div>
    </div>
  </div>

  <!-- ==================== 告警 ==================== -->
  <div class="panel" id="p-alert">
    <div class="card">
      <h3>创建告警 <span class="m post">POST</span> /api/v1/alerts</h3>
      <div class="row">
        <div class="fld"><label>类别 *</label>
          <select id="alCat">
            <option value="VIOLATION">VIOLATION 违规（转租/闲置）</option>
            <option value="DEVICE">DEVICE 设备（离线/低电量/拆卸）</option>
            <option value="SAFETY">SAFETY 安全</option>
            <option value="BUSINESS">BUSINESS 业务（到期/欠费）</option>
          </select></div>
        <div class="fld"><label>类型 *</label>
          <select id="alType">
            <option value="SUBLEASE">SUBLEASE 转租转借</option>
            <option value="IDLE">IDLE 长期闲置</option>
            <option value="DEVICE_OFFLINE">DEVICE_OFFLINE 设备离线</option>
            <option value="LOW_BATTERY">LOW_BATTERY 低电量</option>
            <option value="TAMPER">TAMPER 暴力拆卸</option>
            <option value="UNTRUSTED_RATIO">UNTRUSTED_RATIO 不可信开门占比</option>
            <option value="NON_CONTRACT_OPEN">NON_CONTRACT_OPEN 非合同人开门</option>
            <option value="CONTRACT_EXPIRE">CONTRACT_EXPIRE 合同到期</option>
            <option value="ARREARS">ARREARS 欠费</option>
          </select></div>
        <div class="fld"><label>级别 *</label>
          <select id="alLevel">
            <option value="URGENT">URGENT 紧急（转工单15分钟响应）</option>
            <option value="IMPORTANT">IMPORTANT 重要</option>
            <option value="NORMAL">NORMAL 一般</option>
          </select></div>
        <div class="fld"><label>标题 *</label><input id="alTitle" value="疑似转租转借" style="min-width:200px"></div>
      </div>
      <div class="row">
        <div class="fld"><label>内容</label><input id="alContent" value="同一门锁30天内5个不同身份证开门" style="min-width:280px"></div>
        <div class="fld"><label>触发值</label><input id="alValue" value="25%"></div>
        <div class="fld"><label>阈值</label><input id="alThr" value="10%"></div>
        <div class="fld"><label>设备ID</label><input id="alDev" placeholder="可选"></div>
        <button class="act" onclick="createAlert()">创建</button>
        <button class="act gray" onclick="listAlert()">查询列表</button>
      </div>
      <div class="hint">级别为 URGENT 时后端会打 WARN 日志；转工单时响应时限收紧到 15 分钟。</div>
    </div>

    <div class="card">
      <h3>告警处置</h3>
      <div class="row">
        <div class="fld"><label>告警 ID *</label><input id="alId" placeholder="创建后自动填" style="min-width:190px"></div>
        <div class="fld"><label>处置人ID</label><input id="alUid" value="9002"></div>
        <div class="fld"><label>处置说明/结果</label><input id="alNote" value="已核实" style="min-width:200px"></div>
      </div>
      <div class="row">
        <button class="act" onclick="alAction('handle')">开始处置</button>
        <button class="act" onclick="alAction('resolve')">办结闭环</button>
        <button class="act" onclick="alAction('ignore')">误报忽略</button>
        <button class="act red" onclick="alAction('escalate')">升级</button>
        <button class="act" onclick="alToWo()">⭐ 转工单</button>
        <button class="act gray" onclick="getAlertStats()">刷新统计</button>
      </div>
      <div class="hint">
        状态机：<code>待处理 → 处理中 → 已闭环</code>；
        <code>待处理/处理中 → 误报忽略</code>；<code>→ 已升级 →（仍可继续处置）</code>。<br>
        已闭环/误报忽略是终态。<b>转工单</b>会创建 ALERT 类型工单并回写关联，同一告警只能转一次。
      </div>
    </div>

    <div class="card">
      <h3>告警列表 <span class="m get">GET</span> /api/v1/alerts</h3>
      <div class="row">
        <div class="fld"><label>类别</label>
          <select id="alFCat"><option value="">全部</option>
            <option value="VIOLATION">违规</option><option value="DEVICE">设备</option>
            <option value="SAFETY">安全</option><option value="BUSINESS">业务</option></select></div>
        <div class="fld"><label>级别</label>
          <select id="alFLv"><option value="">全部</option>
            <option value="URGENT">紧急</option><option value="IMPORTANT">重要</option>
            <option value="NORMAL">一般</option></select></div>
        <div class="fld"><label>状态</label>
          <select id="alFSt"><option value="">全部</option>
            <option value="PENDING">待处理</option><option value="HANDLING">处理中</option>
            <option value="HANDLED">已闭环</option><option value="IGNORED">误报忽略</option>
            <option value="ESCALATED">已升级</option></select></div>
        <div class="fld"><label>关键词</label><input id="alKw" placeholder="标题/告警号"></div>
        <button class="act" onclick="listAlert()">查询</button>
      </div>
    </div>
  </div>

'''
s = s.replace(anchor, dash + anchor, 1)

# 3) JS
anchor_js = '// ---------- 工单 ----------'
assert anchor_js in s
js = '''// ---------- 驾驶舱 ----------
function statCard(label, value, color) {
  return '<div style="background:#fff;border:1px solid #e3e6eb;border-radius:6px;padding:14px 16px">'
    + '<div style="font-size:12px;color:#8a94a0">' + label + '</div>'
    + '<div style="font-size:26px;font-weight:600;color:' + (color || '#1f2329') + ';margin-top:4px">'
    + value + '</div></div>';
}

async function loadDash() {
  const o = $('dashOrg').value.trim();
  const q = o ? ('?orgId=' + encodeURIComponent(o)) : '';
  try {
    const [ra, rw] = await Promise.all([
      fetch('/api/v1/alerts/stats' + q, { headers: hdr() }),
      fetch('/api/v1/workorders?pageNum=1&pageSize=1', { headers: hdr() })
    ]);
    const a = await ra.json();
    const w = await rw.json();
    if (a.code !== 'BP00000') { show('告警统计', ra.status, a); return; }
    const s = a.data || {};
    const woTotal = (w.data || {}).total || 0;
    $('dashBox').innerHTML =
        statCard('告警总数', s.total)
      + statCard('待处理', s.pending, '#c0392b')
      + statCard('处理中', s.handling, '#b7791f')
      + statCard('已闭环', s.handled, '#0f7b46')
      + statCard('误报忽略', s.ignored, '#8a94a0')
      + statCard('紧急未闭环', s.urgentOpen, '#c0392b')
      + statCard('工单总数', woTotal, '#1668dc');

    const lv = s.byLevel || {}, cat = s.byCategory || {};
    const catName = { SAFETY: '安全', DEVICE: '设备', BUSINESS: '业务', VIOLATION: '违规' };
    const lvName = { URGENT: '紧急', IMPORTANT: '重要', NORMAL: '一般' };
    let html = '<b>按级别</b>：';
    Object.keys(lv).forEach(k => { html += (lvName[k] || k) + ' <b>' + lv[k] + '</b>　'; });
    html += '<br><b>按类别</b>：';
    Object.keys(cat).forEach(k => { html += (catName[k] || k) + ' <b>' + cat[k] + '</b>　'; });
    $('dashDetail').innerHTML = html;
    show('GET /api/v1/alerts/stats' + q, ra.status, a);
  } catch (e) {
    show('驾驶舱', 0, { error: String(e) });
  }
}

// ---------- 告警 ----------
function createAlert() {
  const b = { alertCategory: $('alCat').value, alertType: $('alType').value,
              alertLevel: $('alLevel').value, alertTitle: $('alTitle').value.trim() };
  if ($('alContent').value.trim()) b.alertContent = $('alContent').value.trim();
  if ($('alValue').value.trim()) b.alertValue = $('alValue').value.trim();
  if ($('alThr').value.trim()) b.thresholdValue = $('alThr').value.trim();
  if ($('alDev').value.trim()) b.deviceId = $('alDev').value.trim();
  return req('POST', '/api/v1/alerts', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) $('alId').value = id;
  });
}

function alAction(act) {
  const id = $('alId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填告警 ID（或先创建告警）</span>'; return; }
  const uid = Number($('alUid').value || 0);
  let b;
  if (act === 'handle') b = { handleUserId: uid, action: $('alNote').value.trim() };
  else b = { handleUserId: uid, result: $('alNote').value.trim() };
  return req('POST', '/api/v1/alerts/' + id + '/' + act, b);
}

function alToWo() {
  const id = $('alId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填告警 ID</span>'; return; }
  return req('POST', '/api/v1/alerts/' + id + '/to-workorder',
             { handleUserId: Number($('alUid').value || 0), action: '管理员' });
}

function getAlertStats() {
  const o = $('dashOrg').value.trim();
  return req('GET', '/api/v1/alerts/stats' + (o ? ('?orgId=' + encodeURIComponent(o)) : ''));
}

function listAlert() {
  let q = 'pageNum=1&pageSize=20';
  if ($('alFCat').value) q += '&category=' + $('alFCat').value;
  if ($('alFLv').value) q += '&level=' + $('alFLv').value;
  if ($('alFSt').value) q += '&status=' + $('alFSt').value;
  if ($('alKw').value.trim()) q += '&keyword=' + encodeURIComponent($('alKw').value.trim());
  return req('GET', '/api/v1/alerts?' + q);
}

// ---------- 工单 ----------'''
s = s.replace(anchor_js, js, 1)

# 4) 接口清单
s = s.replace('<b>工单</b>　POST /api/v1/workorders',
              '<b>告警</b>　POST /api/v1/alerts ｜ GET /api/v1/alerts ｜ GET /api/v1/alerts/stats ｜ '
              'POST .../handle ｜ .../resolve ｜ .../ignore ｜ .../escalate ｜ .../to-workorder<br>\n'
              '        <b>工单</b>　POST /api/v1/workorders', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已加驾驶舱与告警页，文件长度', len(s))
