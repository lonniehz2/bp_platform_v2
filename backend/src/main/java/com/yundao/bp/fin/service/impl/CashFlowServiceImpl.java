package com.yundao.bp.fin.service.impl;

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
        e.setBalanceAfter(balanceAfter(now).add(signed)
                .setScale(2, RoundingMode.HALF_UP));
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
