# -*- coding: utf-8 -*-
"""二级管理权规则：

1. 级别定义
   OWNERSHIP          所有权（组织/产权方）—— 可创建 MANAGEMENT
   MANAGEMENT         管理权 —— 可创建/删除 SECONDARY_MANAGEMENT
   SECONDARY_MANAGEMENT 二级管理权 —— 对设备的管理功能与 MANAGEMENT 一致，
                       但**不能创建其他二级或下级管理权**

2. 校验点
   · apply：申请 SECONDARY_MANAGEMENT 时，当前用户必须在同一空间上有
     OWNERSHIP/MANAGEMENT 且 allowManage=1
   · revoke：撤销 SECONDARY_MANAGEMENT 时同样校验
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'grant',
                 'service', 'impl', 'GrantServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

if 'SECONDARY_MANAGEMENT' in s:
    print('已存在')
    raise SystemExit(0)

# ---- 1) 权限位：二级管理权与一级管理权一致 ----
s = s.replace('''        e.setAllowManage("OWNERSHIP".equals(cmd.grantLevel())
                || "MANAGEMENT".equals(cmd.grantLevel()) ? 1 : 0);''',
'''        e.setAllowManage("OWNERSHIP".equals(cmd.grantLevel())
                || "MANAGEMENT".equals(cmd.grantLevel())
                || "SECONDARY_MANAGEMENT".equals(cmd.grantLevel()) ? 1 : 0);''', 1)

# ---- 2) apply 前置校验 ----
anchor = '''        String idemKey = idempotentKey(cmd.personId(), cmd.spaceId(), cmd.grantLevel(),'''
s = s.replace(anchor, '''        requireManagerForSecondary(cmd.grantLevel(), cmd.spaceId());
''' + anchor, 1)

# ---- 3) 校验方法 ----
helper = '''
    /**
     * 二级管理权的授予约束：
     * 只有在该空间上拥有 OWNERSHIP / MANAGEMENT 且 allowManage=1 的人，
     * 才能创建或删除 SECONDARY_MANAGEMENT；二级管理权本身不能再向下授予。
     */
    private void requireManagerForSecondary(String grantLevel, Long spaceId) {
        if (!"SECONDARY_MANAGEMENT".equals(grantLevel)) {
            return;
        }
        Long me = TenantContext.userId();
        if (me == null) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "无法识别当前操作人，不能授予二级管理权");
        }
        Long personId = me;
        if (userMapper != null) {
            com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(me);
            if (u != null && u.getPersonId() != null) {
                personId = u.getPersonId();
            }
        }
        Long granted = entitlementMapper.selectCount(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getPersonId, personId)
                        .eq(spaceId != null, GrantEntitlement::getSpaceId, spaceId)
                        .in(GrantEntitlement::getGrantLevel,
                                java.util.List.of("OWNERSHIP", "MANAGEMENT"))
                        .eq(GrantEntitlement::getAllowManage, 1)
                        .eq(GrantEntitlement::getGrantStatus, "ACTIVE"));
        if (granted == null || granted == 0) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "只有拥有管理权或所有权的人才能授予/撤销二级管理权");
        }
    }
'''
i = s.rstrip().rfind('}')
s = s[:i] + helper + s[i:]

# ---- 4) 依赖注入 ----
inject = '''
    /** 用户（操作人 → 人员映射） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamUserMapper userMapper;
'''
if 'private com.yundao.bp.iam.mapper.IamUserMapper userMapper' not in s:
    j = s.find('    public GrantServiceImpl(')
    s = s[:j] + inject + '\n' + s[j:]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('GrantServiceImpl：二级管理权校验已加')
