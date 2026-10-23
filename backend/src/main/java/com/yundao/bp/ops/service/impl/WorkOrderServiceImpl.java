package com.yundao.bp.ops.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.ops.constant.SlaStatus;
import com.yundao.bp.ops.constant.WorkOrderAction;
import com.yundao.bp.ops.constant.WorkOrderStatus;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsWorkorder;
import com.yundao.bp.ops.entity.OpsWorkorderLog;
import com.yundao.bp.ops.mapper.OpsWorkorderLogMapper;
import com.yundao.bp.ops.mapper.OpsWorkorderMapper;
import com.yundao.bp.ops.service.WorkOrderService;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 工单服务实现。
 *
 * <p><b>SLA 计算口径</b>（考核依据）：
 * <ul>
 *   <li><b>响应</b>：接单时间 - 创建时间，超过 {@code slaResponseMinutes} 记 {@code RESPONSE_TIMEOUT}</li>
 *   <li><b>完工</b>：完工时间 - 创建时间，超过 {@code slaFinishMinutes} 记 {@code FINISH_TIMEOUT}</li>
 *   <li>完工超时优先级高于响应超时（终态以更严重的为准）</li>
 * </ul>
 */
@Service
public class WorkOrderServiceImpl implements WorkOrderService {

    private static final Logger log = LoggerFactory.getLogger(WorkOrderServiceImpl.class);

    /** 各工单类型的默认 SLA（分钟）：{响应, 完工} */
    private static final Map<String, int[]> DEFAULT_SLA = Map.of(
            "REPAIR", new int[]{30, 240},
            "COMPLAINT", new int[]{60, 480},
            "INSPECT", new int[]{120, 1440},
            "INSTALL", new int[]{240, 2880},
            "MAINTAIN", new int[]{240, 2880},
            "CONSULT", new int[]{60, 480},
            "ALERT", new int[]{15, 120},
            "VISIT", new int[]{120, 1440});

    private final OpsWorkorderMapper orderMapper;
    private final OpsWorkorderLogMapper logMapper;
    private final SnowflakeIdGenerator idGen;


    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按数据范围追加组织与人员条件（full=true 时组织也过滤）。 */
    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol,
            boolean full) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf()) {
            if (scope.personId() == null) {
                qw.eq(personCol, -1L);
            } else {
                qw.eq(personCol, scope.personId());
            }
            return;
        }
        if (!full) {
            return;     // 实体无组织列时，ORG/ORG_SUB 不额外限制
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty()) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }


    /** 用户（派单候选人） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamUserMapper assignUserMapper;

    /** 用户-角色关系 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamUserRoleMapper assignUserRoleMapper;

    /** 角色（按编码筛服务岗） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.mapper.IamRoleMapper assignRoleMapper;

    public WorkOrderServiceImpl(OpsWorkorderMapper orderMapper,
                                OpsWorkorderLogMapper logMapper,
                                SnowflakeIdGenerator idGen) {
        this.orderMapper = orderMapper;
        this.logMapper = logMapper;
        this.idGen = idGen;
    }

    // ==================== 创建 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO create(WorkOrderCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        int[] def = DEFAULT_SLA.getOrDefault(cmd.orderType(), new int[]{60, 480});
        int respMin = cmd.slaResponseMinutes() != null ? cmd.slaResponseMinutes() : def[0];
        int finMin = cmd.slaFinishMinutes() != null ? cmd.slaFinishMinutes() : def[1];
        if (respMin <= 0 || finMin <= 0) {
            throw BizException.paramInvalid("SLA 时限必须为正数（分钟）");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        OpsWorkorder e = new OpsWorkorder();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setWorkorderNo("W" + id);
        e.setOrderType(cmd.orderType());
        e.setOrderSource(blankToNull(cmd.orderSource()) == null ? "STAFF" : cmd.orderSource());
        e.setOrgId(cmd.orgId());
        e.setSpaceId(cmd.spaceId());
        e.setHouseId(cmd.houseId());
        e.setDeviceId(cmd.deviceId());
        e.setDeviceType(cmd.deviceType());
        e.setPersonId(cmd.personId());
        e.setReporterName(cmd.reporterName());
        e.setReporterPhone(cmd.reporterPhone());
        e.setOrderTitle(cmd.orderTitle());
        e.setOrderContent(cmd.orderContent());
        e.setOrderAddress(cmd.orderAddress());
        e.setImages(cmd.images());
        e.setSlaResponseMinutes(respMin);
        e.setSlaFinishMinutes(finMin);
        e.setSlaStatus(SlaStatus.ON_TIME.name());
        e.setIsDeviceChanged(0);
        e.setOrderStatus(WorkOrderStatus.PENDING.name());
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateTime(now);
        orderMapper.insert(e);

        writeLog(e, WorkOrderAction.CREATE, null, WorkOrderStatus.PENDING,
                null, cmd.orderContent() == null ? "创建工单" : cmd.orderContent());
        return WorkOrderVO.from(e);
    }

    // ==================== 查询 ====================

    @Override
    public WorkOrderVO get(Long id) {
        return WorkOrderVO.from(requireOrder(id));
    }

    @Override
    public List<OpsWorkorderLog> logs(Long id) {
        requireOrder(id);
        return logMapper.selectList(new LambdaQueryWrapper<OpsWorkorderLog>()
                .eq(OpsWorkorderLog::getWorkorderId, id)
                .orderByAsc(OpsWorkorderLog::getCreateTime)
                .orderByAsc(OpsWorkorderLog::getId));
    }

    @Override
    public PageResult<WorkOrderVO> page(long pageNum, long pageSize, String orderType,
                                        String orderStatus, Long assignUserId, String keyword) {
        LambdaQueryWrapper<OpsWorkorder> qw = new LambdaQueryWrapper<OpsWorkorder>()
                .eq(orderType != null && !orderType.isBlank(),
                        OpsWorkorder::getOrderType, orderType)
                .eq(orderStatus != null && !orderStatus.isBlank(),
                        OpsWorkorder::getOrderStatus, orderStatus)
                .eq(assignUserId != null, OpsWorkorder::getAssignUserId, assignUserId)
                .orderByDesc(OpsWorkorder::getId);
        applyDataScope(qw, OpsWorkorder::getOrgId, OpsWorkorder::getPersonId, true);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(OpsWorkorder::getOrderTitle, keyword)
                    .or().like(OpsWorkorder::getWorkorderNo, keyword));
        }
        IPage<OpsWorkorder> page = orderMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<WorkOrderVO> rows = page.getRecords().stream().map(WorkOrderVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    // ==================== 流转 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO assign(Long id, Long assignUserId, String assignUserName,
                              String assignUserPhone, String content) {
        if (assignUserId == null) {
            throw BizException.paramInvalid("处理人不能为空");
        }
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus from = statusOf(e);
        transition(e, WorkOrderStatus.ASSIGNED);

        e.setAssignUserId(assignUserId);
        e.setAssignUserName(assignUserName);
        e.setAssignUserPhone(assignUserPhone);
        e.setAssignTime(LocalDateTime.now());
        orderMapper.updateById(e);

        writeLog(e, WorkOrderAction.ASSIGN, from, WorkOrderStatus.ASSIGNED,
                assignUserName, content == null ? "派单给 " + assignUserName : content);
        return WorkOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO accept(Long id, Long operatorId, String operatorName, String content) {
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus from = statusOf(e);
        if (from != WorkOrderStatus.ASSIGNED && from != WorkOrderStatus.PENDING) {
            throw BizException.stateConflict(
                    "当前状态（" + from.label() + "）不能接单");
        }
        transition(e, WorkOrderStatus.ACCEPTED);

        LocalDateTime now = LocalDateTime.now();
        e.setAcceptTime(now);
        e.setSlaStatus(calcResponseSla(e, now));
        orderMapper.updateById(e);

        writeLog(e, WorkOrderAction.ACCEPT, from, WorkOrderStatus.ACCEPTED, operatorName,
                content == null ? "接单" : content);
        return WorkOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO start(Long id, Long operatorId, String operatorName, String content) {
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus from = statusOf(e);
        transition(e, WorkOrderStatus.PROCESSING);
        orderMapper.updateById(e);
        writeLog(e, WorkOrderAction.START, from, WorkOrderStatus.PROCESSING, operatorName,
                content == null ? "开始处理" : content);
        return WorkOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO finish(Long id, Long operatorId, String operatorName,
                              String handleResult, String content) {
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus from = statusOf(e);
        transition(e, WorkOrderStatus.FINISHED);

        LocalDateTime now = LocalDateTime.now();
        e.setFinishTime(now);
        e.setHandleResult(handleResult);
        // 完工 SLA 优先（更严重）
        String finSla = calcFinishSla(e, now);
        if (!SlaStatus.ON_TIME.name().equals(finSla) || e.getSlaStatus() == null) {
            e.setSlaStatus(finSla);
        }
        orderMapper.updateById(e);

        writeLog(e, WorkOrderAction.FINISH, from, WorkOrderStatus.FINISHED, operatorName,
                content == null ? (handleResult == null ? "完工" : handleResult) : content);
        return WorkOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO close(Long id, Long operatorId, String operatorName, String content) {
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus from = statusOf(e);
        transition(e, WorkOrderStatus.CLOSED);
        e.setCloseTime(LocalDateTime.now());
        orderMapper.updateById(e);
        writeLog(e, WorkOrderAction.CLOSE, from, WorkOrderStatus.CLOSED, operatorName,
                content == null ? "闭环" : content);
        return WorkOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO cancel(Long id, Long operatorId, String operatorName, String reason) {
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus from = statusOf(e);
        transition(e, WorkOrderStatus.CANCELLED);
        orderMapper.updateById(e);
        writeLog(e, WorkOrderAction.CANCEL, from, WorkOrderStatus.CANCELLED, operatorName,
                reason == null ? "取消" : reason);
        return WorkOrderVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public WorkOrderVO reject(Long id, Long operatorId, String operatorName, String reason) {
        OpsWorkorder e = requireOrder(id);
        WorkOrderStatus from = statusOf(e);
        transition(e, WorkOrderStatus.REJECTED);
        orderMapper.updateById(e);
        writeLog(e, WorkOrderAction.REJECT, from, WorkOrderStatus.REJECTED, operatorName,
                reason == null ? "驳回" : reason);
        return WorkOrderVO.from(e);
    }

    // ==================== 内部 ====================

    private OpsWorkorder requireOrder(Long id) {
        OpsWorkorder e = orderMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("工单");
        }
        return e;
    }

    private static WorkOrderStatus statusOf(OpsWorkorder e) {
        try {
            return WorkOrderStatus.valueOf(e.getOrderStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("工单状态非法: " + e.getOrderStatus());
        }
    }

    /** 状态机校验并写入新状态（调用方负责 updateById）。 */
    private static void transition(OpsWorkorder e, WorkOrderStatus target) {
        WorkOrderStatus from = statusOf(e);
        if (from == target) {
            throw BizException.stateConflict("工单已处于 " + target.label() + " 状态");
        }
        if (!WorkOrderStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "工单状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setOrderStatus(target.name());
    }

    private static String calcResponseSla(OpsWorkorder e, LocalDateTime acceptAt) {
        if (e.getCreateTime() == null || e.getSlaResponseMinutes() == null) {
            return SlaStatus.ON_TIME.name();
        }
        long minutes = ChronoUnit.MINUTES.between(e.getCreateTime(), acceptAt);
        return minutes > e.getSlaResponseMinutes()
                ? SlaStatus.RESPONSE_TIMEOUT.name() : SlaStatus.ON_TIME.name();
    }

    private static String calcFinishSla(OpsWorkorder e, LocalDateTime finishAt) {
        if (e.getCreateTime() == null || e.getSlaFinishMinutes() == null) {
            return SlaStatus.ON_TIME.name();
        }
        long minutes = ChronoUnit.MINUTES.between(e.getCreateTime(), finishAt);
        return minutes > e.getSlaFinishMinutes()
                ? SlaStatus.FINISH_TIMEOUT.name() : SlaStatus.ON_TIME.name();
    }

    private void writeLog(OpsWorkorder e, WorkOrderAction action, WorkOrderStatus from,
                          WorkOrderStatus to, String operatorName, String content) {
        OpsWorkorderLog lg = new OpsWorkorderLog();
        lg.setId(idGen.nextId());
        lg.setTenantId(e.getTenantId());
        lg.setWorkorderId(e.getId());
        lg.setAction(action.name());
        lg.setFromStatus(from == null ? null : from.name());
        lg.setToStatus(to == null ? null : to.name());
        lg.setOperatorName(operatorName);
        lg.setContent(content);
        lg.setCreateTime(LocalDateTime.now());
        logMapper.insert(lg);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }

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
        java.util.List<OpsWorkorder> list = orderMapper.selectList(
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
            if (u == null || !"ENABLED".equals(u.getStatus())) {
                continue;
            }
            if (orgId != null && u.getOrgId() != null && !orgId.equals(u.getOrgId())) {
                continue;
            }
            Long load = orderMapper.selectCount(
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
            // 实体不存超时标记，按 SLA 分钟数与时间戳现算
            java.time.LocalDateTime nowTs = java.time.LocalDateTime.now();
            boolean responseLate = o.getAcceptTime() == null && o.getCreateTime() != null
                    && o.getSlaResponseMinutes() != null
                    && o.getCreateTime().plusMinutes(o.getSlaResponseMinutes())
                            .isBefore(nowTs);
            boolean finishLate = o.getFinishTime() == null && o.getCreateTime() != null
                    && o.getSlaFinishMinutes() != null
                    && o.getCreateTime().plusMinutes(o.getSlaFinishMinutes())
                            .isBefore(nowTs);
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
}
