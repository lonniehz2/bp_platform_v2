# -*- coding: utf-8 -*-
"""在申请分页里批量填充 personName"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
for root, _, fs in os.walk(J):
    if 'ApplicationServiceImpl.java' in fs:
        P = os.path.join(root, 'ApplicationServiceImpl.java')
        break

s = io.open(P, encoding='utf-8').read()

# 找到 page 里的 VO 转换行
m = re.search(r'IPage<BizApplication> page = appMapper\.selectPage\([^;]*;\s*\n'
              r'(\s*)List<ApplicationVO> (?:vos|list|rows)?\s*=\s*([^;]+);', s)
print('锚点：', 'OK' if m else '未找到')

if m and 'personNameMap' not in s:
    indent = m.group(1)
    old = m.group(0)
    new = old + (
        '\n' + indent + '// 批量填充申请人姓名（避免前端显示 personId 数字）\n'
        + indent + 'java.util.Map<Long, String> personNameMap = new java.util.HashMap<>();\n'
        + indent + 'java.util.List<Long> pids = new java.util.ArrayList<>();\n'
        + indent + 'for (ApplicationVO v : ' + m.group(2).strip() + ') {\n'
        + indent + '    if (v.personId() != null) {\n'
        + indent + '        pids.add(v.personId());\n'
        + indent + '    }\n'
        + indent + '}\n'
        + indent + 'if (!pids.isEmpty()) {\n'
        + indent + '    for (com.yundao.bp.person.entity.Person p :\n'
        + indent + '            personMapper.selectBatchIds(pids)) {\n'
        + indent + '        personNameMap.put(p.getId(), p.getPersonName());\n'
        + indent + '    }\n'
        + indent + '}\n'
        + indent + 'java.util.List<ApplicationVO> enriched = new java.util.ArrayList<>();\n'
        + indent + 'for (ApplicationVO v : ' + m.group(2).strip() + ') {\n'
        + indent + '    enriched.add(ApplicationVO.from(\n'
        + indent + '            appMapper.selectById(v.id()), personNameMap.get(v.personId())));\n'
        + indent + '}\n'
    )
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ 已插入批量姓名填充')
else:
    print('  - 已存在或锚点不匹配')
