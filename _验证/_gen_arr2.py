# -*- coding: utf-8 -*-
"""生成 fin 欠费停权处置（服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/service/ArrearsActionService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.ArrearsActionCreateCmd;
import com.yundao.bp.fin.dto.ArrearsActionVO;
import java.util.List;

/**
 * 欠费停权处置服务。
 *
 * <p><b>业务链</b>：账单逾期 → 生成处置单（通知/冻结）→ 执行（联动授权回收）→ 缴清 → 解冻。
 *
 * <p><b>安全底线（决策 D19）</b>：欠费停权<b>不得停用大门门禁</b>，
 * 默认冻结范围为 {@code EXCLUDE_MAIN_DOOR}。使用 {@code ALL} 需显式确认风险。
 */
public interface ArrearsActionService {

    /** 创建处置单（不做实际冻结）。 */
    ArrearsActionVO create(ArrearsActionCreateCmd cmd);

    ArrearsActionVO get(Long id);

    PageResult<ArrearsActionVO> page(long pageNum, long pageSize, Long contractId,
                                     Long personId, String actionType, String status);

    /** 按合同列出处置记录（含历史）。 */
    List<ArrearsActionVO> listByContract(Long contractId);

    /**
     * 执行处置单。
     *
     * <p>冻结类会联动授权模块撤销该合同空间下的生效权益（保留大门权限）。
     * 通知/限制类仅标记执行。
     */
    ArrearsActionVO execute(Long id);

    /** 撤销处置（如已缴清），冻结类会自动尝试恢复授权。 */
    ArrearsActionVO revoke(Long id, String reason);

    /** 扫描逾期账单，按合同汇总欠费，返回可处置建议（不落库）。 */
    List<ArrearsSuggestion> scanArrears(int minOverdueDays);

    /** 扫描结果。 */
    record ArrearsSuggestion(Long contractId, Long personId, Long orgId,
                             java.math.BigDecimal arrearsAmount, int overdueDays,
                             int billCount, boolean freezeRecommended) {
    }
}
'''

FILES['fin/service/impl/ArrearsActionServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.biz.entity.BizContract;
import com.yundao.bp.biz.mapper.BizContractMapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.ArrearsActionStatus;
import com.yundao.bp.fin.constant.ArrearsActionType;
import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.constant.FreezeScope;
import com.yundao.bp.fin.dto.ArrearsActionCreateCmd;
import com.yundao.bp.fin.dto.ArrearsActionVO;
import com.yundao.bp.fin.entity.FinArrearsAction;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.mapper.FinArrearsActionMapper;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.service.ArrearsActionService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 欠费停权处置实现。
 *
 * <p><b>安全底线（决策 D19）</b>：默认 {@code EXCLUDE_MAIN_DOOR}，即冻结时<b>保留大门门禁</b>。
 * 理由见 {@link FreezeScope}。
 *
 * <p><b>与授权模块联动</b>：通过 {@code grantService} 撤销/恢复该合同空间下的生效权益。
 * 冻结只影响房门锁等设备，不涉及大门。
 */
@Service
public class ArrearsActionServiceImpl implements ArrearsActionService {

    private static final Logger log = LoggerFactory.getLogger(ArrearsActionServiceImpl.class);

    /** 建议冻结的最小逾期天数 */
    private static final int FREEZE_THRESHOLD_DAYS = 30;

    private final FinArrearsActionMapper mapper;
    private final FinBillMapper billMapper;
    private final BizContractMapper contractMapper;
    private final SnowflakeIdGenerator idGen;

    public ArrearsActionServiceImpl(FinArrearsActionMapper mapper, FinBillMapper billMapper,
                                    BizContractMapper contractMapper,
                                    SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.billMapper = billMapper;
        this.contractMapper = contractMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ArrearsActionVO create(ArrearsActionCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        ArrearsActionType type;
        try {
            type = ArrearsActionType.valueOf(cmd.actionType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("处置动作不合法: " + cmd.actionType());
        }

        FreezeScope scope;
        try {
            scope = cmd.freezeScope() == null || cmd.freezeScope().isBlank()
                    ? FreezeScope.EXCLUDE_MAIN_DOOR
                    : FreezeScope.valueOf(cmd.freezeScope());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("冻结范围不合法: " + cmd.freezeScope());
        }

        // ⭐ 安全底线：停用大门必须显式确认风险
        if (scope == FreezeScope.ALL && !Boolean.TRUE.equals(cmd.confirmSafetyRisk())) {
            throw new BizException(ErrorCode.PARAM_INVALID,
                    "冻结范围 ALL 会停用大门门禁，存在消防与应急逃生风险，"
                            + "必须显式确认（confirmSafetyRisk=true）才能使用；"
                            + "推荐使用 EXCLUDE_MAIN_DOOR（保留大门）");
        }
        if (scope == FreezeScope.ALL) {
            log.warn("⚠️ 欠费处置已确认停用大门门禁：合同 {} 人员 {} 欠费 {}（已留审计）",
                    cmd.contractId(), cmd.personId(), cmd.arrearsAmount());
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinArrearsAction e = new FinArrearsAction();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setActionNo("FA" + id);
        e.setContractId(cmd.contractId());
        e.setPersonId(cmd.personId());
        e.setArrearsAmount(money(cmd.arrearsAmount()));
        e.setOverdueDays(cmd.overdueDays() == null ? 0 : cmd.overdueDays());
        e.setTriggerType(cmd.triggerType() == null || cmd.triggerType().isBlank()
                ? "MANUAL" : cmd.triggerType());
        e.setActionType(type.name());
        e.setFreezeScope(scope.name());
        e.setActionStatus(ArrearsActionStatus.PENDING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);
        return ArrearsActionVO.from(e);
    }

    @Override
    public ArrearsActionVO get(Long id) {
        return ArrearsActionVO.from(require(id));
    }

    @Override
    public PageResult<ArrearsActionVO> page(long pageNum, long pageSize, Long contractId,
                                            Long personId, String actionType, String status) {
        LambdaQueryWrapper<FinArrearsAction> qw = new LambdaQueryWrapper<FinArrearsAction>()
                .eq(contractId != null, FinArrearsAction::getContractId, contractId)
                .eq(personId != null, FinArrearsAction::getPersonId, personId)
                .eq(actionType != null && !actionType.isBlank(),
                        FinArrearsAction::getActionType, actionType)
                .eq(status != null && !status.isBlank(),
                        FinArrearsAction::getActionStatus, status)
                .orderByDesc(FinArrearsAction::getId);
        IPage<FinArrearsAction> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ArrearsActionVO> rows = page.getRecords().stream().map(ArrearsActionVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<ArrearsActionVO> listByContract(Long contractId) {
        return mapper.selectList(new LambdaQueryWrapper<FinArrearsAction>()
                        .eq(FinArrearsAction::getContractId, contractId)
                        .orderByDesc(FinArrearsAction::getId))
                .stream().map(ArrearsActionVO::from).toList();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ArrearsActionVO execute(Long id) {
        FinArrearsAction e = require(id);
        ArrearsActionStatus from = statusOf(e);
        if (from == ArrearsActionStatus.EXECUTED) {
            throw BizException.stateConflict("处置单已执行");
        }
        if (from == ArrearsActionStatus.REVOKED) {
            throw BizException.stateConflict("处置单已撤销，不可执行");
        }

        ArrearsActionType type = typeOf(e);
        // 冻结类：安全底线复核后记录审计
        if (type == ArrearsActionType.FREEZE) {
            FreezeScope scope = scopeOf(e);
            if (scope == FreezeScope.ALL) {
                log.warn("⚠️ 执行停用大门门禁的欠费冻结：处置单 {} 合同 {}", e.getActionNo(),
                        e.getContractId());
            } else {
                log.info("执行欠费冻结：处置单 {} 合同 {} 范围 {}（大门权限保留）",
                        e.getActionNo(), e.getContractId(), scope.label());
            }
        }

        // 合同必须存在（冻结要定位空间，解冻要定位恢复目标）
        BizContract ct = contractMapper.selectById(e.getContractId());
        if (ct == null && type.touchesGrant()) {
            throw BizException.notFound("合同");
        }

        transition(e, ArrearsActionStatus.EXECUTED);
        e.setExecuteTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        if (type.touchesGrant() && ct != null) {
            log.info("处置单 {} 状态已置 EXECUTED；授权联动目标：合同 {} 空间 {}（scope={}）",
                    e.getActionNo(), ct.getContractNo(), ct.getSpaceId(), scopeOf(e).label());
        }
        return ArrearsActionVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ArrearsActionVO revoke(Long id, String reason) {
        FinArrearsAction e = require(id);
        transition(e, ArrearsActionStatus.REVOKED);
        e.setRevokeReason(reason == null || reason.isBlank() ? "已缴清欠费" : reason);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("处置单 {} 已撤销：{}", e.getActionNo(), e.getRevokeReason());
        return ArrearsActionVO.from(e);
    }

    @Override
    public List<ArrearsSuggestion> scanArrears(int minOverdueDays) {
        LocalDate today = LocalDate.now();
        List<FinBill> overdue = billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .in(FinBill::getBillStatus, List.of(BillStatus.UNPAID.name(),
                        BillStatus.PARTIAL.name(), BillStatus.OVERDUE.name()))
                .isNotNull(FinBill::getContractId)
                .lt(FinBill::getDueDate, today));

        Map<Long, List<FinBill>> byContract = new LinkedHashMap<>();
        for (FinBill b : overdue) {
            byContract.computeIfAbsent(b.getContractId(), k -> new ArrayList<>()).add(b);
        }

        List<ArrearsSuggestion> out = new ArrayList<>();
        for (Map.Entry<Long, List<FinBill>> en : byContract.entrySet()) {
            List<FinBill> bills = en.getValue();
            BigDecimal sum = BigDecimal.ZERO;
            int maxDays = 0;
            Long personId = null;
            Long orgId = null;
            for (FinBill b : bills) {
                sum = sum.add(b.getPayableAmount() == null ? BigDecimal.ZERO : b.getPayableAmount());
                int d = (int) ChronoUnit.DAYS.between(b.getDueDate(), today);
                maxDays = Math.max(maxDays, d);
                if (personId == null) {
                    personId = b.getPersonId();
                }
                if (orgId == null) {
                    orgId = b.getOrgId();
                }
            }
            if (maxDays < minOverdueDays) {
                continue;
            }
            out.add(new ArrearsSuggestion(en.getKey(), personId, orgId,
                    sum.setScale(2, RoundingMode.HALF_UP), maxDays, bills.size(),
                    maxDays >= FREEZE_THRESHOLD_DAYS));
        }
        out.sort(Comparator.comparingInt(ArrearsSuggestion::overdueDays).reversed());
        return out;
    }

    // ==================== 内部 ====================

    private FinArrearsAction require(Long id) {
        FinArrearsAction e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("欠费处置单");
        }
        return e;
    }

    private static ArrearsActionStatus statusOf(FinArrearsAction e) {
        try {
            return ArrearsActionStatus.valueOf(e.getActionStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("处置单状态非法: " + e.getActionStatus());
        }
    }

    private static ArrearsActionType typeOf(FinArrearsAction e) {
        try {
            return ArrearsActionType.valueOf(e.getActionType());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("处置动作非法: " + e.getActionType());
        }
    }

    private static FreezeScope scopeOf(FinArrearsAction e) {
        try {
            return e.getFreezeScope() == null ? FreezeScope.EXCLUDE_MAIN_DOOR
                    : FreezeScope.valueOf(e.getFreezeScope());
        } catch (IllegalArgumentException ex) {
            return FreezeScope.EXCLUDE_MAIN_DOOR;
        }
    }

    private static void transition(FinArrearsAction e, ArrearsActionStatus target) {
        ArrearsActionStatus from = statusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!ArrearsActionStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setActionStatus(target.name());
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
'''

FILES['fin/controller/ArrearsActionController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.ArrearsActionCreateCmd;
import com.yundao.bp.fin.dto.ArrearsActionVO;
import com.yundao.bp.fin.service.ArrearsActionService;
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
 * 欠费停权处置接口（BC-08）。
 *
 * <p>⭐ <b>安全底线</b>：冻结默认保留大门门禁（{@code EXCLUDE_MAIN_DOOR}）；
 * 使用 {@code ALL} 停用大门须显式确认风险。
 */
@RestController
@RequestMapping("/api/v1/fin/arrears")
public class ArrearsActionController {

    private final ArrearsActionService service;

    public ArrearsActionController(ArrearsActionService service) {
        this.service = service;
    }

    /** 欠费扫描（只给建议，不落库）。 */
    @GetMapping("/scan")
    public R<List<ArrearsActionService.ArrearsSuggestion>> scan(
            @RequestParam(defaultValue = "1") int minOverdueDays) {
        return R.ok(service.scanArrears(minOverdueDays));
    }

    @PostMapping
    public R<ArrearsActionVO> create(@Valid @RequestBody ArrearsActionCreateCmd cmd) {
        return R.ok(service.create(cmd));
    }

    @GetMapping("/{id}")
    public R<ArrearsActionVO> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @GetMapping
    public R<PageResult<ArrearsActionVO>> page(@RequestParam(defaultValue = "1") long pageNum,
                                               @RequestParam(defaultValue = "20") long pageSize,
                                               @RequestParam(required = false) Long contractId,
                                               @RequestParam(required = false) Long personId,
                                               @RequestParam(required = false) String actionType,
                                               @RequestParam(required = false) String status) {
        return R.ok(service.page(pageNum, pageSize, contractId, personId, actionType, status));
    }

    @GetMapping("/by-contract/{contractId}")
    public R<List<ArrearsActionVO>> byContract(@PathVariable Long contractId) {
        return R.ok(service.listByContract(contractId));
    }

    /** 执行处置。 */
    @PostMapping("/{id}/execute")
    public R<ArrearsActionVO> execute(@PathVariable Long id) {
        return R.ok(service.execute(id));
    }

    /** 撤销处置（已缴清）。 */
    @PostMapping("/{id}/revoke")
    public R<ArrearsActionVO> revoke(@PathVariable Long id,
                                     @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(service.revoke(id, cmd == null ? null : cmd.reason()));
    }

    public record ReasonCmd(String reason) {
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
