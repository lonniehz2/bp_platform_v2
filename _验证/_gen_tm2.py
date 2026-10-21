# -*- coding: utf-8 -*-
"""生成 biz 退租腾退模块（服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['biz/service/TerminationService.java'] = '''package com.yundao.bp.biz.service;

import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.common.api.PageResult;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 退租/腾退服务。
 *
 * <p>流程：申请 → 审批 → 批准 →（验房 → 结算 → 释放房源 → 回收授权）→ 办结。
 *
 * <p><b>政策口径</b>：
 * <ul>
 *   <li>重庆：腾退给 3 个月过渡期，期内租金 1.5 倍、期满 2.0 倍</li>
 *   <li>成都：搬迁期不超过 6 个月，承租人可指定物品处置人</li>
 *   <li>违规清退：需登记限制再申请结束日（如 5 年内不得再申请）</li>
 * </ul>
 */
public interface TerminationService {

    /** 申请退租（自动按类型带出过渡期/搬迁期政策参数）。 */
    TerminationVO apply(TerminationCreateCmd cmd);

    TerminationVO get(Long id);

    PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                   Long contractId, Long houseId, String keyword);

    /** 提交审批：APPLYING → APPROVING。 */
    TerminationVO submit(Long id);

    /** 审批通过：APPROVING → APPROVED。 */
    TerminationVO approve(Long id, String opinion);

    /** 驳回：APPROVING → REJECTED。 */
    TerminationVO reject(Long id, String reason);

    /** 撤单：APPLYING → CANCELLED。 */
    TerminationVO cancel(Long id, String reason);

    /** 验房：记录验房结果与损坏赔偿（不合格时需重新验）。 */
    TerminationVO inspect(Long id, String inspectStatus, String inspectResult,
                          BigDecimal damageAmount, String inspectImages);

    /** 结算：押金/欠费/损坏 → 结算金额。 */
    TerminationVO settle(Long id, BigDecimal depositRefund, BigDecimal arrearsAmount);

    /** 标记房源已释放 / 授权已回收（供 house/grant 模块回调）。 */
    TerminationVO markReleased(Long id, Boolean houseReleased, Boolean grantRevoked);

    /** 办结：COMPLETED（要求四个前置齐备）。 */
    TerminationVO complete(Long id, LocalDate actualExitDate);

    /** 登记强制执行 / 公证 / 物品处置人。 */
    TerminationVO registerEnforce(Long id, LocalDate applyDate, String court,
                                 String itemHandlerName, String itemHandlerPhone,
                                 String notaryNo);
}
'''

FILES['biz/service/impl/TerminationServiceImpl.java'] = '''package com.yundao.bp.biz.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.constant.SettleStatus;
import com.yundao.bp.biz.constant.TerminationStatus;
import com.yundao.bp.biz.constant.TerminationType;
import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.biz.entity.BizTermination;
import com.yundao.bp.biz.mapper.BizTerminationMapper;
import com.yundao.bp.biz.service.TerminationService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 退租/腾退实现。
 */
@Service
public class TerminationServiceImpl implements TerminationService {

    private static final Logger log = LoggerFactory.getLogger(TerminationServiceImpl.class);

    /** 重庆：腾退过渡期默认 3 个月 */
    private static final int DEFAULT_TRANSITION_MONTHS = 3;
    /** 重庆：过渡期内租金倍率 1.5 */
    private static final BigDecimal DEFAULT_TRANSITION_MULTIPLIER = new BigDecimal("1.5");
    /** 成都：搬迁期上限 6 个月 */
    private static final int MAX_RELOCATION_MONTHS = 6;
    /** 违规清退：5 年内不得再申请 */
    private static final int EXPEL_BAN_YEARS = 5;

    private final BizTerminationMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public TerminationServiceImpl(BizTerminationMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO apply(TerminationCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        TerminationType type;
        try {
            type = TerminationType.valueOf(cmd.terminationType());
        } catch (IllegalArgumentException ex) {
            throw BizException.paramInvalid("退租类型不合法");
        }

        if (cmd.relocationMonths() != null && cmd.relocationMonths() > MAX_RELOCATION_MONTHS) {
            throw BizException.paramInvalid(
                    "搬迁期不能超过 " + MAX_RELOCATION_MONTHS + " 个月（成都政策）");
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        LocalDate today = LocalDate.now();

        BizTermination e = new BizTermination();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setTerminationNo("BT" + id);
        e.setContractId(cmd.contractId());
        e.setHouseId(cmd.houseId());
        e.setPersonId(cmd.personId());
        e.setTerminationType(type.name());
        e.setApplyTime(now);
        e.setPlanExitDate(cmd.planExitDate() == null ? today.plusMonths(1) : cmd.planExitDate());
        e.setExitReason(cmd.exitReason());
        e.setInspectStatus("PENDING");
        e.setDamageAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setSettleAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setDepositRefund(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setArrearsAmount(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        e.setSettleStatus(SettleStatus.PENDING.name());
        e.setTerminationStatus(TerminationStatus.APPLYING.name());
        e.setHouseReleased(0);
        e.setGrantRevoked(0);
        e.setEnforceFlag(0);
        e.setNotaryFlag(0);

        // 重庆：腾退过渡期（仅腾退类给过渡期）
        if (type == TerminationType.EXPEL || type == TerminationType.NORMAL) {
            int months = cmd.transitionMonths() == null
                    ? DEFAULT_TRANSITION_MONTHS : cmd.transitionMonths();
            e.setTransitionStartDate(e.getPlanExitDate());
            e.setTransitionEndDate(e.getPlanExitDate().plusMonths(months));
            e.setTransitionMonths(months);
            e.setTransitionRentMultiplier(cmd.transitionRentMultiplier() == null
                    ? DEFAULT_TRANSITION_MULTIPLIER : cmd.transitionRentMultiplier());
        }
        // 成都：搬迁期
        if (cmd.relocationMonths() != null && cmd.relocationMonths() > 0) {
            e.setRelocationStartDate(e.getPlanExitDate());
            e.setRelocationEndDate(e.getPlanExitDate().plusMonths(cmd.relocationMonths()));
        }
        // 违规清退：限制再申请
        if (type == TerminationType.EXPEL) {
            e.setBanReapplyEndDate(today.plusYears(EXPEL_BAN_YEARS));
        }

        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return TerminationVO.from(e);
    }

    @Override
    public TerminationVO get(Long id) {
        return TerminationVO.from(require(id));
    }

    @Override
    public PageResult<TerminationVO> page(long pageNum, long pageSize, String type, String status,
                                          Long contractId, Long houseId, String keyword) {
        LambdaQueryWrapper<BizTermination> qw = new LambdaQueryWrapper<BizTermination>()
                .eq(type != null && !type.isBlank(), BizTermination::getTerminationType, type)
                .eq(status != null && !status.isBlank(),
                        BizTermination::getTerminationStatus, status)
                .eq(contractId != null, BizTermination::getContractId, contractId)
                .eq(houseId != null, BizTermination::getHouseId, houseId)
                .orderByDesc(BizTermination::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.like(BizTermination::getTerminationNo, keyword);
        }
        IPage<BizTermination> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<TerminationVO> rows = page.getRecords().stream().map(TerminationVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO submit(Long id) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.APPROVING);
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO approve(Long id, String opinion) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.APPROVED);
        e.setExitReason(e.getExitReason() == null ? opinion : e.getExitReason());
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO reject(Long id, String reason) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.REJECTED);
        e.setExitReason(reason);
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO cancel(Long id, String reason) {
        BizTermination e = require(id);
        transition(e, TerminationStatus.CANCELLED);
        e.setExitReason(reason);
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO inspect(Long id, String inspectStatus, String inspectResult,
                                 BigDecimal damageAmount, String inspectImages) {
        BizTermination e = require(id);
        if (!(TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())
                || TerminationStatus.APPROVING.name().equals(e.getTerminationStatus()))) {
            throw BizException.stateConflict("仅在审批中/已批准状态可验房");
        }
        if (!List.of("PENDING", "PASSED", "ABNORMAL").contains(inspectStatus)) {
            throw BizException.paramInvalid("验房状态不合法: " + inspectStatus);
        }
        e.setInspectStatus(inspectStatus);
        e.setInspectResult(inspectResult);
        e.setInspectImages(inspectImages);
        if (damageAmount != null) {
            if (damageAmount.compareTo(BigDecimal.ZERO) < 0) {
                throw BizException.paramInvalid("损坏赔偿金额不能为负");
            }
            e.setDamageAmount(damageAmount.setScale(2, RoundingMode.HALF_UP));
        }
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO settle(Long id, BigDecimal depositRefund, BigDecimal arrearsAmount) {
        BizTermination e = require(id);
        if (!TerminationStatus.APPROVED.name().equals(e.getTerminationStatus())) {
            throw BizException.stateConflict("仅在已批准状态可结算");
        }
        BigDecimal refund = nz(depositRefund);
        BigDecimal arrears = nz(arrearsAmount);
        BigDecimal damage = nz(e.getDamageAmount());
        // 结算金额 = 押金退还 - 欠费 - 损坏赔偿（正数退还，负数补缴）
        BigDecimal settle = refund.subtract(arrears).subtract(damage)
                .setScale(2, RoundingMode.HALF_UP);
        e.setDepositRefund(refund);
        e.setArrearsAmount(arrears);
        e.setSettleAmount(settle);
        e.setSettleStatus(SettleStatus.SETTLED.name());
        mapper.updateById(e);
        log.info("退租单 {} 结算完成：押金退还 {} - 欠费 {} - 损坏 {} = {}",
                e.getTerminationNo(), refund, arrears, damage, settle);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO markReleased(Long id, Boolean houseReleased, Boolean grantRevoked) {
        BizTermination e = require(id);
        if (houseReleased != null) {
            e.setHouseReleased(houseReleased ? 1 : 0);
        }
        if (grantRevoked != null) {
            e.setGrantRevoked(grantRevoked ? 1 : 0);
        }
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO complete(Long id, LocalDate actualExitDate) {
        BizTermination e = require(id);
        TerminationVO cur = TerminationVO.from(e);
        // 四个前置校验
        if (!"PASSED".equals(e.getInspectStatus())) {
            throw BizException.stateConflict("验房未通过，不能办结");
        }
        if (!SettleStatus.SETTLED.name().equals(e.getSettleStatus())
                && !SettleStatus.WAIVED.name().equals(e.getSettleStatus())) {
            throw BizException.stateConflict("结算未完成，不能办结");
        }
        if (cur.houseReleased() == null || !cur.houseReleased()) {
            throw BizException.stateConflict("房源未释放回可配池，不能办结");
        }
        if (cur.grantRevoked() == null || !cur.grantRevoked()) {
            throw BizException.stateConflict("授权未回收，不能办结");
        }
        transition(e, TerminationStatus.COMPLETED);
        e.setActualExitDate(actualExitDate == null ? LocalDate.now() : actualExitDate);
        mapper.updateById(e);
        log.info("退租单 {} 办结，房源 {} 已释放、授权已回收", e.getTerminationNo(), e.getHouseId());
        return TerminationVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public TerminationVO registerEnforce(Long id, LocalDate applyDate, String court,
                                         String itemHandlerName, String itemHandlerPhone,
                                         String notaryNo) {
        BizTermination e = require(id);
        if (applyDate != null) {
            e.setEnforceFlag(1);
            e.setEnforceApplyDate(applyDate);
        }
        if (court != null && !court.isBlank()) {
            e.setEnforceCourt(court);
        }
        if (itemHandlerName != null && !itemHandlerName.isBlank()) {
            e.setItemHandlerName(itemHandlerName);
            e.setItemHandlerPhone(itemHandlerPhone);
        }
        if (notaryNo != null && !notaryNo.isBlank()) {
            e.setNotaryFlag(1);
            e.setNotaryNo(notaryNo);
        }
        mapper.updateById(e);
        return TerminationVO.from(e);
    }

    // ==================== 内部 ====================

    private BizTermination require(Long id) {
        BizTermination e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("退租单");
        }
        return e;
    }

    private static void transition(BizTermination e, TerminationStatus target) {
        TerminationStatus from;
        try {
            from = TerminationStatus.valueOf(e.getTerminationStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("退租单状态非法: " + e.getTerminationStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!TerminationStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setTerminationStatus(target.name());
        e.setUpdateTime(LocalDateTime.now());
    }

    private static BigDecimal nz(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
'''

FILES['biz/controller/TerminationController.java'] = '''package com.yundao.bp.biz.controller;

import com.yundao.bp.biz.dto.TerminationCreateCmd;
import com.yundao.bp.biz.dto.TerminationVO;
import com.yundao.bp.biz.service.TerminationService;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDate;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 退租/腾退接口（BC-05 业务办理）。
 *
 * <p>办结需四个前置齐备：验房通过 + 结算完成 + 房源已释放 + 授权已回收。
 */
@RestController
@RequestMapping("/api/v1/terminations")
public class TerminationController {

    private final TerminationService service;

    public TerminationController(TerminationService service) {
        this.service = service;
    }

    @PostMapping
    public R<TerminationVO> apply(@Valid @RequestBody TerminationCreateCmd cmd) {
        return R.ok(service.apply(cmd));
    }

    @GetMapping("/{id}")
    public R<TerminationVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<TerminationVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                             @RequestParam(defaultValue = "20") long pageSize,
                                             @RequestParam(required = false) String type,
                                             @RequestParam(required = false) String status,
                                             @RequestParam(required = false) Long contractId,
                                             @RequestParam(required = false) Long houseId,
                                             @RequestParam(required = false) String keyword) {
        return R.ok(service.page(pageNum, pageSize, type, status, contractId, houseId, keyword));
    }

    @PostMapping("/{id}/submit")
    public R<TerminationVO> submit(@PathVariable Long id) {
        return R.ok(service.submit(id));
    }

    @PostMapping("/{id}/approve")
    public R<TerminationVO> approve(@PathVariable Long id,
                                    @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.approve(id, cmd == null ? null : cmd.reason()));
    }

    @PostMapping("/{id}/reject")
    public R<TerminationVO> reject(@PathVariable Long id,
                                   @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.reject(id, cmd == null ? null : cmd.reason()));
    }

    @PostMapping("/{id}/cancel")
    public R<TerminationVO> cancel(@PathVariable Long id,
                                   @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.cancel(id, cmd == null ? null : cmd.reason()));
    }

    /** 验房。 */
    @PostMapping("/{id}/inspect")
    public R<TerminationVO> inspect(@PathVariable Long id, @RequestBody InspectCmd cmd) {
        return R.ok(service.inspect(id, cmd.inspectStatus(), cmd.inspectResult(),
                cmd.damageAmount(), cmd.inspectImages()));
    }

    /** 结算。 */
    @PostMapping("/{id}/settle")
    public R<TerminationVO> settle(@PathVariable Long id, @RequestBody SettleCmd cmd) {
        return R.ok(service.settle(id, cmd.depositRefund(), cmd.arrearsAmount()));
    }

    /** 标记房源已释放 / 授权已回收。 */
    @PostMapping("/{id}/mark-released")
    public R<TerminationVO> markReleased(@PathVariable Long id, @RequestBody ReleaseCmd cmd) {
        return R.ok(service.markReleased(id, cmd.houseReleased(), cmd.grantRevoked()));
    }

    /** 办结。 */
    @PostMapping("/{id}/complete")
    public R<TerminationVO> complete(@PathVariable Long id,
                                     @RequestBody(required = false) CompleteCmd cmd) {
        return R.ok(service.complete(id, cmd == null ? null : cmd.actualExitDate()));
    }

    /** 登记强制执行/公证/物品处置人。 */
    @PostMapping("/{id}/register-enforce")
    public R<TerminationVO> registerEnforce(@PathVariable Long id,
                                            @RequestBody EnforceCmd cmd) {
        return R.ok(service.registerEnforce(id, cmd.enforceApplyDate(), cmd.enforceCourt(),
                cmd.itemHandlerName(), cmd.itemHandlerPhone(), cmd.notaryNo()));
    }

    public record ReasonCmd(String reason) {
    }

    public record InspectCmd(String inspectStatus, String inspectResult,
                             BigDecimal damageAmount, String inspectImages) {
    }

    public record SettleCmd(BigDecimal depositRefund, BigDecimal arrearsAmount) {
    }

    public record ReleaseCmd(Boolean houseReleased, Boolean grantRevoked) {
    }

    public record CompleteCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate actualExitDate) {
    }

    public record EnforceCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate enforceApplyDate,
            String enforceCourt, String itemHandlerName, String itemHandlerPhone,
            String notaryNo) {
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
