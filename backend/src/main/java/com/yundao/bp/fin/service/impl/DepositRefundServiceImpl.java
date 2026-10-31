package com.yundao.bp.fin.service.impl;

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


    /** 数据范围（ALL/ORG_SUB/ORG/SELF） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.iam.datascope.DataScopeService dataScopeService;

    /** 按数据范围追加条件（full=true 时组织也过滤）。 */
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
            return;     // 无组织列时，ORG/ORG_SUB 不额外限制
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


    /** 合同（取组织用于数据范围过滤） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper contractOrgIdMapper;

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
        BigDecimal due = exempt ? BigDecimal.ZERO
                : (cmd.depositAmount() == null ? BigDecimal.ZERO : money(cmd.depositAmount()));
        BigDecimal paid = exempt ? BigDecimal.ZERO
                : (cmd.paidAmount() == null ? BigDecimal.ZERO : money(cmd.paidAmount()));
        if ((due == null || due.compareTo(BigDecimal.ZERO) == 0) && cmd.depositAmount() == null
                && contractOrgIdMapper != null) {
            com.yundao.bp.biz.entity.BizContract c =
                    contractOrgIdMapper.selectById(cmd.contractId());
            if (c != null && c.getDepositAmount() != null) {
                due = money(c.getDepositAmount());
            }
        }
        if (due == null) {
            due = BigDecimal.ZERO;
        }
        BigDecimal cap = cmd.capAmount() == null ? null : money(cmd.capAmount());
        boolean overCap = cap != null && due.compareTo(cap) > 0;

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinDeposit e = new FinDeposit();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setContractId(cmd.contractId());
        // 组织取自合同，供数据范围（ORG/ORG_SUB）过滤
        if (contractOrgIdMapper != null) {
            com.yundao.bp.biz.entity.BizContract c = contractOrgIdMapper.selectById(cmd.contractId());
            if (c != null) {
                e.setOrgId(c.getOrgId());
            }
        }
        Long depositPerson = cmd.personId();
        if (depositPerson == null && contractOrgIdMapper != null) {
            com.yundao.bp.biz.entity.BizContract c =
                    contractOrgIdMapper.selectById(cmd.contractId());
            depositPerson = c == null ? null : c.getLesseePersonId();
        }
        e.setPersonId(depositPerson);
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
        applyDataScope(qw, FinDeposit::getOrgId, FinDeposit::getPersonId, true);
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
        // 押金退还：原子扣减（条件更新），并发下不会超退
        //   update ... set refund += amt, balance -= amt where contract_id=? and balance >= amt
        //   影响行数为 0 说明余额不足或台账不存在
        if ("DEPOSIT".equals(cmd.refundType()) && cmd.contractId() != null) {
            int affected = depositMapper.update(null,
                    new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper
                            <FinDeposit>()
                            .eq(FinDeposit::getContractId, cmd.contractId())
                            .ge(FinDeposit::getBalanceAmount, amt)
                            .setSql("refund_amount = refund_amount + " + amt
                                    + ", balance_amount = balance_amount - " + amt));
            if (affected == 0) {
                FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                        .eq(FinDeposit::getContractId, cmd.contractId()).last("LIMIT 1"));
                if (dep == null) {
                    throw BizException.stateConflict("该合同无押金台账，无法退还押金");
                }
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

        // 原子扣减后同步押金状态（避免余额为 0 但状态仍是已收取）
        if ("DEPOSIT".equals(cmd.refundType()) && cmd.contractId() != null) {
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, cmd.contractId()).last("LIMIT 1"));
            if (dep != null) {
                recalcDeposit(dep);
                dep.setUpdateTime(LocalDateTime.now());
                depositMapper.updateById(dep);
            }
        }
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

        // 退款创建时已扣减押金余额；驳回需原路回补，避免钱被“吞掉”
        if ("DEPOSIT".equals(e.getRefundType()) && e.getContractId() != null) {
            BigDecimal amt = money(e.getRefundAmount());
            int restored = depositMapper.update(null,
                    new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper
                            <FinDeposit>()
                            .eq(FinDeposit::getContractId, e.getContractId())
                            .ge(FinDeposit::getRefundAmount, amt)
                            .setSql("refund_amount = refund_amount - " + amt
                                    + ", balance_amount = balance_amount + " + amt));
            FinDeposit dep = depositMapper.selectOne(new LambdaQueryWrapper<FinDeposit>()
                    .eq(FinDeposit::getContractId, e.getContractId()).last("LIMIT 1"));
            if (dep != null) {
                recalcDeposit(dep);
                dep.setUpdateTime(LocalDateTime.now());
                depositMapper.updateById(dep);
            }
            log.info("退款 {} 驳回，回补押金 {}（影响 {} 行）", e.getRefundNo(), amt, restored);
        }
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
        // 退款打款 → 支出流水
        writeFlow(com.yundao.bp.fin.constant.FlowType.EXPENSE,
                com.yundao.bp.fin.constant.FlowBizType.REFUND, e.getId(),
                e.getRefundAmount(), "退款 " + e.getRefundNo());

        return RefundVO.from(e);
    }


    /** 资金流水记录器（可选注入，便于单测时不依赖） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.service.CashFlowService cashFlowService;

    private void writeFlow(com.yundao.bp.fin.constant.FlowType type,
                           com.yundao.bp.fin.constant.FlowBizType bizType,
                           Long bizId, java.math.BigDecimal amount, String remark) {
        if (cashFlowService == null) {
            return;
        }
        try {
            cashFlowService.record(type, bizType, bizId, amount, remark);
        } catch (Exception ex) {
            log.warn("写资金流水失败（不影响主业务）：{}", ex.getMessage());
        }
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
        if (balance.compareTo(BigDecimal.ZERO) > 0) {
            // 还有余额：有过退款算部分退还，否则仍是已收取
            e.setDepositStatus(refunded.compareTo(BigDecimal.ZERO) > 0
                    ? DepositStatus.PARTIAL_REFUND.name() : DepositStatus.HELD.name());
        } else if (refunded.compareTo(BigDecimal.ZERO) > 0) {
            // 余额归零且有退款 → 已退还（即使其中一部分被抵扣，钱最终退给了租户）
            e.setDepositStatus(DepositStatus.REFUNDED.name());
        } else if (deducted.compareTo(BigDecimal.ZERO) > 0) {
            // 余额归零且无退款 → 全部抵扣（押金被全额扣留）
            e.setDepositStatus(DepositStatus.DEDUCTED.name());
        } else {
            // 从未收取（免收/0 押金）
            e.setDepositStatus(DepositStatus.REFUNDED.name());
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
