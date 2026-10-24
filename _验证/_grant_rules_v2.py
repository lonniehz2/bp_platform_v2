# -*- coding: utf-8 -*-
"""按确认后的规则修正授权模型：

1. 设备初始绑定到账号 → 该账号同时拥有 OWNERSHIP（所有权）与 MANAGEMent 能力
   （OWNERSHIP 已 allowManage=1）
2. 只有所有权者可以把「管理权」转移给其他账号（可带到期时间）
3. 只有管理权（无所有权）的账号：不能再次转让，只能归还自己的管理权
4. 管理权到期自动归还：定时把 valid_end 已过的 ACTIVE 权益置为 EXPIRED
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'grant',
                 'service', 'impl', 'GrantServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

# ---------- 1) 替换旧的二级管理权校验 ----------
start = s.find('    /**\n     * 二级管理权的授予约束')
if start < 0:
    start = s.find('    private void requireManagerForSecondary(')
    start = s.rfind('    /**', 0, start) if start > 0 else -1
end = s.find('    @Override', start if start > 0 else 0)

new_rule = '''    /**
     * 管理权转移约束（按业务确认口径）：
     * <ul>
     *   <li>设备初始绑定到某账号 → 该账号拥有所有权（OWNERSHIP，含管理能力）</li>
     *   <li><b>只有所有权者</b>可以把管理权转移给其他账号</li>
     *   <li>只有管理权（无所有权）的账号不能再转让，只能归还自己的管理权</li>
     * </ul>
     */
    private void requireOwnershipForTransfer(String grantLevel, Long spaceId) {
        if (!"MANAGEMENT".equals(grantLevel)
                && !"SECONDARY_MANAGEMENT".equals(grantLevel)) {
            return;
        }
        Long me = TenantContext.userId();
        if (me == null) {
            return;   // 系统任务/内部调用
        }
        if (isAdmin(me)) {
            return;   // 组织管理员可代为转移
        }
        Long personId = me;
        if (userMapper != null) {
            com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(me);
            if (u != null && u.getPersonId() != null) {
                personId = u.getPersonId();
            }
        }
        Long owner = entitlementMapper.selectCount(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getPersonId, personId)
                        .eq(spaceId != null, GrantEntitlement::getSpaceId, spaceId)
                        .eq(GrantEntitlement::getGrantLevel, "OWNERSHIP")
                        .eq(GrantEntitlement::getAllowManage, 1)
                        .eq(GrantEntitlement::getGrantStatus, "ACTIVE"));
        if (owner != null && owner > 0) {
            return;
        }
        Long manager = entitlementMapper.selectCount(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getPersonId, personId)
                        .eq(spaceId != null, GrantEntitlement::getSpaceId, spaceId)
                        .eq(GrantEntitlement::getGrantLevel, "MANAGEMENT")
                        .eq(GrantEntitlement::getGrantStatus, "ACTIVE"));
        if (manager != null && manager > 0) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "只有所有权者可以转移管理权；管理权持有者只能归还自己的管理权");
        }
        throw com.yundao.bp.common.exception.BizException.stateConflict(
                "只有该空间的所有权者才能授予管理权");
    }

    /** 是否组织管理员（跨组织代管场景放行）。 */
    private boolean isAdmin(Long userId) {
        if (userMapper == null) {
            return false;
        }
        com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(userId);
        return u != null && ("PLATFORM".equals(u.getUserType())
                || "ADMIN".equals(u.getUserType()));
    }

'''

if start > 0 and end > start:
    s = s[:start] + new_rule + s[end:]
    print('已替换为「所有权者才能转移管理权」规则')
else:
    print('未找到旧校验方法，改为追加')
    i = s.rstrip().rfind('}')
    s = s[:i] + new_rule + s[i:]

# ---------- 2) apply 调用改名 ----------
s = s.replace('requireManagerForSecondary(cmd.grantLevel(), cmd.spaceId());',
              'requireOwnershipForTransfer(cmd.grantLevel(), cmd.spaceId());')

# ---------- 3) revoke 权限校验：所有权者可强制收回 / 持有者可归还 ----------
anchor = '''        GrantStatus cur = GrantStatus.valueOf(e.getGrantStatus());'''
s = s.replace(anchor, '''        requireRevokeRight(e);
''' + anchor, 1)

revoke_right = '''
    /**
     * 撤销/归还权限：
     * 所有权者可强制收回；权益持有者本人可归还；管理员可代操作。
     */
    private void requireRevokeRight(GrantEntitlement e) {
        Long me = TenantContext.userId();
        if (me == null || isAdmin(me)) {
            return;
        }
        Long personId = me;
        if (userMapper != null) {
            com.yundao.bp.iam.entity.IamUser u = userMapper.selectById(me);
            if (u != null && u.getPersonId() != null) {
                personId = u.getPersonId();
            }
        }
        if (e.getPersonId() != null && e.getPersonId().equals(personId)) {
            return;   // 本人归还
        }
        Long owner = entitlementMapper.selectCount(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getPersonId, personId)
                        .eq(e.getSpaceId() != null, GrantEntitlement::getSpaceId, e.getSpaceId())
                        .eq(GrantEntitlement::getGrantLevel, "OWNERSHIP")
                        .eq(GrantEntitlement::getGrantStatus, "ACTIVE"));
        if (owner == null || owner == 0) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "无权撤销：只有所有权者或权益持有人本人可以操作");
        }
    }

    @Override
    public int expireOverdue() {
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        java.util.List<GrantEntitlement> list = entitlementMapper.selectList(
                new LambdaQueryWrapper<GrantEntitlement>()
                        .eq(GrantEntitlement::getGrantStatus, "ACTIVE")
                        .isNotNull(GrantEntitlement::getValidEnd)
                        .lt(GrantEntitlement::getValidEnd, now));
        int n = 0;
        for (GrantEntitlement e : list) {
            if (e.getValidEnd() != null && e.getValidEnd().isBefore(now)) {
                e.setGrantStatus("EXPIRED");
                e.setRevokeReason("管理权到期自动归还");
                entitlementMapper.updateById(e);
                n++;
            }
        }
        if (n > 0) {
            log.info("权益到期归还：{} 条", n);
        }
        return n;
    }
'''
i = s.rstrip().rfind('}')
s = s[:i] + revoke_right + s[i:]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已加 revoke 权限校验与到期归还 expireOverdue')
