package com.yundao.bp.fin.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.entity.FinBill;
import com.yundao.bp.fin.mapper.FinBillMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.YearMonth;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 跨月历史账单迁移。
 *
 * <p>只自动拆分「未收款、无减免」的账单；已收款/有补贴减免的账单跳过，需人工冲正，
 * 避免自动拆分破坏已核销资金和补贴流水。
 */
@Service
public class BillMigrationService {

    private final FinBillMapper billMapper;
    private final SnowflakeIdGenerator idGen;
    private final org.springframework.jdbc.core.JdbcTemplate jdbc;

    public BillMigrationService(FinBillMapper billMapper, SnowflakeIdGenerator idGen,
                                org.springframework.jdbc.core.JdbcTemplate jdbc) {
        this.billMapper = billMapper;
        this.idGen = idGen;
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> preview() {
        List<Map<String, Object>> out = new ArrayList<>();
        for (FinBill b : candidates()) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", b.getId());
            m.put("billNo", b.getBillNo());
            m.put("periodStart", b.getPeriodStart());
            m.put("periodEnd", b.getPeriodEnd());
            m.put("billAmount", b.getBillAmount());
            m.put("waivedAmount", b.getWaivedAmount());
            m.put("paidAmount", b.getPaidAmount());
            m.put("billStatus", b.getBillStatus());
            m.put("autoSplittable", isSplittable(b));
            m.put("reason", isSplittable(b) ? null : "已收款或有减免，需人工冲正");
            if (isSplittable(b)) {
                m.put("parts", buildParts(b, false));
            }
            out.add(m);
        }
        return out;
    }

    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> splitUnpaid(boolean dryRun) {
        int split = 0;
        int skipped = 0;
        List<String> errors = new ArrayList<>();
        for (FinBill b : candidates()) {
            if (!isSplittable(b)) {
                skipped++;
                continue;
            }
            if (dryRun) {
                split++;
                continue;
            }
            try {
                List<FinBill> parts = buildParts(b, true);
                for (FinBill p : parts) {
                    billMapper.insert(p);
                }
                String newNos = parts.stream().map(FinBill::getBillNo)
                        .collect(java.util.stream.Collectors.joining(" / "));
                jdbc.update("update bp_fin_bill set is_deleted = 1, remark = ?, "
                                + "update_time = now() where id = ?",
                        appendRemark(b.getRemark(), "跨月账单拆分：" + newNos), b.getId());
                split++;
            } catch (Exception ex) {
                skipped++;
                errors.add(b.getBillNo() + "：" + ex.getMessage());
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("dryRun", dryRun);
        out.put("split", split);
        out.put("skipped", skipped);
        out.put("errors", errors);
        return out;
    }

    private List<FinBill> candidates() {
        return billMapper.selectList(new LambdaQueryWrapper<FinBill>()
                .eq(FinBill::getIsDeleted, 0)
                .ne(FinBill::getBillStatus, "CANCELLED")
                .apply("date_format(period_start,'%Y-%m') <> date_format(period_end,'%Y-%m')")
                .orderByAsc(FinBill::getId));
    }

    private static boolean isSplittable(FinBill b) {
        return money(b.getPaidAmount()).compareTo(BigDecimal.ZERO) == 0
                && money(b.getWaivedAmount()).compareTo(BigDecimal.ZERO) == 0;
    }

    private List<FinBill> buildParts(FinBill old, boolean createIds) {
        LocalDate start = old.getPeriodStart();
        LocalDate end = old.getPeriodEnd();
        long totalDays = ChronoUnit.DAYS.between(start, end) + 1;
        List<FinBill> parts = new java.util.ArrayList<>();
        BigDecimal amountUsed = BigDecimal.ZERO;
        BigDecimal discountUsed = BigDecimal.ZERO;
        BigDecimal lateUsed = BigDecimal.ZERO;
        LocalDate cursor = start;
        while (!cursor.isAfter(end)) {
            LocalDate monthEnd = cursor.with(java.time.temporal.TemporalAdjusters.lastDayOfMonth());
            LocalDate segEnd = monthEnd.isAfter(end) ? end : monthEnd;
            long days = ChronoUnit.DAYS.between(cursor, segEnd) + 1;
            boolean last = segEnd.equals(end);
            BigDecimal amount = last
                    ? money(old.getBillAmount()).subtract(amountUsed)
                    : splitAmount(old.getBillAmount(), days, totalDays);
            BigDecimal discount = last
                    ? money(old.getDiscountAmount()).subtract(discountUsed)
                    : splitAmount(old.getDiscountAmount(), days, totalDays);
            BigDecimal late = last
                    ? money(old.getLateFee()).subtract(lateUsed)
                    : splitAmount(old.getLateFee(), days, totalDays);
            amountUsed = amountUsed.add(amount);
            discountUsed = discountUsed.add(discount);
            lateUsed = lateUsed.add(late);
            parts.add(copy(old, createIds, cursor, segEnd, amount, discount, late, days));
            cursor = segEnd.plusDays(1);
        }
        return parts;
    }

    private FinBill copy(FinBill old, boolean createIds, LocalDate start, LocalDate end,
                         BigDecimal amount, BigDecimal discount, BigDecimal late, long days) {
        FinBill b = new FinBill();
        if (createIds) {
            long id = idGen.nextId();
            b.setId(id);
            b.setBillNo("FB" + id);
        }
        b.setTenantId(old.getTenantId());
        b.setOrgId(old.getOrgId());
        b.setContractId(old.getContractId());
        b.setHouseId(old.getHouseId());
        b.setSpaceId(old.getSpaceId());
        b.setPersonId(old.getPersonId());
        b.setPayerName(old.getPayerName());
        b.setPayerPhone(old.getPayerPhone());
        b.setFeeItemId(old.getFeeItemId());
        b.setBillPeriod(YearMonth.from(start).toString());
        b.setPeriodStart(start);
        b.setPeriodEnd(end);
        b.setSettlementDate(end);
        b.setBillAmount(amount);
        b.setDiscountAmount(discount);
        b.setLateFee(late);
        b.setPaidAmount(money(null));
        b.setWaivedAmount(money(null));
        b.setSubsidyAmount(old.getSubsidyAmount());
        b.setPayableAmount(amount.subtract(discount).add(late)
                .setScale(2, RoundingMode.HALF_UP));
        b.setDueDate(old.getDueDate());
        b.setBillDate(LocalDate.now());
        b.setBillStatus(money(amount).compareTo(BigDecimal.ZERO) <= 0 ? "PAID" : "UNPAID");
        b.setOverdueDays(0);
        b.setGenerateType(old.getGenerateType());
        b.setRemark(appendRemark(old.getRemark(), "跨月拆分"));
        b.setRuleId(old.getRuleId());
        b.setRuleVersion(old.getRuleVersion());
        b.setRuleSnapshot(old.getRuleSnapshot());
        b.setBillingQuantity(old.getBillingQuantity());
        b.setBillingDays((int) days);
        b.setProrationMonths(BigDecimal.valueOf(days)
                .divide(BigDecimal.valueOf(start.lengthOfMonth()), 6, RoundingMode.HALF_UP));
        b.setQuantityUnit(old.getQuantityUnit());
        b.setQuantitySource(old.getQuantitySource());
        b.setTierDetail(old.getTierDetail());
        b.setUnitPriceSnapshot(old.getUnitPriceSnapshot());
        b.setPriceSource(old.getPriceSource());
        b.setIsDeleted(0);
        b.setCreateTime(LocalDateTime.now());
        return b;
    }

    private static BigDecimal splitAmount(BigDecimal total, long days, long totalDays) {
        if (total == null || total.compareTo(BigDecimal.ZERO) == 0 || totalDays <= 0) {
            return money(null);
        }
        return total.multiply(BigDecimal.valueOf(days))
                .divide(BigDecimal.valueOf(totalDays), 2, RoundingMode.HALF_UP);
    }

    private static String appendRemark(String old, String suffix) {
        String base = old == null ? "" : old;
        return base.isBlank() ? suffix : base + "；" + suffix;
    }

    private static BigDecimal money(BigDecimal v) {
        return (v == null ? BigDecimal.ZERO : v).setScale(2, RoundingMode.HALF_UP);
    }
}
