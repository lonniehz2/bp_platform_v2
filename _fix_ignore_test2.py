# -*- coding: utf-8 -*-
"""修复被破坏的 IamModuleTest 断言行"""
import io

P = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\iam\IamModuleTest.java'
L = io.open(P, encoding='utf-8').read().split('\n')

OUT_SET = ('        assertEquals(Set.of("bp_iam_tenant", "bp_iam_permission", "bp_sys_dict",\n'
           '                "bp_sys_config", "bp_msg_template", "bp_rpt_report_def",\n'
           '                "bp_rpt_screen_def", "bp_open_api", "bp_open_call_log"),\n'
           '                MybatisTenantConfig.IGNORE_TABLES);')

# 定位被破坏的区域：含 'bp_open_call_log")rvice' 的行
bad_idx = [i for i, x in enumerate(L) if 'bp_open_call_log")' in x and 'require' not in x]
print('受影响行：%s' % [i + 1 for i in bad_idx])

if bad_idx:
    i = bad_idx[0]
    # 该行前半是被截断的 assertEquals，后半残片是 '...orgService.create(new OrgCreateCmd('
    tail = ''
    if 'rvice.create' in L[i]:
        tail = '        orgService.create(new OrgCreateCmd('
    # 向前找到 assertEquals 起始行
    start = i
    while start > 0 and 'assertEquals(Set.of(' not in L[start]:
        start -= 1
    L[start:i + 1] = [OUT_SET] + ([tail] if tail else [])
    io.open(P, 'w', encoding='utf-8').write('\n'.join(L))
    print('已重写第 %d~%d 行' % (start + 1, i + 1))

s = io.open(P, encoding='utf-8').read()
k = s.find('assertEquals(Set.of(')
print('\n结果：\n' + s[k - 120:k + 340])
