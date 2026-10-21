package com.yundao.bp.ops.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.ops.constant.VisitStatus;
import com.yundao.bp.ops.dto.VisitCreateCmd;
import com.yundao.bp.ops.dto.VisitResultCmd;
import com.yundao.bp.ops.dto.VisitVO;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsHouseVisit;
import com.yundao.bp.ops.mapper.OpsHouseVisitMapper;
import com.yundao.bp.ops.service.VisitService;
import com.yundao.bp.ops.service.WorkOrderService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 巡房走访实现。
 *
 * <p><b>业务价值</b>：保障房的"使用情况核查"是政策硬要求
 * （防转租转借、防长期闲置）。走访结果里的
 * {@code isSublease / isIdle / isIllegalUse} 三个标记是违规认定的直接依据，
 * 命中后应转工单处置。
 */
@Service
public class VisitServiceImpl implements VisitService {

    private static final Logger log = LoggerFactory.getLogger(VisitServiceImpl.class);

    private final OpsHouseVisitMapper mapper;
    private final WorkOrderService workOrderService;
    private final SnowflakeIdGenerator idGen;

    public VisitServiceImpl(OpsHouseVisitMapper mapper, WorkOrderService workOrderService,
                            SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.workOrderService = workOrderService;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public VisitVO create(VisitCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();

        OpsHouseVisit e = new OpsHouseVisit();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setVisitNo("V" + id);
        e.setVisitType(cmd.visitType());
        e.setOrgId(cmd.orgId());
        e.setSpaceId(cmd.spaceId());
        e.setHouseId(cmd.houseId());
        e.setPersonId(cmd.personId());
        e.setPlanDate(cmd.planDate() == null ? LocalDate.now() : cmd.planDate());
        e.setVisitUserId(cmd.visitUserId());
        e.setVisitUserName(cmd.visitUserName());
        e.setTriggerReason(cmd.triggerReason());
        e.setAlertId(cmd.alertId());
        e.setVisitStatus(VisitStatus.PENDING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return VisitVO.from(e);
    }

    @Override
    public VisitVO get(Long id) {
        return VisitVO.from(require(id));
    }

    @Override
    public PageResult<VisitVO> page(long pageNum, long pageSize, String visitType,
                                    String visitStatus, Long houseId, String keyword) {
        LambdaQueryWrapper<OpsHouseVisit> qw = new LambdaQueryWrapper<OpsHouseVisit>()
                .eq(visitType != null && !visitType.isBlank(),
                        OpsHouseVisit::getVisitType, visitType)
                .eq(visitStatus != null && !visitStatus.isBlank(),
                        OpsHouseVisit::getVisitStatus, visitStatus)
                .eq(houseId != null, OpsHouseVisit::getHouseId, houseId)
                .orderByDesc(OpsHouseVisit::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(OpsHouseVisit::getVisitNo, keyword)
                    .or().like(OpsHouseVisit::getFindings, keyword));
        }
        IPage<OpsHouseVisit> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<VisitVO> rows = page.getRecords().stream().map(VisitVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public VisitVO report(Long id, VisitResultCmd cmd) {
        OpsHouseVisit e = require(id);
        VisitStatus target;
        try {
            target = VisitStatus.valueOf(
                    cmd.visitStatus() == null || cmd.visitStatus().isBlank()
                            ? "DONE" : cmd.visitStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("走访状态不合法");
        }
        transition(e, target);

        e.setActualDate(cmd.actualDate() == null ? LocalDate.now() : cmd.actualDate());
        e.setIsOccupied(cmd.isOccupied());
        e.setActualResidents(cmd.actualResidents());
        e.setMatchResult(blankToNull(cmd.matchResult()));
        e.setFindings(cmd.findings());
        e.setIsSublease(cmd.isSublease());
        e.setIsIdle(cmd.isIdle());
        e.setIsIllegalUse(cmd.isIllegalUse());
        e.setImages(cmd.images());
        e.setLocation(cmd.location());
        e.setNextAction(cmd.nextAction());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        if (flagOf(e.getIsSublease()) || flagOf(e.getIsIdle()) || flagOf(e.getIsIllegalUse())) {
            log.warn("走访 {} 发现异常：转租={} 闲置={} 违规={}",
                    e.getVisitNo(), e.getIsSublease(), e.getIsIdle(), e.getIsIllegalUse());
        }
        return VisitVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public VisitVO toWorkOrder(Long id, Long operatorId, String operatorName) {
        OpsHouseVisit e = require(id);
        if (e.getWorkorderId() != null) {
            throw BizException.stateConflict("该走访已转工单（ID=" + e.getWorkorderId() + "）");
        }
        VisitStatus st = statusOf(e);
        if (st == VisitStatus.PENDING) {
            throw BizException.stateConflict("走访尚未完成，不能转工单");
        }
        if (st == VisitStatus.CANCELLED) {
            throw BizException.stateConflict("已取消的走访不能转工单");
        }

        String title = "【走访核查】" + e.getVisitNo();
        StringBuilder content = new StringBuilder();
        if (e.getFindings() != null) {
            content.append(e.getFindings());
        }
        if (flagOf(e.getIsSublease())) {
            content.append("；发现转租转借");
        }
        if (flagOf(e.getIsIdle())) {
            content.append("；发现长期闲置");
        }
        if (flagOf(e.getIsIllegalUse())) {
            content.append("；发现违规使用");
        }

        WorkOrderCreateCmd wo = new WorkOrderCreateCmd(
                "INSPECT", "STAFF", title,
                content.toString(), e.getOrgId(), e.getSpaceId(), e.getHouseId(),
                null, null, e.getPersonId(), null, null, null, e.getImages(),
                120, null, "来源走访：" + e.getVisitNo());
        WorkOrderVO created = workOrderService.create(wo);

        e.setWorkorderId(created.id());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("走访 {} 转工单 {}", e.getVisitNo(), created.workorderNo());
        return VisitVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public VisitVO cancel(Long id, String reason) {
        OpsHouseVisit e = require(id);
        transition(e, VisitStatus.CANCELLED);
        e.setNextAction(reason);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return VisitVO.from(e);
    }

    private OpsHouseVisit require(Long id) {
        OpsHouseVisit e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("走访任务");
        }
        return e;
    }

    private static VisitStatus statusOf(OpsHouseVisit e) {
        try {
            return VisitStatus.valueOf(e.getVisitStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("走访状态非法: " + e.getVisitStatus());
        }
    }

    private static void transition(OpsHouseVisit e, VisitStatus target) {
        VisitStatus from = statusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!VisitStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setVisitStatus(target.name());
    }

    private static boolean flagOf(Integer v) {
        return v != null && v == 1;
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
