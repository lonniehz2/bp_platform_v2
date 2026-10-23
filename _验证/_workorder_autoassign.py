# -*- coding: utf-8 -*-
"""物业工单自动派单：按「同组织 + 服务岗/工作人员 + 在手工单最少」规则分配。

接口：
  POST /ops/workorders/{id}/auto-assign     单条自动派单
  POST /ops/workorders/auto-assign-pending  批量派单（所有待派单）
规则：
  1. 只派新单（PENDING），已派单/已完结的跳过
  2. 候选人 = 同组织的启用用户，且拥有 SERVICE_CLERK / STAFF / ACCEPTOR 角色
  3. 取在手工单（未关闭/未取消）数量最少者；相同则按用户 ID 升序，保证可复现
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'ops')

# ---------- Service 接口 ----------
S = os.path.join(J, 'service', 'WorkOrderService.java')
s = io.open(S, encoding='utf-8').read()
if 'autoAssign' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 自动派单：按同组织服务岗在手工单最少者分配。 */
    WorkOrderVO autoAssign(Long id);

    /** 批量自动派单：处理所有待派单工单，返回成功派单数。 */
    int autoAssignPending(Long orgId);
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('WorkOrderService：autoAssign 已加')

# ---------- 实现 ----------
I = os.path.join(J, 'service', 'impl', 'WorkOrderServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'autoAssign' not in s:
    inject = '''
    /** 用户（派单候选人） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamUserMapper assignUserMapper;

    /** 用户-角色关系 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamUserRoleMapper assignUserRoleMapper;

    /** 角色（按编码筛服务岗） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamRoleMapper assignRoleMapper;
'''
    if 'assignUserMapper' not in s:
        j = s.find('    public WorkOrderServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]

    impl = '''
    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public WorkOrderVO autoAssign(Long id) {
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus st = statusOf(e);
        if (st != WorkOrderStatus.PENDING) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "只有待派单工单可以自动派单，当前状态：" + st.label());
        }
        if (assignUserMapper == null || assignUserRoleMapper == null
                || assignRoleMapper == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("派单服务未就绪");
        }
        Long candidate = pickAssignee(e.getOrgId());
        if (candidate == null) {
            throw com.yundao.bp.common.exception.BizException.stateConflict(
                    "该组织下没有可派单的服务岗人员，请先分配角色");
        }
        com.yundao.bp.iam.entity.IamUser u = assignUserMapper.selectById(candidate);
        String name = u == null ? null
                : (u.getRealName() != null ? u.getRealName() : u.getUsername());
        String phone = u == null ? null : u.getPhone();
        return assign(id, candidate, name, phone, "系统自动派单（在手工单最少）");
    }

    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public int autoAssignPending(Long orgId) {
        java.util.List<OpsWorkorder> list = mapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        <OpsWorkorder>()
                        .eq(orgId != null, OpsWorkorder::getOrgId, orgId)
                        .eq(OpsWorkorder::getOrderStatus, WorkOrderStatus.PENDING.name()));
        int n = 0;
        for (OpsWorkorder o : list) {
            try {
                autoAssign(o.getId());
                n++;
            } catch (Exception ex) {
                log.debug("工单 {} 自动派单跳过：{}", o.getWorkorderNo(), ex.getMessage());
            }
        }
        log.info("批量自动派单：待派 {}，成功 {}", list.size(), n);
        return n;
    }

    /** 选择在手工单最少的服务岗人员。 */
    private Long pickAssignee(Long orgId) {
        java.util.List<String> serviceRoleCodes = java.util.List.of(
                "SERVICE_CLERK", "STAFF", "ACCEPTOR");
        java.util.List<Long> roleIds = new java.util.ArrayList<>();
        for (com.yundao.bp.iam.entity.IamRole r : assignRoleMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        <com.yundao.bp.iam.entity.IamRole>()
                        .in(com.yundao.bp.iam.entity.IamRole::getRoleCode, serviceRoleCodes))) {
            roleIds.add(r.getId());
        }
        if (roleIds.isEmpty()) {
            return null;
        }
        java.util.LinkedHashSet<Long> userIds = new java.util.LinkedHashSet<>();
        for (com.yundao.bp.iam.entity.IamUserRole ur : assignUserRoleMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        <com.yundao.bp.iam.entity.IamUserRole>()
                        .in(com.yundao.bp.iam.entity.IamUserRole::getRoleId, roleIds))) {
            userIds.add(ur.getUserId());
        }
        if (userIds.isEmpty()) {
            return null;
        }
        Long best = null;
        long bestLoad = Long.MAX_VALUE;
        java.util.List<Long> candidates = new java.util.ArrayList<>(userIds);
        java.util.Collections.sort(candidates);
        for (Long uid : candidates) {
            com.yundao.bp.iam.entity.IamUser u = assignUserMapper.selectById(uid);
            if (u == null || !"ENABLED".equals(u.getUserStatus())) {
                continue;
            }
            if (orgId != null && u.getOrgId() != null && !orgId.equals(u.getOrgId())) {
                continue;
            }
            Long load = mapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <OpsWorkorder>()
                            .eq(OpsWorkorder::getAssignUserId, uid)
                            .notIn(OpsWorkorder::getOrderStatus,
                                    java.util.List.of("CLOSED", "CANCELLED", "FINISHED")));
            long n = load == null ? 0 : load;
            if (n < bestLoad) {
                bestLoad = n;
                best = uid;
            }
        }
        return best;
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('WorkOrderServiceImpl：自动派单已实现')

# ---------- Controller ----------
C = os.path.join(J, 'controller', 'WorkOrderController.java')
s = io.open(C, encoding='utf-8').read()
if 'auto-assign' not in s:
    block = '''
    /** 自动派单：同组织服务岗在手工单最少者。 */
    @PostMapping("/{id}/auto-assign")
    @com.yundao.bp.iam.security.RequirePerm("ops:workorder:assign")
    public R<WorkOrderVO> autoAssign(@PathVariable Long id) {
        return R.ok(workOrderService.autoAssign(id));
    }

    /** 批量自动派单（所有待派单）。 */
    @PostMapping("/auto-assign-pending")
    @com.yundao.bp.iam.security.RequirePerm("ops:workorder:assign")
    public R<Integer> autoAssignPending(@RequestParam(required = false) Long orgId) {
        return R.ok(workOrderService.autoAssignPending(orgId));
    }
'''
    anchor = '    @PostMapping("/{id}/assign")'
    if anchor in s:
        s = s.replace(anchor, block + '\n' + anchor, 1)
    else:
        i = s.rstrip().rfind('}')
        s = s[:i] + block + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('WorkOrderController：/auto-assign 已加')

print('完成')
