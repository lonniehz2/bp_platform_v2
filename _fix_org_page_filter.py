# -*- coding: utf-8 -*-
"""给 /orgs 分页增加 parentId 与「含下级」筛选，使左侧选树能过滤右侧"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1) Controller ----------
CP = None
for root, _, fs in os.walk(J):
    if 'OrgController.java' in fs:
        CP = os.path.join(root, 'OrgController.java')
        break
s = io.open(CP, encoding='utf-8').read()

old = '''    @GetMapping
    public R<PageResult<OrgVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                    @RequestParam(defaultValue = "20") long pageSize,
                                    @RequestParam(required = false) String keyword) {
        return R.ok(orgService.page(pageNum, pageSize, keyword));
    }'''
new = '''    @GetMapping
    public R<PageResult<OrgVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                    @RequestParam(defaultValue = "20") long pageSize,
                                    @RequestParam(required = false) String keyword,
                                    @RequestParam(required = false) Long parentId,
                                    @RequestParam(required = false) Boolean includeSubtree) {
        return R.ok(orgService.page(pageNum, pageSize, keyword, parentId, includeSubtree));
    }'''
assert old in s, 'Controller 锚点未找到'
s = s.replace(old, new, 1)
io.open(CP, 'w', encoding='utf-8').write(s)
print('  ✓ OrgController 支持 parentId / includeSubtree')

# ---------- 2) Service 接口 ----------
IP = None
for root, _, fs in os.walk(J):
    if 'OrgService.java' in fs:
        IP = os.path.join(root, 'OrgService.java')
        break
t = io.open(IP, encoding='utf-8').read()
m = re.search(r'PageResult<OrgVO> page\([^)]*\);', t)
if m:
    t = t.replace(m.group(0),
                  'PageResult<OrgVO> page(long pageNum, long pageSize, String keyword,\n'
                  '                            Long parentId, Boolean includeSubtree);', 1)
    io.open(IP, 'w', encoding='utf-8').write(t)
    print('  ✓ OrgService 接口更新')

# ---------- 3) 实现 ----------
SP = None
for root, _, fs in os.walk(J):
    if 'OrgServiceImpl.java' in fs:
        SP = os.path.join(root, 'OrgServiceImpl.java')
        break
u = io.open(SP, encoding='utf-8').read()

m = re.search(r'public PageResult<OrgVO> page\(long pageNum, long pageSize, String keyword\)\s*\{',
              u)
if not m:
    print('  !! 实现方法签名未匹配')
else:
    # 找到方法体结束
    start = m.start()
    i = u.find('{', start)
    depth = 0
    j = i
    while j < len(u):
        if u[j] == '{':
            depth += 1
        elif u[j] == '}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    body = u[i:j + 1]
    print('\n原实现体：\n' + body[:600])

    new_impl = '''public PageResult<OrgVO> page(long pageNum, long pageSize, String keyword,
                                  Long parentId, Boolean includeSubtree) {
        LambdaQueryWrapper<IamOrg> qw = new LambdaQueryWrapper<IamOrg>()
                .orderByAsc(IamOrg::getSortNo)
                .orderByAsc(IamOrg::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(IamOrg::getOrgName, keyword)
                    .or().like(IamOrg::getOrgCode, keyword));
        }
        if (parentId != null) {
            if (Boolean.TRUE.equals(includeSubtree)) {
                // 含下级：用 path 前缀匹配（path 末尾带自身 id 时也能命中）
                IamOrg parent = orgMapper.selectById(parentId);
                if (parent == null) {
                    return PageResult.empty(pageNum, pageSize);
                }
                String prefix = parent.getOrgPath() == null ? "" : parent.getOrgPath();
                qw.and(w -> w.likeRight(IamOrg::getOrgPath, prefix)
                        .or().eq(IamOrg::getId, parentId));
            } else {
                // 默认只取直接下级，符合「点节点看其子组织」的直觉
                qw.eq(IamOrg::getParentId, parentId);
            }
        }
        IPage<IamOrg> page = orgMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<OrgVO> rows = page.getRecords().stream().map(OrgVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }'''
    u = u[:start] + new_impl + u[j + 1:]
    io.open(SP, 'w', encoding='utf-8').write(u)
    print('\n  ✓ OrgServiceImpl 已实现 parentId / includeSubtree')
