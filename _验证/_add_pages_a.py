# -*- coding: utf-8 -*-
"""补齐 7 个页面：公示/年审/复议/信用 独立页签 + 同住人/变更/换房 并入合同页"""
import io

p = r'D:\Work\业务平台开发\backend\src\main\resources\static\index.html'
s = io.open(p, encoding='utf-8').read()

if 'id="p-pub"' in s:
    print('已存在，跳过')
    raise SystemExit

# ---------- 1) 页签按钮（放在「退租」之后）----------
s = s.replace('    <button data-t="p-term">退租</button>',
              '    <button data-t="p-term">退租</button>\n'
              '    <button data-t="p-pub">公示</button>\n'
              '    <button data-t="p-review">年审</button>\n'
              '    <button data-t="p-appeal">复议</button>\n'
              '    <button data-t="p-credit">信用</button>', 1)

# ---------- 2) 合同页追加三张卡片 ----------
contract_anchor = '  <!-- ==================== 退租 ==================== -->'
assert contract_anchor in s

contract_cards = '''    <div class="card">
      <h3>同住人（保障人口）</h3>
      <div class="row">
        <div class="fld"><label>合同ID *</label><input id="chContract" value="2001"></div>
        <div class="fld"><label>姓名 *</label><input id="chName" value="张美丽"></div>
        <div class="fld"><label>关系</label>
          <select id="chRel"><option value="SPOUSE">配偶</option><option value="CHILD">子女</option>
            <option value="PARENT">父母</option><option value="SIBLING">兄弟姐妹</option>
            <option value="OTHER">其他</option></select></div>
        <div class="fld"><label>身份证(脱敏)</label><input id="chMask" placeholder="110101********1234"></div>
        <button class="act" onclick="addCohabitant()">添加</button>
        <button class="act gray" onclick="listCohabitant()">列表</button>
        <button class="act gray" onclick="householdSize()">⭐ 保障人口</button>
      </div>
      <div class="row">
        <div class="fld"><label>同住人ID</label><input id="chId" placeholder="列表后填"></div>
        <button class="act" onclick="grantCohabitant(true)">授权开门</button>
        <button class="act" onclick="grantCohabitant(false)">撤销授权</button>
        <button class="act red" onclick="removeCohabitant()">移除</button>
      </div>
      <div class="hint">
        ⭐ <b>保障人口 = 承租人 1 + 同住人数</b>，按人补贴、年审人均收入核查、退租腾退都用它。<br>
        身份证只存<b>脱敏串</b>，不存明文。
      </div>
    </div>

    <div class="card">
      <h3>合同变更（租金/租期/承租人）</h3>
      <div class="row">
        <div class="fld"><label>合同ID *</label><input id="cgContract" value="2001"></div>
        <div class="fld"><label>变更类型 *</label>
          <select id="cgType"><option value="RENT_ADJUST">租金调整</option>
            <option value="PERIOD">租期变更</option><option value="LESSEE">承租人变更</option>
            <option value="OTHER">其他</option></select></div>
        <div class="fld"><label>新月租金</label><input id="cgRent" placeholder="1300"></div>
        <div class="fld"><label>新止租日</label><input id="cgEnd" placeholder="2028-12-31"></div>
        <div class="fld"><label>变更原因</label><input id="cgReason" value="年审调租" style="min-width:150px"></div>
        <button class="act" onclick="createChange()">发起变更</button>
      </div>
      <div class="row">
        <div class="fld"><label>变更单ID *</label><input id="cgId" placeholder="发起后自动填" style="min-width:190px"></div>
        <button class="act" onclick="cgAction('approve')">⭐ 批准（写回合同）</button>
        <button class="act red" onclick="cgAction('reject')">驳回</button>
        <button class="act gray" onclick="listChange()">变更历史</button>
      </div>
      <div class="hint">
        ⭐ <b>批准才写回合同</b>：租金/止租日/承租人真正变更。变更前后存 JSON 快照可审计。<br>
        同合同<b>只允许一个待审批变更</b>，防止两笔调租互相覆盖。
      </div>
    </div>

    <div class="card">
      <h3>换房（成都限1次 / 重庆应换不换1.5倍）</h3>
      <div class="row">
        <div class="fld"><label>人员ID *</label><input id="exPerson" value="4001"></div>
        <div class="fld"><label>原合同ID *</label><input id="exOldContract" value="2001"></div>
        <div class="fld"><label>原房源ID *</label><input id="exOldHouse" value="5001"></div>
        <div class="fld"><label>新房源ID *</label><input id="exNewHouse" value="5002"></div>
        <div class="fld"><label>换房类型</label>
          <select id="exType"><option value="VOLUNTARY">自愿换房</option>
            <option value="ADJUST">调整换房</option><option value="EXPEL_RELOCATE">清退安置</option></select></div>
        <div class="fld"><label>应换房</label>
          <select id="exForced"><option value="0">否</option><option value="1">是（应换不换×1.5）</option></select></div>
        <button class="act" onclick="applyExchange()">申请换房</button>
      </div>
      <div class="row">
        <div class="fld"><label>换房单ID *</label><input id="exId" placeholder="申请后自动填" style="min-width:190px"></div>
        <button class="act" onclick="exAction('submit')">提交审批</button>
        <button class="act" onclick="exAction('approve')">批准</button>
        <button class="act" onclick="exComplete()">⭐ 执行换房</button>
        <button class="act red" onclick="exAction('reject')">驳回</button>
        <button class="act gray" onclick="exNoExchange()">应换不换</button>
      </div>
      <div class="hint">
        ⭐ <b>执行换房会真正落地</b>：生成新合同（延续止租日/租金）+ 原合同终止 + 旧房源回池 + 新房源占用。<br>
        <b>成都</b>同租期限换 <b>1 次</b>；<b>重庆</b>应换不换按 <b>1.5 倍</b>计租。
      </div>
    </div>

''' + contract_anchor
s = s.replace(contract_anchor, contract_cards, 1)

# ---------- 3) 四个新面板 ----------
tabs_anchor = '  <!-- ==================== 驾驶舱 ==================== -->'
assert tabs_anchor in s

panels = '''  <!-- ==================== 公示 ==================== -->
  <div class="panel" id="p-pub">
    <div class="card">
      <h3>发布公示 <span class="m post">POST</span> /api/v1/publicities</h3>
      <div class="row">
        <div class="fld"><label>公示类型 *</label>
          <select id="pbType"><option value="ALLOCATION">ALLOCATION 配租公示</option>
            <option value="QUALIFY">QUALIFY 资格公示</option>
            <option value="EXIT">EXIT 退出公示</option></select></div>
        <div class="fld"><label>组织ID</label><input id="pbOrg" value="7001"></div>
        <div class="fld"><label>标题 *</label><input id="pbTitle" value="2026年第一批公租房配租结果公示" style="min-width:230px"></div>
        <div class="fld"><label>开始日 *</label><input id="pbStart" placeholder="2026-10-19"></div>
        <div class="fld"><label>结束日 *</label><input id="pbEnd" placeholder="2026-10-25"></div>
        <button class="act" onclick="createPublicity()">创建公示</button>
      </div>
      <div class="row">
        <div class="fld"><label>内容</label><input id="pbContent" value="经公开摇号，中签结果如下……" style="min-width:260px"></div>
        <div class="fld"><label>公示ID *</label><input id="pbId" placeholder="创建后自动填" style="min-width:190px"></div>
        <button class="act" onclick="pbAction('publish')">发布</button>
        <button class="act" onclick="pbAction('close')">⭐ 结束公示</button>
        <button class="act gray" onclick="listPublicity()">公示列表</button>
        <button class="act gray" onclick="checkAllocPub()">配租公示检查</button>
      </div>
      <div class="hint">
        ⭐⭐ <b>配租公示不得少于 7 个自然日</b>（含首尾），不足直接拒绝。<br>
        ⭐ <b>公示未结束，签约会被强制拦截</b>——合规硬约束。
      </div>
    </div>
  </div>

  <!-- ==================== 年审 ==================== -->
  <div class="panel" id="p-review">
    <div class="card">
      <h3>年审复核（保留 / 调租 / 退出）</h3>
      <div class="row">
        <div class="fld"><label>人员ID *</label><input id="rvPerson" value="4001"></div>
        <div class="fld"><label>合同ID</label><input id="rvContract" value="2001"></div>
        <div class="fld"><label>房源ID</label><input id="rvHouse" value="5001"></div>
        <div class="fld"><label>复核年度 *</label><input id="rvYear" value="2026"></div>
        <div class="fld"><label>复核类型</label>
          <select id="rvType"><option value="ANNUAL">ANNUAL 年度复核</option>
            <option value="DYNAMIC">DYNAMIC 动态核查</option>
            <option value="SPECIAL">SPECIAL 专项核查</option></select></div>
        <button class="act" onclick="createReview()">创建复核单</button>
      </div>
      <div class="row">
        <div class="fld"><label>复核单ID *</label><input id="rvId" placeholder="创建后自动填" style="min-width:190px"></div>
        <button class="act" onclick="reviewAction('start')">开始复核</button>
        <div class="fld"><label>复核结果</label>
          <select id="rvResult"><option value="KEEP">KEEP 保留资格</option>
            <option value="ADJUST">ADJUST 调整（需填处置）</option>
            <option value="EXIT">EXIT 退出（需填处置）</option></select></div>
        <div class="fld"><label>处置内容</label><input id="rvAdjust" value="收入超标，租金上浮至 1500" style="min-width:220px"></div>
        <button class="act" onclick="finishReview()">⭐ 完成复核</button>
        <button class="act gray" onclick="reviewBatch()">批量生成(试运行)</button>
      </div>
      <div class="hint">
        ⭐⭐ <b>复核结果会真正产生后果</b>：<br>
        <code>KEEP</code> 不动 ｜ <code>ADJUST</code> 可发起调租变更写回合同 ｜ <code>EXIT</code> <b>自动生成退租腾退单</b>（3个月过渡期、1.5倍租金，不触发5年禁申）。<br>
        结果 ADJUST/EXIT <b>必须填处置内容</b>。
      </div>
    </div>
  </div>

  <!-- ==================== 复议 ==================== -->
  <div class="panel" id="p-appeal">
    <div class="card">
      <h3>申诉 / 异议（法定救济通道）</h3>
      <div class="row">
        <div class="fld"><label>业务类型 *</label>
          <select id="apBizType"><option value="ANNUAL_REVIEW">ANNUAL_REVIEW 年度核查</option>
            <option value="REVIEW">REVIEW 审核</option>
            <option value="APPLICATION">APPLICATION 申请</option>
            <option value="PUBLICITY">PUBLICITY 公示</option>
            <option value="EXIT">EXIT 退出</option></select></div>
        <div class="fld"><label>业务ID *</label><input id="apBizId" placeholder="如年审单ID"></div>
        <div class="fld"><label>人员ID *</label><input id="apPerson" value="4001"></div>
        <div class="fld"><label>类型</label>
          <select id="apType"><option value="SUBMIT">SUBMIT 申诉</option>
            <option value="OBJECTION">OBJECTION 公示异议</option></select></div>
        <div class="fld"><label>期限天数</label><input id="apDays" value="10"></div>
        <button class="act" onclick="submitAppeal()">提出申诉</button>
      </div>
      <div class="row">
        <div class="fld"><label>理由 *</label><input id="apReason" value="配偶失业未计入，家庭收入未超标" style="min-width:280px"></div>
      </div>
      <div class="row">
        <div class="fld"><label>申诉单ID *</label><input id="apId" placeholder="提出后自动填" style="min-width:190px"></div>
        <button class="act" onclick="apAction('accept')">受理</button>
        <button class="act" onclick="apAction('investigate')">调查</button>
        <button class="act red" onclick="apAction('withdraw')">撤回</button>
        <button class="act gray" onclick="listAppeal()">申诉列表</button>
      </div>
      <div class="row">
        <div class="fld"><label>决定结论</label>
          <select id="apDecision"><option value="UPHELD">UPHELD 异议成立</option>
            <option value="REJECTED">REJECTED 异议不成立</option></select></div>
        <div class="fld"><label>结果影响</label>
          <select id="apEffect"><option value="RESTORE">RESTORE 恢复资格</option>
            <option value="NONE">NONE 无影响</option><option value="ADJUST">ADJUST 调整标准</option>
            <option value="CANCEL">CANCEL 取消资格</option></select></div>
        <div class="fld"><label>复核意见</label><input id="apOpinion" value="异议成立，恢复原租金标准" style="min-width:200px"></div>
        <button class="act" onclick="decideAppeal()">⭐ 作出决定</button>
        <button class="act gray" onclick="apNotify()">告知结果</button>
      </div>
      <div class="hint">
        ⭐⭐ <b>异议成立会真正回写原业务</b>：<br>
        · <code>ANNUAL_REVIEW + RESTORE</code> → 反向调租把租金改回去 + 年审结论恢复「保留资格」<br>
        · <code>EXIT + RESTORE</code> → <b>撤销已生成的退租腾退单</b><br>
        ⚠️ 异议不成立时结果影响必须为 NONE（否则逻辑矛盾被拒）。
      </div>
    </div>
  </div>

  <!-- ==================== 信用 ==================== -->
  <div class="panel" id="p-credit">
    <div class="card">
      <h3>信用惩戒（失信限制再申请）</h3>
      <div class="row">
        <div class="fld"><label>人员ID *</label><input id="ctPerson" value="4001"></div>
        <div class="fld"><label>违规类型 *</label>
          <select id="ctViolation"><option value="SUBLEASE">SUBLEASE 转租出借(5年)</option>
            <option value="FALSE_INFO">FALSE_INFO 虚假信息(5年)</option>
            <option value="ILLEGAL">ILLEGAL 违法活动(5年)</option>
            <option value="STRUCTURE">STRUCTURE 破坏结构(5年)</option>
            <option value="ARREARS">ARREARS 恶意欠租</option>
            <option value="VACANT">VACANT 长期空置</option>
            <option value="CHANGE_USE">CHANGE_USE 改变用途</option>
            <option value="OTHER">OTHER 其他</option></select></div>
        <div class="fld"><label>惩戒措施 *</label>
          <select id="ctSanction"><option value="BAN_APPLY">BAN_APPLY 限制申请</option>
            <option value="TERMINATE">TERMINATE 终止资格</option>
            <option value="CREDIT_PLATFORM">CREDIT_PLATFORM 推送信用平台</option>
            <option value="FINE">FINE 罚款</option>
            <option value="OTHER">OTHER 其他</option></select></div>
        <div class="fld"><label>限制年限</label><input id="ctYears" placeholder="留空按默认"></div>
        <div class="fld"><label>法律文书号</label><input id="ctDoc" placeholder="漳住保决字〔2026〕第008号" style="min-width:200px"></div>
        <button class="act" onclick="recordCredit()">记入失信</button>
      </div>
      <div class="row">
        <div class="fld"><label>违规描述</label><input id="ctDesc" value="将保障房转租他人牟利" style="min-width:240px"></div>
        <div class="fld"><label>推送平台</label><input id="ctPlatform" value="四川住房保障管理服务平台" style="min-width:200px"></div>
      </div>
      <div class="row">
        <div class="fld"><label>信用记录ID *</label><input id="ctId" placeholder="记入后自动填" style="min-width:190px"></div>
        <button class="act" onclick="ctAction('revoke')">撤销（纠错）</button>
        <button class="act" onclick="ctAction('expire')">解除（期满）</button>
        <button class="act" onclick="ctPush()">标记已推送</button>
        <button class="act gray" onclick="listCredit()">信用记录</button>
      </div>
      <div class="row">
        <div class="fld"><label>校验人员ID</label><input id="ctCheck" value="4001"></div>
        <button class="act" onclick="checkBan()">⭐⭐ 校验是否禁申</button>
        <button class="act gray" onclick="scanCreditExpired()">期满扫描</button>
      </div>
      <div class="hint">
        ⭐⭐ <b>失信会真正阻止申请</b>：申请接口第一行就校验 <code>checkApplyBan</code>，
        处于限制期直接拒绝，且拒绝信息含违规类型+解禁日期+记录号。<br>
        严重违规（转租/虚假信息/违法/破坏结构）默认 <b>5 年</b>；多条记录取<b>最晚解禁</b>的。
      </div>
    </div>
  </div>

''' + tabs_anchor
s = s.replace(tabs_anchor, panels, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print('面板已加，当前长度', len(s))
