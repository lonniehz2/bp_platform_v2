package com.yundao.bp.fin.service.impl;

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
