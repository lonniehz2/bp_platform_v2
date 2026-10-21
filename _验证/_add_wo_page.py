# -*- coding: utf-8 -*-
"""给验证台页面加「工单」标签页"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'id="p-wo"' in s or 'onclick="createWO()"' in s:
    print('工单页已存在，跳过')
    raise SystemExit

# 1) 标签按钮
anchor_tab = '    <button data-t="p-health">健康检查</button>'
assert anchor_tab in s
s = s.replace(anchor_tab,
              '    <button data-t="p-wo">工单</button>\n' + anchor_tab, 1)

# 2) 面板（插在健康检查面板之前）
anchor_panel = '  <!-- ==================== 健康 ==================== -->'
assert anchor_panel in s
wo_panel = '''  <!-- ==================== 工单 ==================== -->
  <div class="panel" id="p-wo">
    <div class="card">
      <h3>创建工单 <span class="m post">POST</span> /api/v1/workorders</h3>
      <div class="row">
        <div class="fld"><label>工单类型 *</label>
          <select id="woType">
            <option value="REPAIR">REPAIR 报修（响应30/完工240分钟）</option>
            <option value="ALERT">ALERT 告警处置（15/120，最紧急）</option>
            <option value="COMPLAINT">COMPLAINT 投诉（60/480）</option>
            <option value="INSPECT">INSPECT 巡检（120/1440）</option>
            <option value="INSTALL">INSTALL 安装（240/2880）</option>
            <option value="MAINTAIN">MAINTAIN 维护（240/2880）</option>
            <option value="CONSULT">CONSULT 咨询（60/480）</option>
            <option value="VISIT">VISIT 走访（120/1440）</option>
          </select></div>
        <div class="fld"><label>来源</label>
          <select id="woSrc">
            <option value="TENANT_APP">租户端</option><option value="STAFF" selected>员工</option>
            <option value="PHONE">电话</option><option value="ALERT">告警转</option>
            <option value="MINIAPP">小程序</option><option value="WALKIN">现场</option>
          </select></div>
        <div class="fld"><label>标题 *</label>
          <input id="woTitle" value="101室门锁无法开门" style="min-width:220px"></div>
        <div class="fld"><label>关联设备ID</label><input id="woDev" placeholder="可选"></div>
      </div>
      <div class="row">
        <div class="fld"><label>问题描述</label>
          <input id="woContent" value="刷卡无反应，已持续2小时" style="min-width:280px"></div>
        <div class="fld"><label>报修人</label><input id="woRep" value="张三"></div>
        <div class="fld"><label>电话</label><input id="woPhone" value="13800138000"></div>
        <div class="fld"><label>地址</label><input id="woAddr" value="1幢1单元1层101室"></div>
        <button class="act" onclick="createWO()">创建</button>
        <button class="act gray" onclick="listWO()">查询列表</button>
      </div>
      <div class="hint">
        SLA 默认值按工单类型自动取（响应/完工分钟数）。创建后自动回填工单 ID 到下方流转区。
      </div>
    </div>

    <div class="card">
      <h3>工单流转（每步都留痕）</h3>
      <div class="row">
        <div class="fld"><label>工单 ID *</label><input id="woId" placeholder="创建后自动填" style="min-width:190px"></div>
        <div class="fld"><label>处理人ID</label><input id="woUid" value="9001"></div>
        <div class="fld"><label>处理人姓名</label><input id="woUname" value="李师傅"></div>
        <div class="fld"><label>电话</label><input id="woUphone" value="13900139000"></div>
        <div class="fld"><label>处理说明</label><input id="woNote" value="已处理"></div>
        <div class="fld"><label>处理结果</label><input id="woResult" value="更换电池，恢复正常"></div>
      </div>
      <div class="row">
        <button class="act" onclick="woAction('assign')">派单</button>
        <button class="act" onclick="woAction('accept')">接单</button>
        <button class="act" onclick="woAction('start')">开始处理</button>
        <button class="act" onclick="woAction('finish')">完工</button>
        <button class="act" onclick="woAction('close')">闭环</button>
        <button class="act red" onclick="woAction('cancel')">取消</button>
        <button class="act red" onclick="woAction('reject')">驳回</button>
        <button class="act gray" onclick="woLogs()">查看流转记录</button>
      </div>
      <div class="hint">
        <b>状态机（不可跳步）</b>：
        <code>待派单 → 已派单 → 已接单 → 处理中 → 已完工 → 已闭环</code><br>
        跳步会返回 <code>BP40001</code>。例如"待派单"直接点"闭环"会被拒。
        已闭环/已取消/已驳回是终态，不能再流转。
      </div>
    </div>

    <div class="card">
      <h3>工单列表 <span class="m get">GET</span> /api/v1/workorders</h3>
      <div class="row">
        <div class="fld"><label>类型</label>
          <select id="woFilterType"><option value="">全部</option>
            <option value="REPAIR">报修</option><option value="ALERT">告警处置</option>
            <option value="COMPLAINT">投诉</option><option value="INSPECT">巡检</option></select></div>
        <div class="fld"><label>状态</label>
          <select id="woFilterStatus"><option value="">全部</option>
            <option value="PENDING">待派单</option><option value="ASSIGNED">已派单</option>
            <option value="ACCEPTED">已接单</option><option value="PROCESSING">处理中</option>
            <option value="FINISHED">已完工</option><option value="CLOSED">已闭环</option>
            <option value="CANCELLED">已取消</option><option value="REJECTED">已驳回</option></select></div>
        <div class="fld"><label>关键词</label><input id="woKw" placeholder="标题/工单号"></div>
        <button class="act" onclick="listWO()">查询</button>
      </div>
    </div>
  </div>

'''
s = s.replace(anchor_panel, wo_panel + anchor_panel, 1)

# 3) JS
anchor_js = '''// ---------- 健康 ----------'''
assert anchor_js in s
wo_js = '''// ---------- 工单 ----------
function createWO() {
  const b = { orderType: $('woType').value, orderSource: $('woSrc').value,
              orderTitle: $('woTitle').value.trim() };
  if ($('woContent').value.trim()) b.orderContent = $('woContent').value.trim();
  if ($('woDev').value.trim()) b.deviceId = $('woDev').value.trim();
  if ($('woRep').value.trim()) b.reporterName = $('woRep').value.trim();
  if ($('woPhone').value.trim()) b.reporterPhone = $('woPhone').value.trim();
  if ($('woAddr').value.trim()) b.orderAddress = $('woAddr').value.trim();
  return req('POST', '/api/v1/workorders', b).then(j => {
    const id = j && j.data && j.data.id;
    if (id) { $('woId').value = id; }
  });
}

function woAction(act) {
  const id = $('woId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填工单 ID（或先创建工单）</span>'; return; }
  const uid = Number($('woUid').value || 0);
  const uname = $('woUname').value.trim();
  let b;
  if (act === 'assign') {
    b = { assignUserId: uid, assignUserName: uname,
          assignUserPhone: $('woUphone').value.trim(), content: $('woNote').value.trim() };
  } else if (act === 'finish') {
    b = { operatorId: uid, operatorName: uname,
          handleResult: $('woResult').value.trim(), content: $('woNote').value.trim() };
  } else {
    b = { operatorId: uid, operatorName: uname, content: $('woNote').value.trim() };
  }
  return req('POST', '/api/v1/workorders/' + id + '/' + act, b);
}

function woLogs() {
  const id = $('woId').value.trim();
  if (!id) { out.innerHTML = '<span class="err">请先填工单 ID</span>'; return; }
  return req('GET', '/api/v1/workorders/' + id + '/logs');
}

function listWO() {
  let q = 'pageNum=1&pageSize=20';
  if ($('woFilterType').value) q += '&orderType=' + $('woFilterType').value;
  if ($('woFilterStatus').value) q += '&orderStatus=' + $('woFilterStatus').value;
  if ($('woKw').value.trim()) q += '&keyword=' + encodeURIComponent($('woKw').value.trim());
  return req('GET', '/api/v1/workorders?' + q);
}

// ---------- 健康 ----------'''
s = s.replace(anchor_js, wo_js, 1)

# 4) 接口清单补充
s = s.replace('<b>人员</b>　POST /api/v1/persons',
              '<b>工单</b>　POST /api/v1/workorders ｜ GET /api/v1/workorders ｜ GET /api/v1/workorders/{id} ｜ '
              'GET /api/v1/workorders/{id}/logs ｜ POST .../assign ｜ .../accept ｜ .../start ｜ .../finish ｜ .../close ｜ .../cancel ｜ .../reject<br>\n'
              '        <b>授权</b>　POST /api/v1/grants ｜ GET /api/v1/grants ｜ GET /api/v1/grants/tasks/{id} ｜ '
              'GET /api/v1/grants/tasks/{id}/details ｜ POST /api/v1/grants/{id}/revoke<br>\n'
              '        <b>人员</b>　POST /api/v1/persons', 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('已添加工单页，文件长度', len(s))
