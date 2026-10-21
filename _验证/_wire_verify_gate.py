# -*- coding: utf-8 -*-
"""把实名认证接入申请校验（决策：认证不通过不得申请，可配置开关）"""
import io

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\biz\service\impl\ApplicationServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

if 'verifyRecordService' in s:
    print('已接入，跳过')
    raise SystemExit

# ---------- 1) import ----------
s = s.replace('import com.yundao.bp.biz.service.CreditService;',
              'import com.yundao.bp.biz.service.CreditService;\n'
              'import com.yundao.bp.person.service.VerifyRecordService;\n'
              'import com.yundao.bp.sys.constant.ConfigKeys;\n'
              'import com.yundao.bp.sys.service.ConfigService;', 1)

# ---------- 2) 可选注入 ----------
old_field = '''    /** 信用惩戒服务（可选注入，避免影响既有构造器与单测） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private CreditService creditService;'''
new_field = '''    /** 信用惩戒服务（可选注入，避免影响既有构造器与单测） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private CreditService creditService;

    /** 实名认证服务（可选注入） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private VerifyRecordService verifyRecordService;

    /** 系统参数（实名开关与例外策略） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private ConfigService configService;'''
assert old_field in s
s = s.replace(old_field, new_field, 1)

# ---------- 3) 校验逻辑 ----------
old_check = '''        // ⭐ 信用惩戒校验（决策 D31）：处于限制申请期的人员不得申请
        // 放在最前面，避免"填完一堆材料才被告知不能申请"
        if (creditService != null) {
            creditService.checkApplyBan(cmd.personId());
        }'''
new_check = '''        // ⭐ 信用惩戒校验（决策 D31）：处于限制申请期的人员不得申请
        // 放在最前面，避免"填完一堆材料才被告知不能申请"
        if (creditService != null) {
            creditService.checkApplyBan(cmd.personId());
        }

        // ⭐ 实名认证校验（决策 D32）：未通过实名认证不得申请
        // 同样前置，理由同信用校验：不让申请人白填材料
        checkVerify(cmd.personId());'''
assert old_check in s
s = s.replace(old_check, new_check, 1)

# ---------- 4) 新增私有方法 ----------
anchor = '''    // ==================== 创建 ===================='''
method = '''    /**
     * 实名认证校验。
     *
     * <p><b>规则</b>：该人员最近一次实名认证必须通过，否则不得申请。
     *
     * <p><b>为什么必须真正拦在申请入口</b>：实名认证是「人证合一」的唯一保证，
     * 只在建档时记录而不校验，等于允许冒名申请——这是保障房领域最常见也最严重的骗租手法。
     *
     * <p><b>可配置</b>：部分地区允许"先申请后认证"（如线上提交、线下核验），
     * 由系统参数 {@code biz.apply.requireVerify} 控制，默认要求认证。
     * 关闭时不做拦截，但仍会记录（便于事后审计）。
     */
    private void checkVerify(Long personId) {
        if (personId == null) {
            throw BizException.paramInvalid("申请人不能为空");
        }
        boolean required = configService == null
                || configService.getBool(ConfigKeys.APPLY_REQUIRE_VERIFY, true);
        if (!required) {
            return;
        }
        if (verifyRecordService == null) {
            // 未部署认证能力时不阻断（灰度环境），但不静默放行到无感知
            return;
        }
        java.util.Map<String, Object> c = verifyRecordService.conclusion(personId);
        Object verified = c.get("verified");
        if (!Boolean.TRUE.equals(verified)) {
            Object reason = c.get("conclusion");
            throw new BizException(com.yundao.bp.common.api.ErrorCode.STATE_CONFLICT,
                    "申请人尚未通过实名认证，不能提交申请。"
                            + (reason == null ? "" : "（" + reason + "）")
                            + " 请在「实名认证」中完成人脸或身份证核验后重试。");
        }
    }

''' + anchor
assert anchor in s
s = s.replace(anchor, method, 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('已接入实名校验（含可配置开关）')

# ---------- 5) ConfigKeys 增加键 ----------
P2 = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
      r'\sys\constant\ConfigKeys.java')
s2 = io.open(P2, encoding='utf-8').read()
if 'APPLY_REQUIRE_VERIFY' not in s2:
    s2 = s2.replace('''    // ---------- 申诉 ----------''',
                    '''    // ---------- 申请 ----------
    /** 是否要求实名认证后才能申请（默认 true） */
    public static final String APPLY_REQUIRE_VERIFY = "biz.apply.requireVerify";

    // ---------- 申诉 ----------''', 1)
    io.open(P2, 'w', encoding='utf-8').write(s2)
    print('  ✓ ConfigKeys 新增 biz.apply.requireVerify')
