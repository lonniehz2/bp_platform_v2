# -*- coding: utf-8 -*-
"""生成 ops 告警工单模块（第 2 部分：服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['ops/service/WorkOrderService.java'] = '''package com.yundao.bp.ops.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsWorkorderLog;
import java.util.List;

/**
 * 工单服务。
 *
 * <p>状态机：PENDING → ASSIGNED → ACCEPTED → PROCESSING → FINISHED → CLOSED
 * （另有 CANCELLED / REJECTED 终态）。每次流转都写 {@code bp_ops_workorder_log}。
 */
public interface WorkOrderService {

    WorkOrderVO create(WorkOrderCreateCmd cmd);

    WorkOrderVO get(Long id);

    /** 流转记录（按时间正序）。 */
    List<OpsWorkorderLog> logs(Long id);

    PageResult<WorkOrderVO> page(long pageNum, long pageSize, String orderType,
                                 String orderStatus, Long assignUserId, String keyword);

    /** 派单。 */
    WorkOrderVO assign(Long id, Long assignUserId, String assignUserName,
                       String assignUserPhone, String content);

    /** 接单（记录响应时间，并结算响应 SLA）。 */
    WorkOrderVO accept(Long id, Long operatorId, String operatorName, String content);

    /** 开始处理。 */
    WorkOrderVO start(Long id, Long operatorId, String operatorName, String content);

    /** 完工（记录完工时间，结算完工 SLA）。 */
    WorkOrderVO finish(Long id, Long operatorId, String operatorName,
                       String handleResult, String content);

    /** 闭环（记录闭环时间；考核指标）。 */
    WorkOrderVO close(Long id, Long operatorId, String operatorName, String content);

    /** 取消。 */
    WorkOrderVO cancel(Long id, Long operatorId, String operatorName, String reason);

    /** 驳回。 */
    WorkOrderVO reject(Long id, Long operatorId, String operatorName, String reason);
}
'''

FILES['ops/service/impl/WorkOrderServiceImpl.java'] = '''package com.yundao.bp.ops.service.impl;

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
                null, "创建工单", cmd.orderContent());
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
}
'''

FILES['ops/controller/WorkOrderController.java'] = '''package com.yundao.bp.ops.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.dto.WorkOrderVO;
import com.yundao.bp.ops.entity.OpsWorkorderLog;
import com.yundao.bp.ops.service.WorkOrderService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 工单接口（BC-06 运维告警）。
 *
 * <p>完整闭环：创建 → 派单 → 接单 → 开始 → 完工 → 闭环；每步都有流转记录。
 */
@RestController
@RequestMapping("/api/v1/workorders")
public class WorkOrderController {

    private final WorkOrderService workOrderService;

    public WorkOrderController(WorkOrderService workOrderService) {
        this.workOrderService = workOrderService;
    }

    @PostMapping
    public R<WorkOrderVO> create(@Valid @RequestBody WorkOrderCreateCmd cmd) {
        return R.ok(workOrderService.create(cmd));
    }

    @GetMapping("/{id}")
    public R<WorkOrderVO> get(@PathVariable Long id) {
        return R.ok(workOrderService.get(id));
    }

    @GetMapping("/{id}/logs")
    public R<List<OpsWorkorderLog>> logs(@PathVariable Long id) {
        return R.ok(workOrderService.logs(id));
    }

    @GetMapping
    public R<PageResult<WorkOrderVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                           @RequestParam(defaultValue = "20") long pageSize,
                                           @RequestParam(required = false) String orderType,
                                           @RequestParam(required = false) String orderStatus,
                                           @RequestParam(required = false) Long assignUserId,
                                           @RequestParam(required = false) String keyword) {
        return R.ok(workOrderService.page(pageNum, pageSize, orderType, orderStatus,
                assignUserId, keyword));
    }

    @PostMapping("/{id}/assign")
    public R<WorkOrderVO> assign(@PathVariable Long id, @RequestBody AssignCmd cmd) {
        return R.ok(workOrderService.assign(id, cmd.assignUserId(), cmd.assignUserName(),
                cmd.assignUserPhone(), cmd.content()));
    }

    @PostMapping("/{id}/accept")
    public R<WorkOrderVO> accept(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.accept(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/start")
    public R<WorkOrderVO> start(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.start(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/finish")
    public R<WorkOrderVO> finish(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.finish(id, cmd.operatorId(), cmd.operatorName(),
                cmd.handleResult(), cmd.content()));
    }

    @PostMapping("/{id}/close")
    public R<WorkOrderVO> close(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.close(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/cancel")
    public R<WorkOrderVO> cancel(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.cancel(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    @PostMapping("/{id}/reject")
    public R<WorkOrderVO> reject(@PathVariable Long id, @RequestBody ActionCmd cmd) {
        return R.ok(workOrderService.reject(id, cmd.operatorId(), cmd.operatorName(),
                cmd.content()));
    }

    public record AssignCmd(Long assignUserId, String assignUserName,
                            String assignUserPhone, String content) {
    }

    public record ActionCmd(Long operatorId, String operatorName,
                            String content, String handleResult) {
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
