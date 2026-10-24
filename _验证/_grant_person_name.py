# -*- coding: utf-8 -*-
"""授权列表补充人员姓名：GrantVO 增加 personName，page 批量回填。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'grant')

# 1) VO 增加 personName + 双参 from
V = os.path.join(J, 'dto', 'GrantVO.java')
s = io.open(V, encoding='utf-8').read()
if 'personName' not in s:
    s = s.replace('        Long personId,', '        Long personId,\n        String personName,', 1)
    s = s.replace('    public static GrantVO from(GrantEntitlement e) {',
'''    public static GrantVO from(GrantEntitlement e) {
        return from(e, null);
    }

    public static GrantVO from(GrantEntitlement e, String personName) {''', 1)
    # 在构造里插入 personName（紧跟 personId）
    s = s.replace('e.getPersonId(),', 'e.getPersonId(), personName,', 1)
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('GrantVO：personName 已加')

# 2) page 批量回填
S = os.path.join(J, 'service', 'impl', 'GrantServiceImpl.java')
s = io.open(S, encoding='utf-8').read()
if 'personNameOf' not in s:
    old = '''        IPage<GrantEntitlement> page = entitlementMapper.selectPage(new Page<>(pageNum, pageSize), qw);'''
    if old in s:
        s = s.replace(old, '''        IPage<GrantEntitlement> page = entitlementMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        java.util.Map<Long, String> names = personNamesOf(page.getRecords());''', 1)
        # 替换该方法的返回
        s = s.replace('        return PageResult.of(page.getTotal(), pageNum, pageSize,\n'
                      '                page.getRecords().stream().map(GrantVO::from).toList());',
                      '        return PageResult.of(page.getTotal(), pageNum, pageSize,\n'
                      '                page.getRecords().stream()\n'
                      '                        .map(x -> GrantVO.from(x, names.get(x.getPersonId())))\n'
                      '                        .toList());')
        helper = '''
    /** 批量取人员姓名（一次查询，避免逐行回表）。 */
    private java.util.Map<Long, String> personNamesOf(
            java.util.List<GrantEntitlement> rows) {
        java.util.Map<Long, String> out = new java.util.HashMap<>();
        if (personMapper == null || rows == null || rows.isEmpty()) {
            return out;
        }
        java.util.List<Long> ids = rows.stream()
                .map(GrantEntitlement::getPersonId).filter(java.util.Objects::nonNull)
                .distinct().toList();
        if (ids.isEmpty()) {
            return out;
        }
        for (com.yundao.bp.person.entity.Person p : personMapper.selectBatchIds(ids)) {
            out.put(p.getId(), p.getPersonName());
        }
        return out;
    }
'''
        i = s.rstrip().rfind('}')
        s = s[:i] + helper + s[i:]
        inject = '''
    /** 人员（授权列表回填姓名） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.person.mapper.PersonMapper personMapper;
'''
        if 'private com.yundao.bp.person.mapper.PersonMapper personMapper' not in s:
            j = s.find('    public GrantServiceImpl(')
            s = s[:j] + inject + '\n' + s[j:]
        io.open(S, 'w', encoding='utf-8', newline='').write(s)
        print('GrantServiceImpl：人员姓名批量回填已加')
    else:
        print('未找到 page 查询语句')
