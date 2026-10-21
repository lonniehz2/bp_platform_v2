# -*- coding: utf-8 -*-
"""替换整段为批量查询版本（ends at return PageResult）"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
for root, _, fs in os.walk(J):
    if 'ApplicationServiceImpl.java' in fs:
        P = os.path.join(root, 'ApplicationServiceImpl.java')
        break

s = io.open(P, encoding='utf-8').read()

start = s.find('        List<ApplicationVO> rows = page.getRecords().stream()')
ret = s.find('        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);', start)
if start == -1 or ret == -1:
    print('!! 定位失败 start=%s ret=%s' % (start, ret))
else:
    block = '''        List<BizApplication> records = page.getRecords();
        // 批量填充申请人姓名：一次 in 查询，避免 N+1，前端不再显示 personId 数字
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
    s = s[:start] + block + s[ret:]
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ 已替换为批量版本')
    i = s.find('List<BizApplication> records')
    print('\n' + s[i:i + 800])
