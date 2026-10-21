# -*- coding: utf-8 -*-
"""修正「含下级」路径前缀：org_path 不含自身，需拼接 id"""
import io
import re

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\iam\service\impl\OrgServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

old = '''            if (Boolean.TRUE.equals(includeSubtree)) {
                // 含下级：用 path 前缀匹配（path 末尾带自身 id 时也能命中）
                IamOrg parent = orgMapper.selectById(parentId);
                if (parent == null) {
                    return PageResult.empty(pageNum, pageSize);
                }
                String prefix = parent.getOrgPath() == null ? "" : parent.getOrgPath();
                qw.and(w -> w.likeRight(IamOrg::getOrgPath, prefix)
                        .or().eq(IamOrg::getId, parentId));
            } else {'''
new = '''            if (Boolean.TRUE.equals(includeSubtree)) {
                // 含下级：org_path 存的是「祖先路径」且不含自身，
                // 因此血缘前缀必须是 path + 自身id + "/"，否则根节点 path 为空
                // 会匹配到全表。
                IamOrg parent = orgMapper.selectById(parentId);
                if (parent == null) {
                    return PageResult.empty(pageNum, pageSize);
                }
                String base = parent.getOrgPath() == null ? "" : parent.getOrgPath();
                String lineage = base + parentId + "/";
                qw.and(w -> w.likeRight(IamOrg::getOrgPath, lineage)
                        .or().eq(IamOrg::getId, parentId));
            } else {'''
assert old in s, '锚点未找到'
s = s.replace(old, new, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 修正血缘前缀 = org_path + id + "/"')
