package com.yundao.bp.ops.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.ops.dto.InspectionPlanCmd;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.entity.OpsInspectionPlan;
import com.yundao.bp.ops.mapper.OpsInspectionPlanMapper;
import com.yundao.bp.ops.service.InspectionPlanService;
import com.yundao.bp.ops.service.WorkOrderService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 巡检计划实现：按周期生成工单。 */
@Service
public class InspectionPlanServiceImpl implements InspectionPlanService {
    /** 数据范围服务 */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按组织/人员列限权；personCol 为 null 表示仅组织维度。 */
    private <T> void applyScope(
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
        if ("ORG_SUB".equals(scope.level()) && scope.orgIds() != null
                && !scope.orgIds().isEmpty() && orgCol != null) {
            qw.in(orgCol, scope.orgIds());
            return;
        }
        if (scope.orgId() != null && orgCol != null) {
            qw.eq(orgCol, scope.orgId());
        }
    }


    private static final Logger log = LoggerFactory.getLogger(InspectionPlanServiceImpl.class);

    private final OpsInspectionPlanMapper mapper;
    private final SnowflakeIdGenerator idGen;
    private final WorkOrderService workOrderService;

    public InspectionPlanServiceImpl(OpsInspectionPlanMapper mapper, SnowflakeIdGenerator idGen,
                                     WorkOrderService workOrderService) {
        this.mapper = mapper;
        this.idGen = idGen;
        this.workOrderService = workOrderService;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public OpsInspectionPlan create(InspectionPlanCmd cmd) {
        if (cmd.planName() == null || cmd.planName().isBlank()) {
            throw BizException.paramInvalid("计划名称不能为空");
        }
        OpsInspectionPlan p = new OpsInspectionPlan();
        p.setId(idGen.nextId());
        p.setTenantId(TenantContext.tenantId());
        p.setOrgId(cmd.orgId());
        p.setSpaceId(cmd.spaceId());
        p.setPlanName(cmd.planName());
        p.setInspectType(cmd.inspectType() == null ? "SAFETY" : cmd.inspectType());
        p.setFrequency(cmd.frequency() == null ? "WEEK" : cmd.frequency());
        p.setNextRunDate(cmd.nextRunDate() == null ? LocalDate.now() : cmd.nextRunDate());
        p.setAssignUserId(cmd.assignUserId());
        p.setAssignUserName(cmd.assignUserName());
        p.setPlanStatus("ENABLED");
        p.setRemark(cmd.remark());
        p.setIsDeleted(0);
        p.setCreateTime(LocalDateTime.now());
        mapper.insert(p);
        return p;
    }

    @Override
    public PageResult<OpsInspectionPlan> page(long pageNum, long pageSize, String planStatus) {
        LambdaQueryWrapper<OpsInspectionPlan> qw = new LambdaQueryWrapper<OpsInspectionPlan>()
                .eq(planStatus != null && !planStatus.isBlank(),
                        OpsInspectionPlan::getPlanStatus, planStatus)
                .orderByAsc(OpsInspectionPlan::getNextRunDate);
        applyScope(qw, OpsInspectionPlan::getOrgId, null);
        var page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> runDue() {
        LocalDate today = LocalDate.now();
        List<OpsInspectionPlan> due = mapper.selectList(
                new LambdaQueryWrapper<OpsInspectionPlan>()
                        .eq(OpsInspectionPlan::getPlanStatus, "ENABLED")
                        .le(OpsInspectionPlan::getNextRunDate, today));
        int generated = 0;
        int skipped = 0;
        for (OpsInspectionPlan p : due) {
            try {
                WorkOrderCreateCmd cmd = new WorkOrderCreateCmd(
                        "INSPECT", "STAFF",
                        "巡检任务：" + p.getPlanName(),
                        "巡检类型 " + p.getInspectType() + "，周期 " + p.getFrequency(),
                        p.getOrgId(), p.getSpaceId(), null, null, null,
                        p.getAssignUserId(), p.getAssignUserName(), null, null, null,
                        null, null,
                        "由巡检计划生成");
                workOrderService.create(cmd);
                p.setNextRunDate(advance(p.getNextRunDate(), p.getFrequency()));
                p.setUpdateTime(LocalDateTime.now());
                mapper.updateById(p);
                generated++;
            } catch (Exception ex) {
                log.warn("巡检计划 {} 生成工单失败：{}", p.getId(), ex.getMessage());
                skipped++;
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("due", due.size());
        out.put("generated", generated);
        out.put("skipped", skipped);
        return out;
    }

    /** 推进下次执行日。 */
    private LocalDate advance(LocalDate base, String frequency) {
        String f = frequency == null ? "WEEK" : frequency;
        LocalDate next = switch (f) {
            case "DAY" -> base.plusDays(1);
            case "MONTH" -> base.plusMonths(1);
            default -> base.plusWeeks(1);
        };
        LocalDate today = LocalDate.now();
        while (!next.isAfter(today)) {
            next = advance(next, f);
        }
        return next;
    }
}
