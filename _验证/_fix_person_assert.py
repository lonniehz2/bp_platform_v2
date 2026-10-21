# -*- coding: utf-8 -*-
"""修正 assertTrue 第二参数类型（JUnit5 只接受 String）"""
import io

FIX = [
    (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\person\GuaranteeProfileTest.java',
     [('assertTrue(String.valueOf(m.get("advice")).contains("已过期"), m.get("advice"));',
       'assertTrue(String.valueOf(m.get("advice")).contains("已过期"),\n'
       '                    String.valueOf(m.get("advice")));'),
      ('assertTrue(String.valueOf(m.get("advice")).contains("复核"), m.get("advice"));',
       'assertTrue(String.valueOf(m.get("advice")).contains("复核"),\n'
       '                    String.valueOf(m.get("advice")));')]),
    (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\person\VerifyRecordTest.java',
     [('assertTrue(r.getRawResponse().length() < 5000, r.getRawResponse().length());',
       'assertTrue(r.getRawResponse().length() < 5000,\n'
       '                "实际长度 " + r.getRawResponse().length());'),
      ('assertTrue(String.valueOf(m.get("conclusion")).contains("疑似冒用"),\n'
       '                m.get("conclusion"));',
       'assertTrue(String.valueOf(m.get("conclusion")).contains("疑似冒用"),\n'
       '                String.valueOf(m.get("conclusion")));')]),
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
