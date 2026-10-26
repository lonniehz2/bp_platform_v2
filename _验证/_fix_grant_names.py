# -*- coding: utf-8 -*-
"""两处细节修正：
1) 授权列表返回人员姓名（GrantVO.personIdName 目前为空）
2) 枚举分组优先级：grantStatus 的 EFFECTIVE 不应显示成合同的「履约中」
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 1) 枚举：把 grantLevel / grantStatus 放到 TYPE_OVERRIDE ----------
P = os.path.join(ROOT, 'frontend', 'src', 'constants', 'enums.js')
s = io.open(P, encoding='utf-8').read()

# 删除之前加到 GLOBAL 的块
OLD_GLOBAL = """  // ---------- 通行授权 ----------
  grantLevel: {
    OWNERSHIP: '产权级', MANAGEMENT: '管理级', USAGE: '使用级', VISIT: '访客级'
  },
  grantStatus: {
    PENDING: '待生效', EFFECTIVE: '已生效', EXPIRED: '已到期',
    FROZEN: '已冻结', REVOKED: '已撤销'
  },

"""
if OLD_GLOBAL in s:
    s = s.replace(OLD_GLOBAL, '', 1)
    print('已从 GLOBAL 移除授权枚举')

# 加到 TYPE_OVERRIDE（字段级优先）
if "grantStatus: {" not in s.split('const TYPE_OVERRIDE')[1].split('}')[0]:
    OLD_TAIL = """  dayStatus: { FREE: '空闲', FULL: '满房', LOCKED: '锁定', CLOSED: '关闭' }
}"""
    NEW_TAIL = """  dayStatus: { FREE: '空闲', FULL: '满房', LOCKED: '锁定', CLOSED: '关闭' },
  // 授权：EFFECTIVE 在合同里是「履约中」，这里必须是「已生效」
  grantStatus: {
    PENDING: '待生效', EFFECTIVE: '已生效', EXPIRED: '已到期',
    FROZEN: '已冻结', REVOKED: '已撤销'
  },
  grantLevel: {
    OWNERSHIP: '产权级', MANAGEMENT: '管理级', USAGE: '使用级', VISIT: '访客级'
  }
}"""
    if OLD_TAIL in s:
        s = s.replace(OLD_TAIL, NEW_TAIL, 1)
        print('已加入 TYPE_OVERRIDE')

io.open(P, 'w', encoding='utf-8', newline='').write(s)

# ---------- 2) 后端：授权列表补人员姓名 ----------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'grant', 'service', 'impl', 'GrantServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

if 'fillPersonNames' not in s:
    # 注入 PersonMapper
    s = s.replace("    private final GrantEntitlementMapper entitlementMapper;",
                  "    private final GrantEntitlementMapper entitlementMapper;\n"
                  "    @org.springframework.beans.factory.annotation.Autowired(required = false)\n"
                  "    private com.yundao.bp.person.mapper.PersonMapper personMapper;", 1)

    OLD_PAGE = """        List<GrantVO> rows = page.getRecords().stream().map(GrantVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);"""
    NEW_PAGE = """        List<GrantVO> rows = fillPersonNames(page.getRecords());
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);"""
    if OLD_PAGE in s:
        s = s.replace(OLD_PAGE, NEW_PAGE, 1)

    # 追加填充方法
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 批量补人员姓名（列表展示用，避免前端显示人员ID）。 */
    private List<GrantVO> fillPersonNames(List<GrantEntitlement> list) {
        if (list == null || list.isEmpty() || personMapper == null) {
            return list == null ? List.of()
                    : list.stream().map(GrantVO::from).toList();
        }
        java.util.Set<Long> ids = new java.util.HashSet<>();
        for (GrantEntitlement e : list) {
            if (e.getPersonId() != null) {
                ids.add(e.getPersonId());
            }
        }
        java.util.Map<Long, String> nameOf = new java.util.HashMap<>();
        if (!ids.isEmpty()) {
            for (com.yundao.bp.person.entity.Person p
                    : personMapper.selectBatchIds(ids)) {
                nameOf.put(p.getId(), p.getPersonName());
            }
        }
        return list.stream()
                .map(e -> GrantVO.from(e, nameOf.get(e.getPersonId())))
                .toList();
    }
''' + s[i:]
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('后端已补人员姓名填充')
