# -*- coding: utf-8 -*-
"""生成 fin 资金账务（第 2 部分：服务/控制器）"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/service/BillingService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.PaymentCreateCmd;
import com.yundao.bp.fin.dto.PaymentVO;
import java.math.BigDecimal;

/**
 * 账单与收款服务（BC-08 资金账务）。
 *
 * <p><b>核销闭环</b>：账单(应收) → 收款单(实收) → 核销明细 → 账单状态与应付金额回写。
 */
public interface BillingService {

    // ---------- 账单 ----------
    BillVO createBill(BillCreateCmd cmd);

    BillVO getBill(Long id);

    PageResult<BillVO> pageBills(long pageNum, long pageSize, Long orgId, Long contractId,
                                 Long personId, String status, String keyword);

    /** 逾期扫描：过缴费截止日仍未缴的账单置 OVERDUE 并回填逾期天数。 */
    int scanOverdue();

    /** 减免/免除账单。 */
    BillVO waiveBill(Long id, BigDecimal waiveAmount, String reason);

    /** 作废账单（已收金额必须为 0）。 */
    BillVO cancelBill(Long id, String reason);

    // ---------- 收款 ----------
    PaymentVO createPayment(PaymentCreateCmd cmd);

    PaymentVO getPayment(Long id);

    PageResult<PaymentVO> pagePayments(long pageNum, long pageSize, Long orgId, Long personId,
                                       String status, String keyword);

    /** 确认收款成功（PENDING → SUCCESS）。 */
    PaymentVO confirmPayment(Long id);

    /**
     * 核销：把收款单的钱核到指定账单上。
     *
     * <p>核销额不能超过「收款单可核销余额」与「账单应付金额」两者较小值。
     */
    BillVO allocate(Long paymentId, Long billId, BigDecimal amount);
}
'''

FILES['fin/service/impl/BillingServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.constant.PayStatus;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.PaymentCreateCmd;
import com.yundao.bp.fin.dto.PaymentVO;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinPayment;
import com.yundao.bp.fin.entity.FinPaymentAllocate;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinPaymentAllocateMapper;
import com.yundao.bp.fin.mapper.FinPaymentMapper;
import com.yundao.bp.fin.service.BillingService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 账单与收款实现。
 *
 * <p><b>金额口径（全部 2 位小数，HALF_UP）</b>：
 * <pre>
 *   应付金额 payable = 应收 - 减免 + 滞纳金 - 已收 - 已免
 *   收款可核销余额 = 收款金额 - 已核销
 * </pre>
 *
 * <p><b>核销上限</b>：{@code min(收款余额, 账单应付)}，避免超收或超核。
 */
@Service
public class BillingServiceImpl implements BillingService {

    private static final Logger log = LoggerFactory.getLogger(BillingServiceImpl.class);

    private final FinBillMapper billMapper;
    private final FinPaymentMapper paymentMapper;
    private final FinPaymentAllocateMapper allocateMapper;
    private final SnowflakeIdGenerator idGen;

    public BillingServiceImpl(FinBillMapper billMapper, FinPaymentMapper paymentMapper,
                              FinPaymentAllocateMapper allocateMapper,
                              SnowflakeIdGenerator idGen) {
        this.billMapper = billMapper;
        this.paymentMapper = paymentMapper;
        this.allocateMapper = allocateMapper;
        this.idGen = idGen;
    }

    // ==================== 账单 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BillVO createBill(BillCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        if (!cmd.periodEnd().isAfter(cmd.periodStart())) {
            throw BizException.paramInvalid("费用截止日必须晚于起始日");
        }
        BigDecimal bill = money(cmd.billAmount());
        BigDecimal discount = money(cmd.discountAmount());
        BigDecimal lateFee = money(cmd.lateFee());
        if (discount.compareTo(bill) > 0) {
            throw BizException.paramInvalid("减免金额不能大于应收金额");
        }
        BigDecimal payable = bill.subtract(discount).add(lateFee)
                .setScale(2, RoundingMode.HALF_UP);

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinBill e = new FinBill();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setBillNo("FB" + id);
        e.setOrgId(cmd.orgId());
        e.setContractId(cmd.contractId());
        e.setHouseId(cmd.houseId());
        e.setSpaceId(cmd.spaceId());
        e.setPersonId(cmd.personId());
        e.setPayerName(cmd.payerName());
        e.setPayerPhone(cmd.payerPhone());
        e.setFeeItemId(cmd.feeItemId());
        e.setBillPeriod(cmd.billPeriod());
        e.setPeriodStart(cmd.periodStart());
        e.setPeriodEnd(cmd.periodEnd());
        e.setBillAmount(bill);
        e.setDiscountAmount(discount);
        e.setLateFee(lateFee);
        e.setPaidAmount(money(null));
        e.setWaivedAmount(money(null));
        e.setPayableAmount(payable);
        e.setDueDate(cmd.dueDate() == null ? cmd.periodStart() : cmd.dueDate());
        e.setBillStatus(payable.compareTo(BigDecimal.ZERO) <= 0
                ? BillStatus.PAID.name() : BillStatus.UNPAID.name());
        e.setOverdueDays(0);
        e.setGenerateType(blankToNull(cmd.generateType()) == null ? "MANUAL" : cmd.generateType());
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateTime(now);
        billMapper.insert(e);
        return BillVO.from(e);
    }

    @Override
    public BillVO getBill(Long id) {
        return BillVO.from(requireBill(id));
    }

    @Override
    public PageResult<BillVO> pageBills(long pageNum, long pageSize, Long orgId, Long contractId,
                                        Long personId, String status, String keyword) {
        LambdaQueryWrapper<FinBill> qw = new LambdaQueryWrapper<FinBill>()
                .eq(orgId != null, FinBill::getOrgId, orgId)
                .eq(contractId != null, FinBill::getContractId, contractId)
                .eq(personId != null, FinBill::getPersonId, personId)
                .eq(status != null && !status.isBlank(), FinBill::getBillStatus, status)
                .orderByDesc(FinBill::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.like(FinBill::getBillNo, keyword);
        }
        IPage<FinBill> page = billMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<BillVO> rows = page.getRecords().stream().map(BillVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int scanOverdue() {
        List<FinBill> due = billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .in(FinBill::getBillStatus, List.of(BillStatus.UNPAID.name(),
                        BillStatus.PARTIAL.name()))
                .lt(FinBill::getDueDate, LocalDate.now()));
        int n = 0;
        for (FinBill e : due) {
            e.setBillStatus(BillStatus.OVERDUE.name());
            e.setOverdueDays((int) ChronoUnit.DAYS.between(e.getDueDate(), LocalDate.now()));
            e.setUpdateTime(LocalDateTime.now());
            billMapper.updateById(e);
            n++;
        }
        if (n > 0) {
            log.info("账单逾期扫描：{} 张账单置为 OVERDUE", n);
        }
        return n;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BillVO waiveBill(Long id, BigDecimal waiveAmount, String reason) {
        FinBill e = requireBill(id);
        BillStatus st = billStatusOf(e);
        if (st.isTerminal()) {
            throw BizException.stateConflict("账单已" + st.label() + "，不可减免");
        }
        BigDecimal waive = money(waiveAmount);
        BigDecimal payable = money(e.getPayableAmount());
        if (waive.compareTo(payable) > 0) {
            throw BizException.paramInvalid("减免金额不能大于应付金额 " + payable);
        }
        e.setWaivedAmount(money(e.getWaivedAmount()).add(waive));
        BigDecimal newPayable = payable.subtract(waive).setScale(2, RoundingMode.HALF_UP);
        e.setPayableAmount(newPayable);
        e.setBillStatus(newPayable.compareTo(BigDecimal.ZERO) <= 0
                ? BillStatus.WAIVED.name() : st.name());
        if (reason != null && !reason.isBlank()) {
            e.setRemark(reason);
        }
        e.setUpdateTime(LocalDateTime.now());
        billMapper.updateById(e);
        return BillVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BillVO cancelBill(Long id, String reason) {
        FinBill e = requireBill(id);
        if (money(e.getPaidAmount()).compareTo(BigDecimal.ZERO) > 0) {
            throw BizException.stateConflict("账单已有收款，不能作废（请走退款流程）");
        }
        transitionBill(e, BillStatus.CANCELLED);
        e.setRemark(reason);
        e.setUpdateTime(LocalDateTime.now());
        billMapper.updateById(e);
        return BillVO.from(e);
    }

    // ==================== 收款 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PaymentVO createPayment(PaymentCreateCmd cmd) {
        String tenantId = TenantContext.tenantId();
        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();

        FinPayment e = new FinPayment();
        e.setId(id);
        e.setTenantId(tenantId);
        e.setPaymentNo("FP" + id);
        e.setOrgId(cmd.orgId());
        e.setPersonId(cmd.personId());
        e.setPayerName(cmd.payerName());
        e.setPayAmount(money(cmd.payAmount()));
        e.setPayChannel(cmd.payChannel());
        e.setPayTime(now);
        e.setTradeNo(cmd.tradeNo());
        e.setPayStatus(PayStatus.SUCCESS.name());
        e.setReconcileStatus("UNRECONCILED");
        e.setReconciledAmount(money(null));
        e.setUnknownFlag(cmd.unknownFlag() == null ? 0 : cmd.unknownFlag());
        e.setOperatorId(cmd.operatorId());
        e.setRemark(cmd.remark());
        e.setCreateTime(now);
        paymentMapper.insert(e);
        return PaymentVO.from(e);
    }

    @Override
    public PaymentVO getPayment(Long id) {
        return PaymentVO.from(requirePayment(id));
    }

    @Override
    public PageResult<PaymentVO> pagePayments(long pageNum, long pageSize, Long orgId,
                                              Long personId, String status, String keyword) {
        LambdaQueryWrapper<FinPayment> qw = new LambdaQueryWrapper<FinPayment>()
                .eq(orgId != null, FinPayment::getOrgId, orgId)
                .eq(personId != null, FinPayment::getPersonId, personId)
                .eq(status != null && !status.isBlank(), FinPayment::getPayStatus, status)
                .orderByDesc(FinPayment::getId);
        if (keyword != null && !keyword.isBlank()) {
            qw.like(FinPayment::getPaymentNo, keyword);
        }
        IPage<FinPayment> page = paymentMapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<PaymentVO> rows = page.getRecords().stream().map(PaymentVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PaymentVO confirmPayment(Long id) {
        FinPayment e = requirePayment(id);
        if (!PayStatus.PENDING.name().equals(e.getPayStatus())) {
            throw BizException.stateConflict("仅待支付状态可确认成功");
        }
        e.setPayStatus(PayStatus.SUCCESS.name());
        e.setPayTime(LocalDateTime.now());
        e.setUpdateTime(LocalDateTime.now());
        paymentMapper.updateById(e);
        return PaymentVO.from(e);
    }

    // ==================== 核销 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BillVO allocate(Long paymentId, Long billId, BigDecimal amount) {
        FinPayment pay = requirePayment(paymentId);
        FinBill bill = requireBill(billId);

        if (!PayStatus.SUCCESS.name().equals(pay.getPayStatus())) {
            throw BizException.stateConflict("收款单未成功，不能核销");
        }
        BillStatus bs = billStatusOf(bill);
        if (!bs.isOutstanding()) {
            throw BizException.stateConflict("账单已" + bs.label() + "，无需核销");
        }

        BigDecimal req = amount == null ? money(bill.getPayableAmount()) : money(amount);
        if (req.compareTo(BigDecimal.ZERO) <= 0) {
            throw BizException.paramInvalid("核销金额必须大于 0");
        }
        BigDecimal payRemain = money(pay.getPayAmount())
                .subtract(money(pay.getReconciledAmount()));
        BigDecimal billPayable = money(bill.getPayableAmount());

        if (req.compareTo(payRemain) > 0) {
            throw BizException.paramInvalid(
                    "核销金额超过收款单可核销余额 " + payRemain);
        }
        if (req.compareTo(billPayable) > 0) {
            throw BizException.paramInvalid("核销金额超过账单应付金额 " + billPayable);
        }

        // 1) 写核销明细
        FinPaymentAllocate al = new FinPaymentAllocate();
        al.setId(idGen.nextId());
        al.setTenantId(pay.getTenantId());
        al.setPaymentId(paymentId);
        al.setBillId(billId);
        al.setAllocateAmount(req);
        al.setAllocateType("PAY");
        al.setCreateTime(LocalDateTime.now());
        allocateMapper.insert(al);

        // 2) 回写收款单
        BigDecimal newReconciled = money(pay.getReconciledAmount()).add(req)
                .setScale(2, RoundingMode.HALF_UP);
        pay.setReconciledAmount(newReconciled);
        BigDecimal payTotal = money(pay.getPayAmount());
        pay.setReconcileStatus(newReconciled.compareTo(payTotal) >= 0
                ? "RECONCILED" : "PARTIAL");
        pay.setUpdateTime(LocalDateTime.now());
        paymentMapper.updateById(pay);

        // 3) 回写账单
        BigDecimal newPaid = money(bill.getPaidAmount()).add(req)
                .setScale(2, RoundingMode.HALF_UP);
        BigDecimal newPayable = billPayable.subtract(req).setScale(2, RoundingMode.HALF_UP);
        bill.setPaidAmount(newPaid);
        bill.setPayableAmount(newPayable);
        bill.setBillStatus(newPayable.compareTo(BigDecimal.ZERO) <= 0
                ? BillStatus.PAID.name() : BillStatus.PARTIAL.name());
        bill.setUpdateTime(LocalDateTime.now());
        billMapper.updateById(bill);

        log.info("核销：收款单 {} → 账单 {} 金额 {}（账单剩余应付 {}）",
                pay.getPaymentNo(), bill.getBillNo(), req, newPayable);
        return BillVO.from(bill);
    }

    // ==================== 内部 ====================

    private FinBill requireBill(Long id) {
        FinBill e = billMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("账单");
        }
        return e;
    }

    private FinPayment requirePayment(Long id) {
        FinPayment e = paymentMapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("收款单");
        }
        return e;
    }

    private static BillStatus billStatusOf(FinBill e) {
        try {
            return BillStatus.valueOf(e.getBillStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("账单状态非法: " + e.getBillStatus());
        }
    }

    private static void transitionBill(FinBill e, BillStatus target) {
        BillStatus from = billStatusOf(e);
        if (from == target) {
            throw BizException.stateConflict("已处于 " + target.label() + " 状态");
        }
        if (!BillStatus.nextOf(from).contains(target)) {
            throw BizException.stateConflict(
                    "账单状态不允许从 " + from.label() + " 变更为 " + target.label());
        }
        e.setBillStatus(target.name());
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }

    private static String blankToNull(String s) {
        return (s == null || s.isBlank()) ? null : s;
    }
}
'''

FILES['fin/controller/BillingController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.PaymentCreateCmd;
import com.yundao.bp.fin.dto.PaymentVO;
import com.yundao.bp.fin.service.BillingService;
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
 * 账单与收款接口（BC-08 资金账务）。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class BillingController {

    private final BillingService billingService;

    public BillingController(BillingService billingService) {
        this.billingService = billingService;
    }

    // ---------- 账单 ----------

    @PostMapping("/bills")
    public R<BillVO> createBill(@Valid @RequestBody BillCreateCmd cmd) {
        return R.ok(billingService.createBill(cmd));
    }

    @GetMapping("/bills/{id}")
    public R<BillVO> getBill(@PathVariable Long id) {
        return R.ok(billingService.getBill(id));
    }

    @GetMapping("/bills")
    public R<PageResult<BillVO>> pageBills(@RequestParam(defaultValue = "1") long pageNum,
                                           @RequestParam(defaultValue = "20") long pageSize,
                                           @RequestParam(required = false) Long orgId,
                                           @RequestParam(required = false) Long contractId,
                                           @RequestParam(required = false) Long personId,
                                           @RequestParam(required = false) String status,
                                           @RequestParam(required = false) String keyword) {
        return R.ok(billingService.pageBills(pageNum, pageSize, orgId, contractId, personId,
                status, keyword));
    }

    /** 逾期扫描。 */
    @PostMapping("/bills/scan-overdue")
    public R<Integer> scanOverdue() {
        return R.ok(billingService.scanOverdue());
    }

    /** 减免。 */
    @PostMapping("/bills/{id}/waive")
    public R<BillVO> waive(@PathVariable Long id, @RequestBody WaiveCmd cmd) {
        return R.ok(billingService.waiveBill(id, cmd.waiveAmount(), cmd.reason()));
    }

    /** 作废。 */
    @PostMapping("/bills/{id}/cancel")
    public R<BillVO> cancel(@PathVariable Long id, @RequestBody(required = false) ReasonCmd cmd) {
        return R.ok(billingService.cancelBill(id, cmd == null ? null : cmd.reason()));
    }

    // ---------- 收款 ----------

    @PostMapping("/payments")
    public R<PaymentVO> createPayment(@Valid @RequestBody PaymentCreateCmd cmd) {
        return R.ok(billingService.createPayment(cmd));
    }

    @GetMapping("/payments/{id}")
    public R<PaymentVO> getPayment(@PathVariable Long id) {
        return R.ok(billingService.getPayment(id));
    }

    @GetMapping("/payments")
    public R<PageResult<PaymentVO>> pagePayments(@RequestParam(defaultValue = "1") long pageNum,
                                                 @RequestParam(defaultValue = "20") long pageSize,
                                                 @RequestParam(required = false) Long orgId,
                                                 @RequestParam(required = false) Long personId,
                                                 @RequestParam(required = false) String status,
                                                 @RequestParam(required = false) String keyword) {
        return R.ok(billingService.pagePayments(pageNum, pageSize, orgId, personId, status,
                keyword));
    }

    @PostMapping("/payments/{id}/confirm")
    public R<PaymentVO> confirm(@PathVariable Long id) {
        return R.ok(billingService.confirmPayment(id));
    }

    /** 核销：把收款单的钱核到账单上。 */
    @PostMapping("/payments/{paymentId}/allocate")
    public R<BillVO> allocate(@PathVariable Long paymentId, @RequestBody AllocateCmd cmd) {
        return R.ok(billingService.allocate(paymentId, cmd.billId(), cmd.amount()));
    }

    public record WaiveCmd(BigDecimal waiveAmount, String reason) {
    }

    public record ReasonCmd(String reason) {
    }

    public record AllocateCmd(Long billId, BigDecimal amount) {
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
