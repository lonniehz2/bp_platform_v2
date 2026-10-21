# -*- coding: utf-8 -*-
"""修正测试中字符串内未转义的英文双引号（改用中文引号）"""
import io

FIX = [
    (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\person\GuaranteeProfileTest.java',
     [('@DisplayName("⭐ 高收入者不能因人多而"被平均"进低保（人均口径防作弊）")',
       '@DisplayName("⭐ 高收入者不能因人多而被平均进低保（人均口径防作弊）")')]),
    (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\person\VerifyRecordTest.java',
     [('@DisplayName("⭐⭐ face=2 不同人 → 不通过，原因是"疑似冒用身份"")',
       '@DisplayName("⭐⭐ face=2 不同人 → 不通过，原因标注疑似冒用身份")'),
      ('@DisplayName("⭐⭐ face=3 不能确定 → 与"不同人"区分开（建议转人工）")',
       '@DisplayName("⭐⭐ face=3 不能确定 → 与不同人区分开（建议转人工）")'),
      ('@DisplayName("⭐ 认证结论：无记录时明确"不可进入资格审核"")',
       '@DisplayName("⭐ 认证结论：无记录时明确不可进入资格审核")')]),
]

for path, pairs in FIX:
    s = io.open(path, encoding='utf-8').read()
    n = 0
    for old, new in pairs:
        if old in s:
            s = s.replace(old, new, 1)
            n += 1
    io.open(path, 'w', encoding='utf-8').write(s)
    print('  %s：修正 %d 处' % (path.split('\\')[-1], n))
