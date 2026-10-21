# -*- coding: utf-8 -*-
"""后端补 personName：申请列表显示申请人姓名而非 ID"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'


def find(name):
    for root, _, fs in os.walk(J):
        if name in fs:
            return os.path.join(root, name)
    return None


# ---------- 1) VO 增加 personName ----------
vo = find('ApplicationVO.java')
s = io.open(vo, encoding='utf-8').read()

if 'String personName' not in s:
    s = s.replace('        Long personId,', '        Long personId,\n        /** 申请人姓名（列表展示用，批量查询填充，避免前端显示 ID） */\n        String personName,', 1)

    # from(e) 委托到 from(e, null)
    s = s.replace('''    public static ApplicationVO from(BizApplication e) {''',
                  '''    public static ApplicationVO from(BizApplication e) {
        return from(e, null);
    }

    public static ApplicationVO from(BizApplication e, String personName) {''', 1)

    # 在构造里插入 personName：找到 "e.getPersonId()," 作为锚点
    m = re.search(r'(new ApplicationVO\(\s*\n\s*e\.getId\(\),\s*\n\s*e\.getApplicationNo\(\),\s*\n\s*e\.getOrgId\(\),\s*\n\s*e\.getPersonId\(\),)', s)
    if m:
        s = s[:m.end()] + '\n                personName,' + s[m.end():]
    else:
        # 退化：按 personId 参数位置插入
        s = re.sub(r'(new ApplicationVO\([\s\S]{0,400}?e\.getPersonId\(\),)',
                   r'\1\n                personName,', s, count=1)

    io.open(vo, 'w', encoding='utf-8').write(s)
    print('  ✓ ApplicationVO 增加 personName 字段与重载')
else:
    print('  - ApplicationVO 已有 personName')

# ---------- 2) service 批量填充姓名 ----------
svc = find('ApplicationServiceImpl.java')
t = io.open(svc, encoding='utf-8').read()

if 'personMapper' not in t:
    # 需要注入 PersonMapper
    t = t.replace('public class ApplicationServiceImpl',
                  'public class ApplicationServiceImpl', 1)
    # 构造函数注入：找已有的 private final ... Mapper
    mm = re.search(r'(    private final \w+Mapper \w+;)', t)
    if mm:
        t = t[:mm.end()] + '\n    private final PersonMapper personMapper;' + t[mm.end():]
    else:
        print('  !! 未找到 mapper 注入点，需手工处理')
    # 构造函数参数
    cm = re.search(r'(public ApplicationServiceImpl\(([^)]*)\))', t)
    if cm:
        t = t.replace(cm.group(1), cm.group(1).replace(')', ', PersonMapper personMapper)'), 1)
        t = t.replace('this.' + '', 'this.', 1)
        # 赋值
        t = re.sub(r'(public ApplicationServiceImpl\([^)]*\)\s*\{)',
                   r'\1\n        this.personMapper = personMapper;', t, count=1)
    # import
    if 'import com.yundao.bp.person.mapper.PersonMapper;' not in t:
        i = t.find('\nimport ')
        t = t[:i] + '\nimport com.yundao.bp.person.mapper.PersonMapper;' + t[i:]

io.open(svc, 'w', encoding='utf-8').write(t)
print('  ✓ ApplicationServiceImpl 注入 PersonMapper')

# 打印构造函数确认
t2 = io.open(svc, encoding='utf-8').read()
cm2 = re.search(r'public ApplicationServiceImpl\(([^)]*)\)\s*\{(.{0,300}?)\}', t2, re.S)
if cm2:
    print('\n  构造函数：\n' + cm2.group(0)[:420])
