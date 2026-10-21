# -*- coding: utf-8 -*-
"""生成 fin 收尾：催缴/对账/流水（服务+控制器）+ 自动记流水"""
import io, os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = {}

FILES['fin/service/CashFlowService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.constant.FlowBizType;
import com.yundao.bp.fin.constant.FlowType;
import com.yundao.bp.fin.dto.CashFlowRecordCmd;
import com.yundao.bp.fin.dto.CashFlowVO;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 资金流水服务。
 *
 * <p>业务侧（收款确认、退款打款、补贴发放）通过 {@code record} 自动写入，
 * 金额带符号：收入为正、支出为负。
 */
public interface CashFlowService {

    /** 自动记流水（供业务模块调用）。 */
    CashFlowVO record(FlowType type, FlowBizType bizType, Long bizId, BigDecimal amount,
                      String remark);

    /** 手工记流水。 */
    CashFlowVO recordManual(CashFlowRecordCmd cmd);

    CashFlowVO get(Long id);

    PageResult<CashFlowVO> page(long pageNum, long pageSize, String flowType, String bizType,
                                Long bizId, LocalDate dateFrom, LocalDate dateTo);

    /** 期间净流入（收入合计 - 支出合计）。 */
    BigDecimal netAmount(LocalDate dateFrom, LocalDate dateTo);

    /** 校验流水（人工核对账实一致性）。 */
    CashFlowVO verify(Long id, String remark);
}
'''

FILES['fin/service/impl/CashFlowServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.FlowBizType;
import com.yundao.bp.fin.constant.FlowType;
import com.yundao.bp.fin.constant.VerifyStatus;
import com.yundao.bp.fin.dto.CashFlowRecordCmd;
import com.yundao.bp.fin.dto.CashFlowVO;
import com.yundao.bp.fin.entity.FinCashFlow;
import com.yundao.bp.fin.mapper.FinCashFlowMapper;
import com.yundao.bp.fin.service.CashFlowService;
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
 * 资金流水实现。
 */
@Service
public class CashFlowServiceImpl implements CashFlowService {

    private static final Logger log = LoggerFactory.getLogger(CashFlowServiceImpl.class);

    private final FinCashFlowMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public CashFlowServiceImpl(FinCashFlowMapper mapper, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CashFlowVO record(FlowType type, FlowBizType bizType, Long bizId, BigDecimal amount,
                             String remark) {
        if (type == null || bizType == null || amount == null) {
            throw BizException.paramInvalid("流水类型/业务类型/金额不能为空");
        }
        BigDecimal abs = amount.abs().setScale(2, RoundingMode.HALF_UP);
        if (abs.compareTo(BigDecimal.ZERO) == 0) {
            throw BizException.paramInvalid("流水金额不能为 0");
        }
        // 收入为正，支出/调整按传入方向（支出取负）
        BigDecimal signed = type == FlowType.EXPENSE ? abs.negate() : abs;

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinCashFlow e = new FinCashFlow();
        e.setId(id);
        e.setTenantId(TenantContext.tenantId());
        e.setFlowNo("FC" + id);
        e.setFlowType(type.name());
        e.setBizType(bizType.name());
        e.setBizId(bizId);
        e.setAmount(signed);
        e.setBalanceAfter(balanceAfter(now));
        e.setFlowTime(now);
        e.setVerifyStatus(VerifyStatus.UNVERIFIED.name());
        e.setVerifyRemark(remark);
        e.setCreateTime(now);
        mapper.insert(e);
        log.debug("资金流水 {} {} {} 金额 {}（biz={}:{}）", e.getFlowNo(), type.name(),
                bizType.name(), signed, bizType.name(), bizId);
        return CashFlowVO.from(e);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CashFlowVO recordManual(CashFlowRecordCmd cmd) {
        FlowType type;
        try {
            type = FlowType.valueOf(cmd.flowType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("流水类型不合法: " + cmd.flowType());
        }
        FlowBizType bizType = FlowBizType.OTHER;
        if (cmd.bizType() != null && !cmd.bizType().isBlank()) {
            try {
                bizType = FlowBizType.valueOf(cmd.bizType());
            } catch (IllegalArgumentException e) {
                throw BizException.paramInvalid("业务类型不合法: " + cmd.bizType());
            }
        }
        return record(type, bizType, cmd.bizId(), cmd.amount(), cmd.remark());
    }

    @Override
    public CashFlowVO get(Long id) {
        FinCashFlow e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("资金流水");
        }
        return CashFlowVO.from(e);
    }

    @Override
    public PageResult<CashFlowVO> page(long pageNum, long pageSize, String flowType,
                                       String bizType, Long bizId, LocalDate dateFrom,
                                       LocalDate dateTo) {
        LambdaQueryWrapper<FinCashFlow> qw = new LambdaQueryWrapper<FinCashFlow>()
                .eq(flowType != null && !flowType.isBlank(), FinCashFlow::getFlowType, flowType)
                .eq(bizType != null && !bizType.isBlank(), FinCashFlow::getBizType, bizType)
                .eq(bizId != null, FinCashFlow::getBizId, bizId)
                .orderByDesc(FinCashFlow::getFlowTime)
                .orderByDesc(FinCashFlow::getId);
        if (dateFrom != null) {
            qw.ge(FinCashFlow::getFlowTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(FinCashFlow::getFlowTime, dateTo.plusDays(1).atStartOfDay());
        }
        IPage<FinCashFlow> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<CashFlowVO> rows = page.getRecords().stream().map(CashFlowVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public BigDecimal netAmount(LocalDate dateFrom, LocalDate dateTo) {
        LambdaQueryWrapper<FinCashFlow> qw = new LambdaQueryWrapper<>();
        if (dateFrom != null) {
            qw.ge(FinCashFlow::getFlowTime, dateFrom.atStartOfDay());
        }
        if (dateTo != null) {
            qw.lt(FinCashFlow::getFlowTime, dateTo.plusDays(1).atStartOfDay());
        }
        List<FinCashFlow> list = mapper.selectList(qw);
        BigDecimal sum = BigDecimal.ZERO;
        for (FinCashFlow f : list) {
            sum = sum.add(f.getAmount() == null ? BigDecimal.ZERO : f.getAmount());
        }
        return sum.setScale(2, RoundingMode.HALF_UP);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public CashFlowVO verify(Long id, String remark) {
        FinCashFlow e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("资金流水");
        }
        e.setVerifyStatus(VerifyStatus.VERIFIED.name());
        e.setVerifyRemark(remark);
        mapper.updateById(e);
        return CashFlowVO.from(e);
    }

    /** 变动后余额 = 此前所有流水之和 + 本次（简化口径，未做账户余额表）。 */
    private BigDecimal balanceAfter(LocalDateTime now) {
        List<FinCashFlow> before = mapper.selectList(new LambdaQueryWrapper<FinCashFlow>()
                .lt(FinCashFlow::getFlowTime, now));
        BigDecimal sum = BigDecimal.ZERO;
        for (FinCashFlow f : before) {
            sum = sum.add(f.getAmount() == null ? BigDecimal.ZERO : f.getAmount());
        }
        return sum.setScale(2, RoundingMode.HALF_UP);
    }
}
'''

FILES['fin/service/DunningService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.DunningCreateCmd;
import com.yundao.bp.fin.dto.DunningVO;
import java.time.LocalDate;
import java.util.List;

/**
 * 催缴记录服务。
 */
public interface DunningService {

    /** 登记一次催缴（自动递增催缴次数）。 */
    DunningVO create(DunningCreateCmd cmd);

    DunningVO get(Long id);

    /** 按账单查催缴历史。 */
    List<DunningVO> listByBill(Long billId);

    PageResult<DunningVO> page(long pageNum, long pageSize, Long billId, Long personId,
                               String dunningType);

    /** 扫描逾期账单，返回需要催缴的账单建议（不落库）。 */
    List<DunningSuggestion> scanNeedDunning(int minOverdueDays, int maxDunningTimes);

    /** 催缴建议。 */
    record DunningSuggestion(Long billId, String billNo, Long contractId, Long personId,
                             String payerName, java.math.BigDecimal payableAmount,
                             int overdueDays, int dunningTimes, LocalDate dueDate) {
    }
}
'''

FILES['fin/service/impl/DunningServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.constant.DunningType;
import com.yundao.bp.fin.dto.DunningCreateCmd;
import com.yundao.bp.fin.dto.DunningVO;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.entity.FinDunningRecord;
import com.yundao.bp.fin.mapper.FinBillMapper;
import com.yundao.bp.fin.mapper.FinDunningRecordMapper;
import com.yundao.bp.fin.service.DunningService;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 催缴记录实现。
 */
@Service
public class DunningServiceImpl implements DunningService {

    private static final Logger log = LoggerFactory.getLogger(DunningServiceImpl.class);

    private final FinDunningRecordMapper mapper;
    private final FinBillMapper billMapper;
    private final SnowflakeIdGenerator idGen;

    public DunningServiceImpl(FinDunningRecordMapper mapper, FinBillMapper billMapper,
                              SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.billMapper = billMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public DunningVO create(DunningCreateCmd cmd) {
        FinBill bill = billMapper.selectById(cmd.billId());
        if (bill == null) {
            throw BizException.notFound("账单");
        }
        BillStatus bs;
        try {
            bs = BillStatus.valueOf(bill.getBillStatus());
        } catch (IllegalArgumentException e) {
            throw BizException.stateConflict("账单状态非法: " + bill.getBillStatus());
        }
        if (!bs.isOutstanding()) {
            throw BizException.stateConflict("账单已" + bs.label() + "，无需催缴");
        }
        DunningType type;
        try {
            type = DunningType.valueOf(cmd.dunningType());
        } catch (IllegalArgumentException e) {
            throw BizException.paramInvalid("催缴方式不合法: " + cmd.dunningType());
        }
        // 上门/电话建议留证，便于举证
        if (type.needsEvidence()
                && (cmd.evidenceUrl() == null || cmd.evidenceUrl().isBlank())) {
            log.warn("催缴方式 {} 未提供佐证（建议上传照片/通话记录），账单 {}", type.label(),
                    bill.getBillNo());
        }

        // 催缴次数自动递增
        Long cnt = mapper.selectCount(new LambdaQueryWrapper<FinDunningRecord>()
                .eq(FinDunningRecord::getBillId, cmd.billId()));
        int no = (cnt == null ? 0 : cnt.intValue()) + 1;

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinDunningRecord e = new FinDunningRecord();
        e.setId(id);
        e.setTenantId(TenantContext.tenantId());
        e.setBillId(cmd.billId());
        e.setPersonId(cmd.personId() == null ? bill.getPersonId() : cmd.personId());
        e.setDunningNo(no);
        e.setDunningType(type.name());
        e.setDunningTime(now);
        e.setDunningContent(cmd.dunningContent());
        e.setDunningResult(cmd.dunningResult());
        e.setEvidenceUrl(cmd.evidenceUrl());
        e.setOperatorId(cmd.operatorId());
        e.setCreateTime(now);
        mapper.insert(e);
        log.info("催缴登记：账单 {} 第 {} 次（{}）", bill.getBillNo(), no, type.label());
        return DunningVO.from(e);
    }

    @Override
    public DunningVO get(Long id) {
        FinDunningRecord e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("催缴记录");
        }
        return DunningVO.from(e);
    }

    @Override
    public List<DunningVO> listByBill(Long billId) {
        return mapper.selectList(new LambdaQueryWrapper<FinDunningRecord>()
                        .eq(FinDunningRecord::getBillId, billId)
                        .orderByAsc(FinDunningRecord::getDunningNo))
                .stream().map(DunningVO::from).toList();
    }

    @Override
    public PageResult<DunningVO> page(long pageNum, long pageSize, Long billId, Long personId,
                                      String dunningType) {
        LambdaQueryWrapper<FinDunningRecord> qw = new LambdaQueryWrapper<FinDunningRecord>()
                .eq(billId != null, FinDunningRecord::getBillId, billId)
                .eq(personId != null, FinDunningRecord::getPersonId, personId)
                .eq(dunningType != null && !dunningType.isBlank(),
                        FinDunningRecord::getDunningType, dunningType)
                .orderByDesc(FinDunningRecord::getId);
        IPage<FinDunningRecord> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<DunningVO> rows = page.getRecords().stream().map(DunningVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    public List<DunningSuggestion> scanNeedDunning(int minOverdueDays, int maxDunningTimes) {
        LocalDate today = LocalDate.now();
        List<FinBill> overdue = billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .in(FinBill::getBillStatus, List.of(BillStatus.UNPAID.name(),
                        BillStatus.PARTIAL.name(), BillStatus.OVERDUE.name()))
                .lt(FinBill::getDueDate, today));

        // 一次性取出这些账单的催缴次数
        Map<Long, Integer> counts = new HashMap<>();
        if (!overdue.isEmpty()) {
            List<Long> ids = overdue.stream().map(FinBill::getId).toList();
            List<FinDunningRecord> recs = mapper.selectList(
                    new LambdaQueryWrapper<FinDunningRecord>()
                            .in(FinDunningRecord::getBillId, ids));
            for (FinDunningRecord r : recs) {
                counts.merge(r.getBillId(), 1, Integer::sum);
            }
        }

        List<DunningSuggestion> out = new ArrayList<>();
        for (FinBill b : overdue) {
            int days = (int) ChronoUnit.DAYS.between(b.getDueDate(), today);
            if (days < minOverdueDays) {
                continue;
            }
            int times = counts.getOrDefault(b.getId(), 0);
            if (times > maxDunningTimes) {
                continue;
            }
            BigDecimal payable = b.getPayableAmount() == null
                    ? BigDecimal.ZERO : b.getPayableAmount();
            out.add(new DunningSuggestion(b.getId(), b.getBillNo(), b.getContractId(),
                    b.getPersonId(), b.getPayerName(), payable, days, times, b.getDueDate()));
        }
        out.sort((a, b) -> Integer.compare(b.overdueDays(), a.overdueDays()));
        return out;
    }
}
'''

FILES['fin/service/ReconcileService.java'] = '''package com.yundao.bp.fin.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.fin.dto.ReconcileCreateCmd;
import com.yundao.bp.fin.dto.ReconcileVO;
import java.time.LocalDate;

/**
 * 财务对账服务。
 */
public interface ReconcileService {

    /** 发起对账（自动汇总系统金额，计算差异）。 */
    ReconcileVO create(ReconcileCreateCmd cmd);

    ReconcileVO get(Long id);

    PageResult<ReconcileVO> page(long pageNum, long pageSize, LocalDate dateFrom, LocalDate dateTo,
                                 String reconcileType, String status);

    /** 处理差异（标记已处理）。 */
    ReconcileVO handle(Long id, String remark);
}
'''

FILES['fin/service/impl/ReconcileServiceImpl.java'] = '''package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.constant.PayStatus;
import com.yundao.bp.fin.constant.ReconcileStatus;
import com.yundao.bp.fin.dto.ReconcileCreateCmd;
import com.yundao.bp.fin.dto.ReconcileVO;
import com.yundao.bp.fin.entity.FinPayment;
import com.yundao.bp.fin.entity.FinReconcile;
import com.yundao.bp.fin.mapper.FinPaymentMapper;
import com.yundao.bp.fin.mapper.FinReconcileMapper;
import com.yundao.bp.fin.service.ReconcileService;
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
 * 财务对账实现。
 *
 * <p><b>系统金额口径</b>：当日该渠道 {@code pay_status=SUCCESS} 的收款单金额合计。
 * 差异 = 系统金额 − 渠道金额。
 */
@Service
public class ReconcileServiceImpl implements ReconcileService {

    private static final Logger log = LoggerFactory.getLogger(ReconcileServiceImpl.class);

    private final FinReconcileMapper mapper;
    private final FinPaymentMapper paymentMapper;
    private final SnowflakeIdGenerator idGen;

    public ReconcileServiceImpl(FinReconcileMapper mapper, FinPaymentMapper paymentMapper,
                                SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.paymentMapper = paymentMapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ReconcileVO create(ReconcileCreateCmd cmd) {
        // 系统金额：不传则按当日该渠道成功收款汇总
        BigDecimal system = cmd.systemAmount();
        if (system == null) {
            system = sumSystemAmount(cmd.reconcileDate(), cmd.payChannel());
        }
        system = money(system);
        BigDecimal channel = money(cmd.channelAmount());
        BigDecimal diff = system.subtract(channel).setScale(2, RoundingMode.HALF_UP);

        long id = idGen.nextId();
        LocalDateTime now = LocalDateTime.now();
        FinReconcile e = new FinReconcile();
        e.setId(id);
        e.setTenantId(TenantContext.tenantId());
        e.setReconcileNo("FRC" + id);
        e.setReconcileDate(cmd.reconcileDate());
        e.setReconcileType(cmd.reconcileType());
        e.setPayChannel(cmd.payChannel());
        e.setSystemAmount(system);
        e.setChannelAmount(channel);
        e.setDiffAmount(diff);
        e.setDiffCount(cmd.diffCount() == null ? 0 : cmd.diffCount());
        e.setReconcileStatus(diff.compareTo(BigDecimal.ZERO) == 0
                ? ReconcileStatus.MATCHED.name() : ReconcileStatus.DIFF.name());
        e.setDiffDetailUrl(cmd.diffDetailUrl());
        e.setCreateTime(now);
        e.setUpdateTime(now);
        mapper.insert(e);

        if (diff.compareTo(BigDecimal.ZERO) != 0) {
            log.warn("对账差异：{} 渠道 {} 系统 {} 渠道 {} 差异 {}",
                    cmd.reconcileDate(), cmd.payChannel(), system, channel, diff);
        } else {
            log.info("对账一致：{} 渠道 {} 金额 {}", cmd.reconcileDate(),
                    cmd.payChannel(), system);
        }
        return ReconcileVO.from(e);
    }

    @Override
    public ReconcileVO get(Long id) {
        FinReconcile e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("对账记录");
        }
        return ReconcileVO.from(e);
    }

    @Override
    public PageResult<ReconcileVO> page(long pageNum, long pageSize, LocalDate dateFrom,
                                        LocalDate dateTo, String reconcileType, String status) {
        LambdaQueryWrapper<FinReconcile> qw = new LambdaQueryWrapper<FinReconcile>()
                .eq(reconcileType != null && !reconcileType.isBlank(),
                        FinReconcile::getReconcileType, reconcileType)
                .eq(status != null && !status.isBlank(),
                        FinReconcile::getReconcileStatus, status)
                .ge(dateFrom != null, FinReconcile::getReconcileDate, dateFrom)
                .le(dateTo != null, FinReconcile::getReconcileDate, dateTo)
                .orderByDesc(FinReconcile::getId);
        IPage<FinReconcile> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        List<ReconcileVO> rows = page.getRecords().stream().map(ReconcileVO::from).toList();
        return PageResult.of(page.getTotal(), pageNum, pageSize, rows);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public ReconcileVO handle(Long id, String remark) {
        FinReconcile e = mapper.selectById(id);
        if (e == null) {
            throw BizException.notFound("对账记录");
        }
        ReconcileStatus st;
        try {
            st = ReconcileStatus.valueOf(e.getReconcileStatus());
        } catch (IllegalArgumentException ex) {
            throw BizException.stateConflict("对账状态非法: " + e.getReconcileStatus());
        }
        if (st == ReconcileStatus.HANDLED) {
            throw BizException.stateConflict("该对账已处理");
        }
        if (st == ReconcileStatus.MATCHED) {
            throw BizException.stateConflict("账实相符，无需处理");
        }
        e.setReconcileStatus(ReconcileStatus.HANDLED.name());
        e.setDiffDetailUrl(remark == null ? e.getDiffDetailUrl() : remark);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        return ReconcileVO.from(e);
    }

    /** 汇总当日某渠道的成功收款金额。 */
    private BigDecimal sumSystemAmount(LocalDate date, String channel) {
        LambdaQueryWrapper<FinPayment> qw = new LambdaQueryWrapper<FinPayment>()
                .eq(FinPayment::getPayStatus, PayStatus.SUCCESS.name())
                .ge(FinPayment::getPayTime, date.atStartOfDay())
                .lt(FinPayment::getPayTime, date.plusDays(1).atStartOfDay());
        if (channel != null && !channel.isBlank()) {
            qw.eq(FinPayment::getPayChannel, channel);
        }
        List<FinPayment> list = paymentMapper.selectList(qw);
        BigDecimal sum = BigDecimal.ZERO;
        for (FinPayment p : list) {
            sum = sum.add(p.getPayAmount() == null ? BigDecimal.ZERO : p.getPayAmount());
        }
        return sum;
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
'''

FILES['fin/controller/FinLedgerController.java'] = '''package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.CashFlowRecordCmd;
import com.yundao.bp.fin.dto.CashFlowVO;
import com.yundao.bp.fin.dto.DunningCreateCmd;
import com.yundao.bp.fin.dto.DunningVO;
import com.yundao.bp.fin.dto.ReconcileCreateCmd;
import com.yundao.bp.fin.dto.ReconcileVO;
import com.yundao.bp.fin.service.CashFlowService;
import com.yundao.bp.fin.service.DunningService;
import com.yundao.bp.fin.service.ReconcileService;
import jakarta.validation.Valid;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 催缴 / 对账 / 资金流水接口（BC-08 资金账务收尾）。
 */
@RestController
@RequestMapping("/api/v1/fin")
public class FinLedgerController {

    private final DunningService dunningService;
    private final ReconcileService reconcileService;
    private final CashFlowService cashFlowService;

    public FinLedgerController(DunningService dunningService,
                               ReconcileService reconcileService,
                               CashFlowService cashFlowService) {
        this.dunningService = dunningService;
        this.reconcileService = reconcileService;
        this.cashFlowService = cashFlowService;
    }

    // ==================== 催缴 ====================

    /** 逾期账单催缴建议。 */
    @GetMapping("/dunnings/scan")
    public R<List<DunningService.DunningSuggestion>> scanDunning(
            @RequestParam(defaultValue = "3") int minOverdueDays,
            @RequestParam(defaultValue = "3") int maxDunningTimes) {
        return R.ok(dunningService.scanNeedDunning(minOverdueDays, maxDunningTimes));
    }

    @PostMapping("/dunnings")
    public R<DunningVO> createDunning(@Valid @RequestBody DunningCreateCmd cmd) {
        return R.ok(dunningService.create(cmd));
    }

    @GetMapping("/dunnings/{id}")
    public R<DunningVO> getDunning(@PathVariable Long id) {
        return R.ok(dunningService.get(id));
    }

    @GetMapping("/dunnings")
    public R<PageResult<DunningVO>> pageDunning(@RequestParam(defaultValue = "1") long pageNum,
                                                @RequestParam(defaultValue = "20") long pageSize,
                                                @RequestParam(required = false) Long billId,
                                                @RequestParam(required = false) Long personId,
                                                @RequestParam(required = false) String dunningType) {
        return R.ok(dunningService.page(pageNum, pageSize, billId, personId, dunningType));
    }

    @GetMapping("/dunnings/by-bill/{billId}")
    public R<List<DunningVO>> dunningByBill(@PathVariable Long billId) {
        return R.ok(dunningService.listByBill(billId));
    }

    // ==================== 对账 ====================

    @PostMapping("/reconciles")
    public R<ReconcileVO> createReconcile(@Valid @RequestBody ReconcileCreateCmd cmd) {
        return R.ok(reconcileService.create(cmd));
    }

    @GetMapping("/reconciles/{id}")
    public R<ReconcileVO> getReconcile(@PathVariable Long id) {
        return R.ok(reconcileService.get(id));
    }

    @GetMapping("/reconciles")
    public R<PageResult<ReconcileVO>> pageReconcile(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo,
            @RequestParam(required = false) String reconcileType,
            @RequestParam(required = false) String status) {
        return R.ok(reconcileService.page(pageNum, pageSize, dateFrom, dateTo, reconcileType,
                status));
    }

    /** 处理对账差异。 */
    @PostMapping("/reconciles/{id}/handle")
    public R<ReconcileVO> handleReconcile(@PathVariable Long id,
                                          @RequestBody(required = false) RemarkCmd cmd) {
        return R.ok(reconcileService.handle(id, cmd == null ? null : cmd.remark()));
    }

    // ==================== 资金流水 ====================

    /** 手工登记流水。 */
    @PostMapping("/cash-flows")
    public R<CashFlowVO> recordFlow(@Valid @RequestBody CashFlowRecordCmd cmd) {
        return R.ok(cashFlowService.recordManual(cmd));
    }

    @GetMapping("/cash-flows/{id}")
    public R<CashFlowVO> getFlow(@PathVariable Long id) {
        return R.ok(cashFlowService.get(id));
    }

    @GetMapping("/cash-flows")
    public R<PageResult<CashFlowVO>> pageFlow(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) String flowType,
            @RequestParam(required = false) String bizType,
            @RequestParam(required = false) Long bizId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(cashFlowService.page(pageNum, pageSize, flowType, bizType, bizId,
                dateFrom, dateTo));
    }

    /** 期间净流入。 */
    @GetMapping("/cash-flows/net")
    public R<BigDecimal> netFlow(
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateFrom,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate dateTo) {
        return R.ok(cashFlowService.netAmount(dateFrom, dateTo));
    }

    /** 校验流水。 */
    @PostMapping("/cash-flows/{id}/verify")
    public R<CashFlowVO> verifyFlow(@PathVariable Long id,
                                     @RequestBody(required = false) RemarkCmd cmd) {
        return R.ok(cashFlowService.verify(id, cmd == null ? null : cmd.remark()));
    }

    public record RemarkCmd(String remark) {
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
