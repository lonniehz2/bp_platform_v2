# -*- coding: utf-8 -*-
"""修正 ApplicationVerifyGateTest：按真实构造签名"""
import io

P = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'
     r'\ApplicationVerifyGateTest.java')
s = io.open(P, encoding='utf-8').read()

# 1) 辅助方法：按真实签名 (orgId, personId, securityType, securityMode, applyChannel,
#    familySize, ... intentAreaMin, intentAreaMax, ..., complianceCommitFlag,
#    dataShareAgreeFlag, ...)
old = '''    /** 构造合法申请（承诺书与授权都签了，只剩实名校验这一关）。 */
    private static ApplicationCreateCmd cmd(long personId) {
        return new ApplicationCreateCmd(personId, "PUBLIC", 1L, null, null, null, null,
                null, null, null, 1, 1, null, null, null, null);
    }'''
new = '''    /**
     * 构造合法申请（承诺书与授权都签了，只剩实名校验这一关）。
     *
     * <p>参数顺序与 {@code ApplicationCreateCmd} 一致：
     * orgId, personId, securityType, securityMode, applyChannel, familySize,
     * intentDistrict, intentProject, intentLayout, intentAreaMin, intentAreaMax,
     * declaredIncome, declaredIncomeYear, familyPropertyAmount,
     * complianceCommitFlag, dataShareAgreeFlag
     */
    private static ApplicationCreateCmd cmd(Long personId) {
        return new ApplicationCreateCmd(1L, personId, "PUBLIC", "HOUSE", "ONLINE", 3,
                null, null, null, null, null, null, null, null, 1, 1);
    }'''
assert old in s, 'cmd 锚点缺失'
s = s.replace(old, new, 1)

# 2) 承诺书未签的用例同样改签名
old2 = '''        ApplicationCreateCmd bad = new ApplicationCreateCmd(4001L, "PUBLIC", 1L, null,
                null, null, null, null, null, null, 0, 0, null, null, null, null);'''
new2 = '''        ApplicationCreateCmd bad = new ApplicationCreateCmd(1L, 4001L, "PUBLIC", "HOUSE",
                "ONLINE", 3, null, null, null, null, null, null, null, null, 0, 0);'''
assert old2 in s, 'bad 锚点缺失'
s = s.replace(old2, new2, 1)

# 3) cmd(null) 会因重载解析报错，显式转 Long
s = s.replace('service.create(cmd(null))', 'service.create(cmd((Long) null))')

io.open(P, 'w', encoding='utf-8').write(s)
print('已按真实构造签名修正 3 处')
