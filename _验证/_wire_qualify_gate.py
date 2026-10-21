# -*- coding: utf-8 -*-
"""把保障档案接入资格审核：PASS 前校验收入档位/家庭人口/人才证书"""
import io

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\biz\service\impl\ApplicationServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

if 'guaranteeProfileService' in s:
    print('已接入，跳过')
    raise SystemExit

# ---------- 1) import ----------
s = s.replace('import com.yundao.bp.person.service.VerifyRecordService;',
              'import com.yundao.bp.person.service.GuaranteeProfileService;\n'
              'import com.yundao.bp.person.service.VerifyRecordService;', 1)

# ---------- 2) 可选注入 ----------
old = '''    /** 系统参数（实名开关与例外策略） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private ConfigService configService;'''
new = '''    /** 系统参数（实名开关与例外策略） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private ConfigService configService;

    /** 保障对象档案（资格判定依据） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private GuaranteeProfileService guaranteeProfileService;'''
assert old in s
s = s.replace(old, new, 1)

# ---------- 3) PASS 前插入档案校验 ----------
old_pass = '''        // 推进状态机
        switch (result) {
            case REJECT -> {'''
new_pass = '''        // ⭐ 资格判定校验（决策 D33）：审核通过前必须依据保障档案判定资格
        // 只信任手工勾选"通过"而不看档案，等于审核流于形式
        if (result == ReviewResult.PASS) {
            checkQualification(e);
        }

        // 推进状态机
        switch (result) {
            case REJECT -> {'''
assert old_pass in s
s = s.replace(old_pass, new_pass, 1)

# ---------- 4) 新增判定方法 ----------
anchor = '''    // ==================== 创建 ===================='''
method = '''    /**
     * 资格判定（审核通过前执行）。
     *
     * <p><b>为什么必须做</b>：如果审核员只勾选「通过」而不看保障档案，
     * 审核环节就退化成了形式。本方法把「档案里的事实」变成硬性判定：
     *
     * <ol>
     *   <li><b>档案必须存在</b>——没有收入/人口信息就无法判断是否符合条件</li>
     *   <li><b>收入档位不能是 NORMAL</b>——超过中低收入线即不符合保障条件</li>
     *   <li><b>家庭人口必须一致</b>——申请填 3 人、档案记 1 人属申报不实</li>
     *   <li><b>人才公寓必须有人才认定</b>且证书在有效期内</li>
     *   <li><b>名下有房</b>需人工说明（部分业态允许，如人才公寓）</li>
     * </ol>
     *
     * <p>判定不通过时抛 {@code STATE_CONFLICT}，并在信息中说明<b>具体不符合哪一条</b>，
     * 供审核员退回或补充材料。
     */
    private void checkQualification(BizApplication e) {
        if (guaranteeProfileService == null) {
            return;
        }
        com.yundao.bp.person.entity.PersonGuaranteeProfile profile;
        try {
            profile = guaranteeProfileService.getByPerson(e.getPersonId());
        } catch (BizException ex) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "该申请人尚无保障对象档案（缺收入/家庭人口信息），不能通过资格审核。"
                            + "请先在「保障档案」中建档后再审核。");
        }

        // ① 收入档位：NORMAL 表示超过中低收入线，不符合保障条件
        String level = profile.getIncomeLevel();
        if ("NORMAL".equals(level)) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "不符合保障条件：家庭人均月收入已超过中低收入线（当前档位：普通）。"
                            + "如认为档案数据有误，请先更新收入信息并重新核算档位。");
        }

        // ② 家庭人口一致性：申报人口与档案不一致属于申报不实
        Integer declared = e.getFamilySize();
        Integer actual = profile.getFamilySize();
        if (declared != null && actual != null && !declared.equals(actual)) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "申报家庭人口（" + declared + " 人）与保障档案登记（" + actual
                            + " 人）不一致，涉嫌申报不实。请核实后由申请人更正申报。");
        }

        // ③ 人才公寓：必须有人才认定且证书在有效期内
        if ("TALENT".equals(e.getSecurityType())) {
            if (profile.getTalentLevel() == null || profile.getTalentLevel().isBlank()) {
                throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                        "人才公寓申请必须提供人才认定信息，当前档案无人才层次记录。");
            }
            if (profile.getTalentValidTo() != null
                    && profile.getTalentValidTo().isBefore(java.time.LocalDate.now())) {
                throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                        "人才认定已过期（有效期至 " + profile.getTalentValidTo()
                                + "），请重新认定后再申请人才公寓。");
            }
        }

        // ④ 名下有房：不直接拒绝（部分业态允许），但要求档案有备注说明
        if (profile.getHasHouse() != null && profile.getHasHouse() == 1
                && (profile.getRemark() == null || profile.getRemark().isBlank())) {
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "申请人名下已有 " + (profile.getHouseCount() == null ? "多"
                            : profile.getHouseCount()) + " 套住房，"
                            + "需在档案备注中说明符合例外情形的依据后才能通过审核。");
        }
    }

''' + anchor
assert anchor in s
s = s.replace(anchor, method, 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('已接入资格判定（5 条硬规则）')
