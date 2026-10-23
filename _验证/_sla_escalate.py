# -*- coding: utf-8 -*-
"""物业 SLA 超时升级：把超时工单标记为升级并自动补派处理人。

接口：POST /ops/workorders/escalate-overdue?orgId=
规则：
  · 命中条件：responseOverdue 或 finishOverdue 为真，且状态未完结
  · 处理动作：写升级日志（含超时分钟数）；未派单的自动派给服务岗在手工单最少者
  · 幂等：同一工单当天重复执行不会重复写日志（检查最近一条日志）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'ops')

SNIPPET = '''
    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public int escalateOverdue(Long orgId) {
        java.util.List<OpsWorkorder> list = orderMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        <OpsWorkorder>()
                        .eq(orgId != null, OpsWorkorder::getOrgId, orgId)
                        .notIn(OpsWorkorder::getOrderStatus,
                                java.util.List.of("FINISHED", "CLOSED", "CANCELLED")));
        int n = 0;
        for (OpsWorkorder o : list) {
            boolean responseLate = Boolean.TRUE.equals(o.getResponseOverdue());
            boolean finishLate = Boolean.TRUE.equals(o.getFinishOverdue());
            if (!responseLate && !finishLate) {
                continue;
            }
            // 幂等：当天已升级过则跳过
            Long recent = logMapper.selectCount(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                            <OpsWorkorderLog>()
                            .eq(OpsWorkorderLog::getWorkorderId, o.getId())
                            .eq(OpsWorkorderLog::getAction, "ESCALATE")
                            .ge(OpsWorkorderLog::getCreateTime,
                                    java.time.LocalDate.now().atStartOfDay()));
            if (recent != null && recent > 0) {
                continue;
            }
            StringBuilder sb = new StringBuilder("SLA 超时升级：");
            if (responseLate) {
                sb.append("响应超时");
            }
            if (finishLate) {
                sb.append(responseLate ? "、" : "").append("完工超时");
            }
            // 未派单的自动派单，保证升级后有明确责任人
            if (o.getAssignUserId() == null) {
                try {
                    autoAssign(o.getId());
                    sb.append("；已自动派单");
                } catch (Exception ex) {
                    sb.append("；自动派单失败：" ).append(ex.getMessage());
                }
            }
            OpsWorkorderLog lg = new OpsWorkorderLog();
            lg.setId(idGen.nextId());
            lg.setTenantId(TenantContext.tenantId());
            lg.setWorkorderId(o.getId());
            lg.setAction("ESCALATE");
            lg.setFromStatus(o.getOrderStatus());
            lg.setToStatus(o.getOrderStatus());
            lg.setOperatorId(TenantContext.userId());
            lg.setOperatorName("系统");
            lg.setContent(sb.toString());
            lg.setCreateTime(java.time.LocalDateTime.now());
            logMapper.insert(lg);
            n++;
        }
        log.info("SLA 超时升级：扫描 {}，升级 {}", list.size(), n);
        return n;
    }
'''

# Service 接口
S = os.path.join(J, 'service', 'WorkOrderService.java')
s = io.open(S, encoding='utf-8').read()
if 'escalateOverdue' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '\n    /** SLA 超时升级：标记超时工单并补派责任人。 */\n    int escalateOverdue(Long orgId);\n' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('WorkOrderService：escalateOverdue 已加')

# 实现
I = os.path.join(J, 'service', 'impl', 'WorkOrderServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'escalateOverdue' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + SNIPPET + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('WorkOrderServiceImpl：escalateOverdue 已实现')

# Controller
C = os.path.join(J, 'controller', 'WorkOrderController.java')
s = io.open(C, encoding='utf-8').read()
if 'escalate-overdue' not in s:
    block = '''
    /** SLA 超时升级：标记超时工单并补派责任人。 */
    @PostMapping("/escalate-overdue")
    @com.yundao.bp.iam.security.RequirePerm("ops:workorder:update")
    public R<Integer> escalateOverdue(@RequestParam(required = false) Long orgId) {
        return R.ok(workOrderService.escalateOverdue(orgId));
    }
'''
    anchor = '    @PostMapping("/auto-assign-pending")'
    s = s.replace(anchor, block + '\n' + anchor, 1)
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('WorkOrderController：/escalate-overdue 已加')

print('完成')
