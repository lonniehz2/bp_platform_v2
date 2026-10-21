# -*- coding: utf-8 -*-
"""重写申请分页的命名填充：批量查询、无 N+1"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
for root, _, fs in os.walk(J):
    if 'ApplicationServiceImpl.java' in fs:
        P = os.path.join(root, 'ApplicationServiceImpl.java')
        break

s = io.open(P, encoding='utf-8').read()

start = s.find('List<ApplicationVO> rows = page.getRecords()')
end_m = re.search(r'(\n\s*return new PageResult)', s[start:])
if start == -1 or not end_m:
    print('!! 锚点未找到')
else:
    end = start + end_m.start(1) + 1
    block = '''List<BizApplication> records = page.getRecords();
        // 批量填充申请人姓名：一次 in 查询，避免 N+1；前端不再显示 personId 数字
        java.util.Map<Long, String> personNameMap = new java.util.HashMap<>();
        java.util.List<Long> personIds = records.stream()
                .map(BizApplication::getPersonId)
                .filter(java.util.Objects::nonNull)
                .distinct()
                .toList();
        if (!personIds.isEmpty()) {
            for (com.yundao.bp.person.entity.Person p : personMapper.selectBatchIds(personIds)) {
                personNameMap.put(p.getId(), p.getPersonName());
            }
        }
        List<ApplicationVO> rows = records.stream()
                .map(e -> ApplicationVO.from(e, personNameMap.get(e.getPersonId())))
                .toList();
'''
    s = s[:start] + block + s[end:]
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ 已重写（批量查询，无 N+1）')

    print('\n--- 结果 ---')
    i = s.find('List<BizApplication> records')
    print(s[i:i + 900])
