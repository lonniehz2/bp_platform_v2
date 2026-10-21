# -*- coding: utf-8 -*-
"""生成 fin 退款单 + 押金台账（服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/service/DepositRefundService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.DepositCreateCmd;
import com.yundao.bp.fin.dto.DepositVO;
import com.yundao.bp.fin.dto.RefundCreateCmd;
import com.yundao.bp.fin.dto.RefundVO;
import java.math.BigDecimal;

/**
 * 押金台账 + 退款单服务。
 *
 * <p>退租结算落地路径：
 * <pre>
 *   押金台账(已收 2000) ──抵扣损坏 300──> 余额 1700
 *   ──申请退款 1700（DEPOSIT）──> 审批 ──> 已退款，台账 REFUNDED
 * </pre>
 */
public interface DepositRefundService {

    // ---------- 押金台账 ----------
    /** 建立押金台账（签约时调用，一合同一条）。 */
    DepositVO createDeposit(DepositCreateCmd cmd);

    DepositVO getDeposit(Long id);

    /** 按合同查押金台账。 */
    DepositVO getDepositByContract(Long contractId);

    PageResult<DepositVO> pageDeposits(long pageNum, long pageSize, Long contractId,
                                       Long personId, String status);

    /** 补收押金。 */
    DepositVO receiveDeposit(Long id, BigDecimal amount);

    /** 押金抵扣（如退租损坏赔偿）。 */
    DepositVO deductDeposit(Long id, BigDecimal amount, String reason);

    // ---------- 退款单 ----------
    RefundVO createRefund(RefundCreateCmd cmd);

    RefundVO getRefund(Long id);

    PageResult<RefundVO> pageRefunds(long pageNum, long pageSize, Long personId,
                                     Long contractId, String status);

    /** 审批通过。 */
    RefundVO approveRefund(Long id, Long approveById);

    /** 驳回。 */
    RefundVO rejectRefund(Long id, Long approveById, String reason);

    /** 打款完成（联动押金台账减少余额）。 */
    RefundVO completeRefund(Long id);
}
'''

FILES['fin/service/impl/DepositRefundServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.DepositStatus;
import com.yundao.bp.fin.constant.RefundStatus;
import com.yundao.bp.fin.dto.DepositCreateCmd;
import com.yundao.bp.fin.dto.DepositVO;
import com.yundao.bp.fin.dto.RefundCreateCmd;
import com.yundao.bp.fin.dto.RefundVO;
import com.yundao.bp.fin.entity.FinDeposit;
import com.yundao.bp.fin.entity.FinRefund;
import com.yundao.bp.fin.mapper.FinDepositMapper;
import com.yundao.bp.fin.mapper.FinRefundMapper;
import com.yundao.bp.fin.service.DepositRefundService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 押金台账与退款实现。
 *
 * <p><b>押金余额口径</b>：{@code balance = 已收 - 已抵扣 - 已退还}，任何操作后都重算并落库。
 *
 * <p><b>政策上限</b>：成都规定押金不超过 1000 元；超限时标记 {@code over_cap_flag=1}，
 * 但<b>不阻断</b>（可能是历史数据或特殊审批），由业务侧复核。
 */
@Service
public class DepositRefundServiceImpl implements DepositRefundService {

    private static final Logger log = LoggerFactory.getLogger(DepositRefundServiceImpl.class);

    private final FinDepositMapper depositMapper;
    private final FinRefundMapper refundMapper;
    private final SnowflakeIdGenerator idGen;

    public DepositRefundServiceImpl(FinDepositMapper depositMapper, FinRefundMapper refundMapper,
                                    SnowflakeIdGenerator idGen) {
        this.depositMapper = depositMapper;
        this.refundMapper = refundMapper;
        this.idGen = idGen;
    }

    // ==================== 押金台账 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DepositVO createDeposit(DepositCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();

        FinDeposit exist = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                .eq(FinDeposit::getContractId, cmd.contractId())
                .last("LIMIT 1"));
        if (exist != null) {
            throw BizException.stateConflict("该合同已有押金台账（ID=" + exist.getId() + "）");
        }

        boolean exempt = cmd.isExempt() != null && cmd.isExempt() == 1;
        BigDecimal due = exempt ? money(null) : money(cmd.depositAmount());
        BigDecimal paid = exempt ? money(null) : money(cmd.paidAmount());
        BigDecimal cap = cmd.capAmount() == null ? null : money(cmd.capAmount());
        boolean overCap = cap != null && due.compareTo(cap) > 0;

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinDeposit e = new FinDeposit();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setContractId(cmd.contractId());
        e.setPersonId(cmd.personId());
        e.setDepositAmount(due);
        e.setPaidAmount(paid);
        e.setDeductAmount(money(null));
        e.setRefundAmount(money(null));
        e.setBalanceAmount(paid.setScale(2, RoundingMode.HALF_UP));
        e.setDepositStatus(DepositStatus.HELD.name());
        e.setCapAmount(cap);
        e.setIsExempt(exempt ? 1 : 0);
        e.setExemptReason(cmd.exemptReason());
        e.setOverCapFlag(overCap ? 1 : 0);
        e.setCreateTime(now);
        e.setUpdateTime(now);
        depositMapper.insert(e);

        if (overCap) {
            log.warn("押金超政策上限：合同 {} 应收 {} > 上限 {}（成都标准 1000 元）",
                    cmd.contractId(), due, cap);
        }
        return DepositVO.from(e);
    }

    @Override
    public DepositVO getDeposit(Long id) {
        return DepositVO.from(requireDeposit(id));
    }

    @Override
    public DepositVO getDepositByContract(Long contractId) {
        FinDeposit e = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                .eq(FinDeposit::getContractId, contractId)
                .last("LIMIT 1"));
        if (e == null) {
            throw BizException.notFound("押金台账");
        }
        return DepositVO.from(e);
    }

    @Override
    public PageResult<DepositVO> pageDeposits(long pageNum, long pageSize, Long contractId,
                                              Long personId, String status) {
        LambdaQueryWrapper<FinDeposit> qw = new LambdaQueryWrapper<FinDeposit>()
                .eq(contractId != null, FinDeposit::getContractId, contractId)
                .eq(personId != null, FinDeposit::getPersonId, personId)
                .eq(status != null && !status.isBlank(), FinDeposit::getDepositStatus, status)
                .orderByDesc(FinDeposit::getId);
        IPage<FinDeposit> page = depositMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<DepositVO> rows = page.getRecords().stream().map(DepositVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DepositVO receiveDeposit(Long id, BigDecimal amount) {
        FinDeposit e = requireDeposit(id);
        if (DepositStatus.HELD.name().equals(e.getDepositStatus())
                && money(e.getBalanceAmount()).compareTo(BigDecimal.ZERO) < 0) {
            throw BizException.stateConflict("押金台账状态异常");
        }
        BigDecimal add = money(amount);
        if (add.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("补收金额必须大于 0");
        }
        e.setPaidAmount(money(e.getPaidAmount()).add(add).setScale(2, RoundingMode.HALF_UP));
        recalcDeposit(e);
        e.setUpdateTime(LocalDateTime.now());
        depositMapper.updateById(e);
        return DepositVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DepositVO deductDeposit(Long id, BigDecimal amount, String reason) {
        FinDeposit e = requireDeposit(id);
        DepositStatus st = depositStatusOf(e);
        if (st.isClosed()) {
            throw BizException.stateConflict("押金已" + st.label() + "，不可再抵扣");
        }
        BigDecimal ded = money(amount);
        if (ded.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("抵扣金额必须大于 0");
        }
        if (ded.compareTo(money(e.getBalanceAmount())) > 0) {
            throw BizException.paramInvalid(
                    "抵扣金额超过押金余额 " + money(e.getBalanceAmount()));
        }
        e.setDeductAmount(money(e.getDeductAmount()).add(ded).setScale(2, RoundingMode.HALF_UP));
        recalcDeposit(e);
        e.setUpdateTime(LocalDateTime.now());
        depositMapper.updateById(e);
        log.info("押金抵扣：台账 {} 抵扣 {}，原因：{}，余额 {}", id, ded, reason,
                e.getBalanceAmount());
        return DepositVO.from(e);
    }

    // ==================== 退款单 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RefundVO createRefund(RefundCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        BigDecimal amt = money(cmd.refundAmount());
        if (amt.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("退款金额必须大于 0");
        }
        // 押金退还：不得超过押金台账余额
        if ("DEPOSIT".equals(cmd.refundType()) && cmd.contractId() != null) {
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, cmd.contractId()).last("LIMIT 1"));
            if (dep == null) {
                throw BizException.stateConflict("该合同无押金台账，无法退还押金");
            }
            if (amt.compareTo(money(dep.getBalanceAmount())) > 0) {
                throw BizException.paramInvalid(
                        "退款金额超过押金余额 " + money(dep.getBalanceAmount()));
            }
        }

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinRefund e = new FinRefund();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setRefundNo("FR" + id);
        e.setPaymentId(cmd.paymentId());
        e.setPersonId(cmd.personId());
        e.setContractId(cmd.contractId());
        e.setRefundAmount(amt);
        e.setRefundReason(cmd.refundReason());
        e.setRefundType(cmd.refundType());
        e.setRefundChannel(blankToNull(cmd.refundChannel()) == null
                ? "ORIGINAL" : cmd.refundChannel());
        e.setRefundStatus(RefundStatus.PENDING.name());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        refundMapper.insert(e);
        return RefundVO.from(e);
    }

    @Override
    public RefundVO getRefund(Long id) {
        return RefundVO.from(requireRefund(id));
    }

    @Override
    public PageResult<RefundVO> pageRefunds(long pageNum, long pageSize, Long personId,
                                            Long contractId, String status) {
        LambdaQueryWrapper<FinRefund> qw = new LambdaQueryWrapper<FinRefund>()
                .eq(personId != null, FinRefund::getPersonId, personId)
                .eq(contractId != null, FinRefund::getContractId, contractId)
                .eq(status != null && !status.isBlank(), FinRefund::getRefundStatus, status)
                .orderByDesc(FinRefund::getId);
        IPage<FinRefund> page = refundMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<RefundVO> rows = page.getRecords().stream().map(RefundVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RefundVO approveRefund(Long id, Long approveById) {
        FinRefund e = requireRefund(id);
        transition(e, RefundStatus.APPROVED);
        e.setApproveById(approveById);
        e.setApproveTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        refundMapper.updateById(e);
        return RefundVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RefundVO rejectRefund(Long id, Long approveById, String reason) {
        FinRefund e = requireRefund(id);
        transition(e, RefundStatus.REJECTED);
        e.setApproveById(approveById);
        e.setApproveTime(LocalDateTime.now());
        e.setRefundReason(reason);
        e.setUpdateTime(LocalDateTime.now());
        refundMapper.updateById(e);
        return RefundVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public RefundVO completeRefund(Long id) {
        FinRefund e = requireRefund(id);
        transition(e, RefundStatus.SUCCESS);
        e.setRefundTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        refundMapper.updateById(e);

        // 押金退还：同步扣减押金台账余额
        if ("DEPOSIT".equals(e.getRefundType()) && e.getContractId() != null) {
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, e.getContractId()).last("LIMIT 1"));
            if (dep != null) {
                dep.setRefundAmount(money(dep.getRefundAmount())
                        .add(money(e.getRefundAmount())).setScale(2, RoundingMode.HALF_UP));
                recalcDeposit(dep);
                dep.setUpdateTime(LocalDateTime.now());
                depositMapper.updateById(dep);
                log.info("押金退还：合同 {} 退还 {}，台账余额 {}", e.getContractId(),
                        e.getRefundAmount(), dep.getBalanceAmount());
            }
        }
        return RefundVO.from(e);
    }

    // ==================== 内部 ====================

    /** 重算押金余额与状态。 */
    private static void recalcDeposit(FinDeposit e) {
        BigDecimal balance = money(e.getPaidAmount())
                .subtract(money(e.getDeductAmount()))
                .subtract(money(e.getRefundAmount()))
                .setScale(2, RoundingMode.HALF_UP);
        e.setBalanceAmount(balance);
        BigDecimal refunded = money(e.getRefundAmount());
        BigDecimal deducted = money(e.getDeductAmount());
        if (money(e.getPaidAmount()).compareTo(BigDecimal.ZERO) == 0 && balance.compareTo(
                BigDecimal.ZERO) == 0) {
            e.setDepositStatus(DepositStatus.REFUNDED.name());
        } else if (balance.compareTo(BigDecimal.ZERO) <= 0) {
            e.setDepositStatus(deducted.compareTo(BigDecimal.ZERO) > 0
                    ? DepositStatus.DEDUCTED.name() : DepositStatus.REFUNDED.name());
        } else if (refunded.compareTo(BigDecimal.ZERO) > 0) {
            e.setDepositStatus(DepositStatus.PARTIAL_REFUND.name());
        } else {
            e.setDepositStatus(DepositStatus.HELD.name());
        }
    }

    private FinDeposit requireDeposit(Long id) {
        FinDeposit e = depositMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("押金台账");
        }
        return e;
    }

    private FinRefund requireRefund(Long id) {
        FinRefund e = refundMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("退款单");
        }
        return e;
    }

    private static DepositStatus depositStatusOf(FinDeposit e) {
        try {
            return DepositStatus.valueOf(e.getDepositStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("押金状态非法: " + e.getDepositStatus());
        }
    }

    private static void transition(FinRefund e, RefundStatus target) {
        RefundStatus from;
        try {
            from = RefundStatus.valueOf(e.getRefundStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("退款单状态非法: " + e.getRefundStatus());
        }
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!RefundStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "退款状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setRefundStatus(target.name());
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
'''

FILES['fin/controller/DepositRefundController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.DepositCreateCmd;
import com.yundao.bp.fin.dto.DepositVO;
import com.yundao.bp.fin.dto.RefundCreateCmd;
import com.yundao.bp.fin.dto.RefundVO;
import com.yundao.bp.fin.service.DepositRefundService;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 押金台账与退款接口（BC-08 资金账务）。
 *
 * <p>退租结算落地：押金抵扣 → 申请退款 → 审批 → 打款（自动扣减台账余额）。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class DepositRefundController {

    private final DepositRefundService service;

    public DepositRefundController(DepositRefundService service) {
        this.service = service;
    }

    // ---------- 押金 ----------

    @PostMapping("/deposits")
    public R<DepositVO> createDeposit(@Valid @RequestBody DepositCreateCmd cmd) {
        return R.ok(service.createDeposit(cmd));
    }

    @GetMapping("/deposits/{id}")
    public R<DepositVO> getDeposit(@PathVariable Long id) {
        return R.ok(service.getDeposit(id));
    }

    @GetMapping("/deposits/by-contract/{contractId}")
    public R<DepositVO> byContract(@PathVariable Long contractId) {
        return R.ok(service.getDepositByContract(contractId));
    }

    @GetMapping("/deposits")
    public R<PageResult<DepositVO>> pageDeposits(@RequestParam(defaultValue = "1") long pageNum,
                                                 @RequestParam(defaultValue = "20") long pageSize,
                                                 @RequestParam(required = false) Long contractId,
                                                 @RequestParam(required = false) Long personId,
                                                 @RequestParam(required = false) String status) {
        return R.ok(service.pageDeposits(pageNum, pageSize, contractId, personId, status));
    }

    @PostMapping("/deposits/{id}/receive")
    public R<DepositVO> receive(@PathVariable Long id, @RequestBody AmountCmd cmd) {
        return R.ok(service.receiveDeposit(id, cmd.amount()));
    }

    /** 押金抵扣（退租损坏赔偿等）。 */
    @PostMapping("/deposits/{id}/deduct")
    public R<DepositVO> deduct(@PathVariable Long id, @RequestBody AmountCmd cmd) {
        return R.ok(service.deductDeposit(id, cmd.amount(), cmd.reason()));
    }

    // ---------- 退款 ----------

    @PostMapping("/refunds")
    public R<RefundVO> createRefund(@Valid @RequestBody RefundCreateCmd cmd) {
        return R.ok(service.createRefund(cmd));
    }

    @GetMapping("/refunds/{id}")
    public R<RefundVO> getRefund(@PathVariable Long id) {
        return R.ok(service.getRefund(id));
    }

    @GetMapping("/refunds")
    public R<PageResult<RefundVO>> pageRefunds(@RequestParam(defaultValue = "1") long pageNum,
                                               @RequestParam(defaultValue = "20") long pageSize,
                                               @RequestParam(required = false) Long personId,
                                               @RequestParam(required = false) Long contractId,
                                               @RequestParam(required = false) String status) {
        return R.ok(service.pageRefunds(pageNum, pageSize, personId, contractId, status));
    }

    @PostMapping("/refunds/{id}/approve")
    public R<RefundVO> approve(@PathVariable Long id, @RequestBody(required = false) ApproveCmd cmd) {
        return R.ok(service.approveRefund(id, cmd == null ? null : cmd.approveById()));
    }

    @PostMapping("/refunds/{id}/reject")
    public R<RefundVO> reject(@PathVariable Long id, @RequestBody(required = false) ApproveCmd cmd) {
        return R.ok(service.rejectRefund(id,
                cmd == null ? null : cmd.approveById(),
                cmd == null ? null : cmd.reason()));
    }

    /** 打款完成（联动押金台账）。 */
    @PostMapping("/refunds/{id}/complete")
    public R<RefundVO> complete(@PathVariable Long id) {
        return R.ok(service.completeRefund(id));
    }

    public record AmountCmd(BigDecimal amount, String reason) {
    }

    public record ApproveCmd(Long approveById, String reason) {
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
