# -*- coding: utf-8 -*-
"""生成 complaint + house_visit（第 2 部分：服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

# ==================== 投诉建议服务 ====================
FILES['ops/service/ComplaintService.java'] = '''package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.ComplaintCreateCmd;
import com.yundao.bp.ops.dto.ComplaintVO;

/**
 * 投诉建议服务。
 */
public interface ComplaintService {

    ComplaintVO create(ComplaintCreateCmd cmd);

    ComplaintVO get(Long id);

    PageResult<ComplaintVO> page(long pageNum, long pageSize, String type, String status,
                                 Long orgId, String keyword);

    /** 开始处理：PENDING → HANDLING。 */
    ComplaintVO handle(Long id, Long handleUserId);

    /** 处理完成：→ HANDLED。 */
    ComplaintVO resolve(Long id, Long handleUserId, String result);

    /** 归档：HANDLED → CLOSED。 */
    ComplaintVO close(Long id, Long handleUserId);

    /** 回访评价（满意度 1-5）。 */
    ComplaintVO evaluate(Long id, Integer satisfaction);

    /** 转工单（投诉升级为维修/处置工单）。 */
    ComplaintVO toWorkOrder(Long id, Long operatorId, String operatorName);
}
'''

FILES['ops/service/impl/ComplaintServiceImpl.java'] = '''package com.yundao.bp.ops.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.ops.constant.ComplaintStatus;
import com.yundao.bp.ops.dto.ComplaintCreateCmd;
import com.yundao.bp.ops.dto.ComplaintVO;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsComplaint;
import com.yundao.bp.ops.mapper.OpsComplaintMapper;
import com.yundao.bp.ops.service.ComplaintService;
import com.yundao.bp.ops.service.WorkOrderService;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 投诉建议实现。
 *
 * <p>投诉类默认 48 小时未处理视为超时（VO 派生 {@code overdue}）。
 */
@Service
public class ComplaintServiceImpl implements ComplaintService {

    private static final Logger log = LoggerFactory.getLogger(ComplaintServiceImpl.class);

    private final OpsComplaintMapper mapper;
    private final WorkOrderService workOrderService;
    private final SnowflakeIdGenerator idGen;

    public ComplaintServiceImpl(OpsComplaintMapper mapper, WorkOrderService workOrderService,
                                SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.workOrderService = workOrderService;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO create(ComplaintCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();

        OpsComplaint e = new OpsComplaint();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setComplaintNo("C" + id);
        e.setComplaintType(cmd.complaintType());
        e.setSource(blankToNull(cmd.source()) == null ? "OTHER" : cmd.source());
        e.setOrgId(cmd.orgId());
        e.setPersonId(cmd.personId());
        e.setSubmitterName(cmd.submitterName());
        e.setSubmitterPhone(cmd.submitterPhone());
        e.setTitle(cmd.title());
        e.setContent(cmd.content());
        e.setImages(cmd.images());
        e.setHandleStatus(ComplaintStatus.PENDING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return ComplaintVO.from(e);
    }

    @Override
    public ComplaintVO get(Long id) {
        return ComplaintVO.from(require(id));
    }

    @Override
    public PageResult<ComplaintVO> page(long pageNum, long pageSize, String type, String status,
                                        Long orgId, String keyword) {
        LambdaQueryWrapper<OpsComplaint> qw = new LambdaQueryWrapper<OpsComplaint>()
                .eq(type != null && !type.isBlank(), OpsComplaint::getComplaintType, type)
                .eq(status != null && !status.isBlank(), OpsComplaint::getHandleStatus, status)
                .eq(orgId != null, OpsComplaint::getOrgId, orgId)
                .orderByDesc(OpsComplaint::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.and(w -> w.like(OpsComplaint::getTitle, keyword)
                    .or().like(OpsComplaint::getComplaintNo, keyword));
        }
        IPage<OpsComplaint> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ComplaintVO> rows = page.getRecords().stream().map(ComplaintVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO handle(Long id, Long handleUserId) {
        OpsComplaint e = require(id);
        transition(e, ComplaintStatus.HANDLING);
        e.setHandleUserId(handleUserId);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO resolve(Long id, Long handleUserId, String result) {
        OpsComplaint e = require(id);
        transition(e, ComplaintStatus.HANDLED);
        e.setHandleUserId(handleUserId);
        e.setHandleResult(result);
        e.setHandleTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO close(Long id, Long handleUserId) {
        OpsComplaint e = require(id);
        transition(e, ComplaintStatus.CLOSED);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO evaluate(Long id, Integer satisfaction) {
        if (satisfaction == null || satisfaction < 1 || satisfaction > 5) {
            throw BizException.paramInvalid("满意度必须是 1-5");
        }
        OpsComplaint e = require(id);
        if (ComplaintStatus.PENDING.name().equals(e.getHandleStatus())) {
            throw BizException.stateConflict("尚未处理，不能评价");
        }
        e.setSatisfaction(satisfaction);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ComplaintVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ComplaintVO toWorkOrder(Long id, Long operatorId, String operatorName) {
        OpsComplaint e = require(id);
        if (e.getWorkorderId() != null) {
            throw BizException.stateConflict("该投诉已转工单（ID=" + e.getWorkorderId() + "）");
        }
        if (ComplaintStatus.CLOSED.name().equals(e.getHandleStatus())) {
            throw BizException.stateConflict("已归档的投诉不能转工单");
        }
        if (ComplaintStatus.PENDING.name().equals(e.getHandleStatus())) {
            transition(e, ComplaintStatus.HANDLING);
        }

        WorkOrderCreateCmd wo = new WorkOrderCreateCmd(
                "COMPLAINT", "STAFF",
                e.getTitle() == null ? "投诉处置" : "【投诉处置】" + e.getTitle(),
                e.getContent(), e.getOrgId(), null, null, null, null, e.getPersonId(),
                e.getSubmitterName(), e.getSubmitterPhone(), null, e.getImages(),
                60, null, "来源投诉：" + e.getComplaintNo());
        WorkOrderVO created = workOrderService.create(wo);

        e.setWorkorderId(created.id());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("投诉 {} 转工单 {}", e.getComplaintNo(), created.workorderNo());
        return ComplaintVO.from(e);
    }

    private OpsComplaint require(Long id) {
        OpsComplaint e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("投诉建议");
        }
        return e;
    }

    private static void transition(OpsComplaint e, ComplaintStatus target) {
        ComplaintStatus from;
        try {
            from = ComplaintStatus.valueOf(e.getHandleStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("投诉状态非法: " + e.getHandleStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ComplaintStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setHandleStatus(target.name());
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
'''

# ==================== 巡房走访服务 ====================
FILES['ops/service/VisitService.java'] = '''package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.VisitCreateCmd;
import com.yundao.bp.ops.dto.VisitResultCmd;
import com.yundao.bp.ops.dto.VisitVO;

/**
 * 巡房/入户走访服务。
 */
public interface VisitService {

    VisitVO create(VisitCreateCmd cmd);

    VisitVO get(Long id);

    PageResult<VisitVO> page(long pageNum, long pageSize, String visitType, String visitStatus,
                             Long houseId, String keyword);

    /** 回填走访结果（PENDING → DONE/REFUSED/ABSENT/CANCELLED）。 */
    VisitVO report(Long id, VisitResultCmd cmd);

    /**
     * 走访异常转工单：发现转租/闲置/违规时生成处置工单。
     */
    VisitVO toWorkOrder(Long id, Long operatorId, String operatorName);

    /** 取消走访任务。 */
    VisitVO cancel(Long id, String reason);
}
'''

FILES['ops/service/impl/VisitServiceImpl.java'] = '''package com.yundao.bp.ops.service.impl;

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
'''

# ==================== 控制器 ====================
FILES['ops/controller/ComplaintController.java'] = '''package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.dto.ComplaintCreateCmd;
import com.yundao.bp.ops.dto.ComplaintVO;
import com.yundao.bp.ops.service.ComplaintService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 投诉建议接口（BC-06）。
 */
@RestController
@RequestMapping("/api/v1/complaints")
public class ComplaintController {

    private final ComplaintService complaintService;

    public ComplaintController(ComplaintService complaintService) {
        this.complaintService = complaintService;
    }

    @PostMapping
    public R<ComplaintVO> create(@Valid @RequestBody ComplaintCreateCmd cmd) {
        return R.ok(complaintService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<ComplaintVO> get(@PathVariable Long id) {
        return R.ok(complaintService.get(id));
    }

    @GetMapping
    public R<PageResult<ComplaintVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                           @RequestParam(defaultValue = "20") long pageSize,
                                           @RequestParam(required = false) String type,
                                           @RequestParam(required = false) String status,
                                           @RequestParam(required = false) Long orgId,
                                           @RequestParam(required = false) String keyword) {
        return R.ok(complaintService.page(pageNum, pageSize, type, status, orgId, keyword));
    }

    @PostMapping("/{id}/handle")
    public R<ComplaintVO> handle(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.handle(id, cmd == null ? null : cmd.handleUserId()));
    }

    @PostMapping("/{id}/resolve")
    public R<ComplaintVO> resolve(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.resolve(id,
                cmd == null ? null : cmd.handleUserId(),
                cmd == null ? null : cmd.result()));
    }

    @PostMapping("/{id}/close")
    public R<ComplaintVO> close(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.close(id, cmd == null ? null : cmd.handleUserId()));
    }

    @PostMapping("/{id}/evaluate")
    public R<ComplaintVO> evaluate(@PathVariable Long id, @RequestBody EvalCmd cmd) {
        return R.ok(complaintService.evaluate(id, cmd.satisfaction()));
    }

    @PostMapping("/{id}/to-workorder")
    public R<ComplaintVO> toWorkOrder(@PathVariable Long id,
                                      @RequestBody(required = false) Cmd cmd) {
        return R.ok(complaintService.toWorkOrder(id,
                cmd == null ? null : cmd.handleUserId(),
                cmd == null ? null : cmd.action()));
    }

    public record Cmd(Long handleUserId, String action, String result) {
    }

    public record EvalCmd(Integer satisfaction) {
    }
}
'''

FILES['ops/controller/VisitController.java'] = '''package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.dto.VisitCreateCmd;
import com.yundao.bp.ops.dto.VisitResultCmd;
import com.yundao.bp.ops.dto.VisitVO;
import com.yundao.bp.ops.service.VisitService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 巡房/入户走访接口（BC-06）。
 *
 * <p>保障房"使用情况核查"的落地手段：走访回填 {@code isSublease/isIdle/isIllegalUse}
 * 三个标记，命中后转工单处置。
 */
@RestController
@RequestMapping("/api/v1/visits")
public class VisitController {

    private final VisitService visitService;

    public VisitController(VisitService visitService) {
        this.visitService = visitService;
    }

    @PostMapping
    public R<VisitVO> create(@Valid @RequestBody VisitCreateCmd cmd) {
        return R.ok(visitService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<VisitVO> get(@PathVariable Long id) {
        return R.ok(visitService.get(id));
    }

    @GetMapping
    public R<PageResult<VisitVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                       @RequestParam(defaultValue = "20") long pageSize,
                                       @RequestParam(required = false) String visitType,
                                       @RequestParam(required = false) String visitStatus,
                                       @RequestParam(required = false) Long houseId,
                                       @RequestParam(required = false) String keyword) {
        return R.ok(visitService.page(pageNum, pageSize, visitType, visitStatus, houseId, keyword));
    }

    /** 回填走访结果。 */
    @PostMapping("/{id}/report")
    public R<VisitVO> report(@PathVariable Long id, @Valid @RequestBody VisitResultCmd cmd) {
        return R.ok(visitService.report(id, cmd));
    }

    /** 走访异常转工单。 */
    @PostMapping("/{id}/to-workorder")
    public R<VisitVO> toWorkOrder(@PathVariable Long id,
                                  @RequestBody(required = false) Cmd cmd) {
        return R.ok(visitService.toWorkOrder(id,
                cmd == null ? null : cmd.operatorId(),
                cmd == null ? null : cmd.operatorName()));
    }

    @PostMapping("/{id}/cancel")
    public R<VisitVO> cancel(@PathVariable Long id, @RequestBody(required = false) Cmd cmd) {
        return R.ok(visitService.cancel(id, cmd == null ? null : cmd.reason()));
    }

    public record Cmd(Long operatorId, String operatorName, String reason) {
    }
}
'''

count = 0
for rel, content in FILES.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
    print('  + ' + rel)
print('生成 %d 个文件' % count)
