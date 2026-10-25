package com.yundao.bp.ops.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.ops.constant.AlertCategory;
import com.yundao.bp.ops.constant.AlertLevel;
import com.yundao.bp.ops.constant.AlertStatus;
import com.yundao.bp.ops.dto.AlertCreateCmd;
import com.yundao.bp.ops.dto.AlertStatsVO;
import com.yundao.bp.ops.dto.AlertVO;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsAlert;
import com.yundao.bp.ops.mapper.OpsAlertMapper;
import com.yundao.bp.ops.service.AlertService;
import com.yundao.bp.ops.service.WorkOrderService;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 告警中心实现。
 *
 * <p><b>告警 → 工单</b>：{@link #toWorkOrder} 会创建 {@code ALERT} 类型工单
 * （默认 SLA 15/120 分钟，比其他类型更紧急），并把 {@code workorder_id} 回写到告警，
 * 告警状态转为 {@code HANDLING}，形成"告警驱动处置"的闭环。
 */
@Service
public class AlertServiceImpl implements AlertService {
    /** 数据范围服务（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按组织或人员列限权；personCol 传 null 表示该实体只有组织维度。 */
    private <T> void applyDataScope(
            com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<T> qw,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> orgCol,
            com.baomidou.mybatisplus.core.toolkit.support.SFunction<T, ?> personCol) {
        if (dataScopeService == null) {
            return;
        }
        com.yundao.bp.iam.datascope.DataScope scope = dataScopeService.current();
        if (scope.isAll()) {
            return;
        }
        if (scope.isSelf() && personCol != null) {
            qw.eq(personCol, scope.personId() == null ? -1L : scope.personId());
            return;
        }
        if (scope.isSelf()) {
            // 无人员列：仅本人不可见，退化为按组织
            if (scope.orgId() != null && orgCol != null) {
                qw.eq(orgCol, scope.orgId());
            } else {
                qw.apply("1 = 0");
            }
            return;
        }
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty() && orgCol != null) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null && orgCol != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }


    private static final Logger log = LoggerFactory.getLogger(AlertServiceImpl.class);

    private final OpsAlertMapper alertMapper;
    private final WorkOrderService workOrderService;
    private final SnowflakeIdGenerator idGen;

    public AlertServiceImpl(OpsAlertMapper alertMapper, WorkOrderService workOrderService,
                            SnowflakeIdGenerator idGen) {
        this.alertMapper = alertMapper;
        this.workOrderService = workOrderService;
        this.idGen = idGen;
    }

    // ==================== 创建 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AlertVO create(AlertCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();

        OpsAlert e = new OpsAlert();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setAlertNo("A" + id);
        e.setAlertCategory(cmd.alertCategory());
        e.setAlertType(cmd.alertType());
        e.setAlertLevel(cmd.alertLevel());
        e.setAlertTitle(cmd.alertTitle());
        e.setAlertContent(cmd.alertContent());
        e.setAlertValue(cmd.alertValue());
        e.setThresholdValue(cmd.thresholdValue());
        e.setRuleId(cmd.ruleId());
        e.setRuleCode(cmd.ruleCode());
        e.setOrgId(cmd.orgId());
        e.setSpaceId(cmd.spaceId());
        e.setHouseId(cmd.houseId());
        e.setPersonId(cmd.personId());
        e.setDeviceId(cmd.deviceId());
        e.setContractId(cmd.contractId());
        e.setRelatedIds(cmd.relatedIds());
        e.setAlertStatus(AlertStatus.PENDING.name());
        e.setAlertTime(now);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        alertMapper.insert(e);

        if (AlertLevel.URGENT.name().equals(cmd.alertLevel())) {
            log.warn("【紧急告警】{} - {}（需立即处置）", e.getAlertNo(), e.getAlertTitle());
        }
        return AlertVO.from(e);
    }

    // ==================== 查询 ====================

    @Override
    public AlertVO get(Long id) {
        return AlertVO.from(require(id));
    }

    @Override
    public PageResult<AlertVO> page(long pageNum, long pageSize, String category, String level,
                                    String status, Long orgId, String keyword) {
        LambdaQueryWrapper<OpsAlert> qw = new LambdaQueryWrapper<OpsAlert>()
                .eq(category != null && !category.isBlank(), OpsAlert::getAlertCategory, category)
                .eq(level != null && !level.isBlank(), OpsAlert::getAlertLevel, level)
                .eq(status != null && !status.isBlank(), OpsAlert::getAlertStatus, status)
                .eq(orgId != null, OpsAlert::getOrgId, orgId)
                .orderByDesc(OpsAlert::getAlertTime)
                .orderByDesc(OpsAlert::getId);
        applyDataScope(qw, OpsAlert::getOrgId, OpsAlert::getPersonId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(OpsAlert::getAlertTitle, keyword)
                    .or().like(OpsAlert::getAlertNo, keyword));
        }
        IPage<OpsAlert> page = alertMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<AlertVO> rows = page.getRecords().stream().map(AlertVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    // ==================== 处置 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AlertVO handle(Long id, Long handleUserId, String action, String result) {
        OpsAlert e = require(id);
        transition(e, AlertStatus.HANDLING);
        // 未显式传入处理人时，记录当前登录用户
        e.setHandleUserId(handleUserId != null ? handleUserId
                : com.yundao.bp.common.tenant.TenantContext.userId());
        e.setHandleAction(action);
        e.setUpdateTime(LocalDateTime.now());
        alertMapper.updateById(e);
        return AlertVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AlertVO resolve(Long id, Long handleUserId, String result) {
        OpsAlert e = require(id);
        transition(e, AlertStatus.HANDLED);
        e.setHandleUserId(handleUserId != null ? handleUserId
                : com.yundao.bp.common.tenant.TenantContext.userId());
        e.setHandleUserId(handleUserId);
        e.setHandleResult(result);
        e.setHandleTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        alertMapper.updateById(e);
        return AlertVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AlertVO ignore(Long id, Long handleUserId, String reason) {
        OpsAlert e = require(id);
        transition(e, AlertStatus.IGNORED);
        e.setHandleUserId(handleUserId != null ? handleUserId
                : com.yundao.bp.common.tenant.TenantContext.userId());
        e.setHandleUserId(handleUserId);
        e.setHandleResult(reason == null ? "误报忽略" : reason);
        e.setHandleTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        alertMapper.updateById(e);
        return AlertVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AlertVO escalate(Long id, String reason) {
        OpsAlert e = require(id);
        transition(e, AlertStatus.ESCALATED);
        e.setEscalateTime(LocalDateTime.now());
        e.setHandleResult(reason);
        e.setUpdateTime(LocalDateTime.now());
        alertMapper.updateById(e);
        log.warn("告警升级 {} - {}", e.getAlertNo(), reason);
        return AlertVO.from(e);
    }

    // ==================== 告警转工单 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AlertVO toWorkOrder(Long id, Long operatorId, String operatorName) {
        OpsAlert e = require(id);
        if (e.getWorkorderId() != null) {
            throw BizException.stateConflict("该告警已转工单（ID=" + e.getWorkorderId() + "），请勿重复操作");
        }
        AlertStatus cur = statusOf(e);
        if (cur.isTerminal()) {
            throw BizException.stateConflict("告警已" + cur.label() + "，不能再转工单");
        }

        // 已升级的告警转工单视为开始处置
        if (cur != AlertStatus.HANDLING) {
            transition(e, AlertStatus.HANDLING);
        }

        // 告警级别 → 工单 SLA：紧急 15 分钟响应，重要/一般 30 分钟
        int responseMinutes = AlertLevel.URGENT.name().equals(e.getAlertLevel()) ? 15 : 30;

        WorkOrderCreateCmd wo = new WorkOrderCreateCmd(
                "ALERT", "ALERT",
                e.getAlertTitle() == null ? "告警处置" : "【告警处置】" + e.getAlertTitle(),
                e.getAlertContent(),
                e.getOrgId(), e.getSpaceId(), e.getHouseId(),
                e.getDeviceId(), null, e.getPersonId(),
                null, null, null, null,
                responseMinutes, null,
                "来源告警：" + e.getAlertNo());
        WorkOrderVO created = workOrderService.create(wo);

        e.setWorkorderId(created.id());
        e.setHandleAction("转工单 " + created.workorderNo());
        e.setUpdateTime(LocalDateTime.now());
        alertMapper.updateById(e);

        log.info("告警 {} 转工单 {}", e.getAlertNo(), created.workorderNo());
        return AlertVO.from(e);
    }

    // ==================== 统计 ====================

    @Override
    public AlertStatsVO stats(Long orgId) {
        long total = count(orgId, null);
        long pending = count(orgId, AlertStatus.PENDING) + count(orgId, AlertStatus.ESCALATED);
        long handling = count(orgId, AlertStatus.HANDLING);
        long handled = count(orgId, AlertStatus.HANDLED);
        long ignored = count(orgId, AlertStatus.IGNORED);

        Map<String, Long> byLevel = new LinkedHashMap<>();
        for (AlertLevel l : AlertLevel.values()) {
            byLevel.put(l.name(), countLevel(orgId, l.name()));
        }
        Map<String, Long> byCategory = new LinkedHashMap<>();
        for (AlertCategory c : AlertCategory.values()) {
            byCategory.put(c.name(), countCategory(orgId, c.name()));
        }
        long urgentOpen = alertMapper.selectCount(new LambdaQueryWrapper<OpsAlert>()
                .eq(orgId != null, OpsAlert::getOrgId, orgId)
                .eq(OpsAlert::getAlertLevel, AlertLevel.URGENT.name())
                .in(OpsAlert::getAlertStatus,
                        List.of(AlertStatus.PENDING.name(), AlertStatus.HANDLING.name(),
                                AlertStatus.ESCALATED.name())));

        return new AlertStatsVO(total, pending, handling, handled, ignored,
                byLevel, byCategory, urgentOpen);
    }

    private long count(Long orgId, AlertStatus status) {
        return alertMapper.selectCount(new LambdaQueryWrapper<OpsAlert>()
                .eq(orgId != null, OpsAlert::getOrgId, orgId)
                .eq(status != null, OpsAlert::getAlertStatus,
                        status == null ? null : status.name()));
    }

    private long countLevel(Long orgId, String level) {
        return alertMapper.selectCount(new LambdaQueryWrapper<OpsAlert>()
                .eq(orgId != null, OpsAlert::getOrgId, orgId)
                .eq(OpsAlert::getAlertLevel, level));
    }

    private long countCategory(Long orgId, String cat) {
        return alertMapper.selectCount(new LambdaQueryWrapper<OpsAlert>()
                .eq(orgId != null, OpsAlert::getOrgId, orgId)
                .eq(OpsAlert::getAlertCategory, cat));
    }

    // ==================== 内部 ====================

    private OpsAlert require(Long id) {
        OpsAlert e = alertMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("告警");
        }
        return e;
    }

    private static AlertStatus statusOf(OpsAlert e) {
        try {
            return AlertStatus.valueOf(e.getAlertStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("告警状态非法: " + e.getAlertStatus());
        }
    }

    private static void transition(OpsAlert e, AlertStatus target) {
        AlertStatus from = statusOf(e);
        if (from == target) {
            throw BizException.stateConflict("告警已处于 " + target.label() + " 状态");
        }
        if (!AlertStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "告警状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setAlertStatus(target.name());
    }
}
