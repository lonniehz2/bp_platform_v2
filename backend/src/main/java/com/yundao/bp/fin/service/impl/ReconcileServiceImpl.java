package com.yundao.bp.fin.service.impl;

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
// Bean 名显式指定：与另一模块的同名实现类区分，避免运行期 BeanDefinition 冲突
@Service("finReconcileServiceImpl")
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
