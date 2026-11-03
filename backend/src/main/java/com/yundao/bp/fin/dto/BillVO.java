package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.BillStatus;
import com.yundao.bp.fin.entity.FinBill;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 账单视图（含逾期派生）。
 */
public record BillVO(
        Long id,
        String billNo,
        Long orgId,
        Long contractId,
        Long houseId,
        Long personId,
        String payerName,
        Long feeItemId,
        String billPeriod,
        LocalDate periodStart,
        LocalDate periodEnd,
        LocalDate settlementDate,
        BigDecimal billAmount,
        BigDecimal unitPriceSnapshot,
        String priceSource,
        BigDecimal discountAmount,
        BigDecimal lateFee,
        BigDecimal paidAmount,
        BigDecimal waivedAmount,
        BigDecimal payableAmount,
        LocalDate dueDate,
        LocalDate billDate,
        String billStatus,
        String billStatusLabel,
        Integer overdueDays,
        /** 派生：是否逾期未缴（实时计算） */
        Boolean overdueNow,
        String generateType,
        String remark,
        Integer billingDays,
        BigDecimal prorationMonths,
        LocalDateTime createTime
) {
    public static BillVO from(FinBill e) {
        if (e == null) {
            return null;
        }
        BillStatus st;
        try {
            st = BillStatus.valueOf(e.getBillStatus());
        } catch (IllegalArgumentException ex) {
            st = BillStatus.UNPAID;
        }
        boolean overdueNow = false;
        long days = 0;
        if (st.isOutstanding() && e.getDueDate() != null
                && LocalDate.now().isAfter(e.getDueDate())) {
            overdueNow = true;
            days = ChronoUnit.DAYS.between(e.getDueDate(), LocalDate.now());
        }
        return new BillVO(e.getId(), e.getBillNo(), e.getOrgId(), e.getContractId(),
                e.getHouseId(), e.getPersonId(), e.getPayerName(), e.getFeeItemId(),
                e.getBillPeriod(), e.getPeriodStart(), e.getPeriodEnd(), e.getSettlementDate(),
                e.getBillAmount(), e.getUnitPriceSnapshot(), e.getPriceSource(),
                e.getDiscountAmount(), e.getLateFee(), e.getPaidAmount(), e.getWaivedAmount(),
                e.getPayableAmount(), e.getDueDate(), e.getBillDate(), e.getBillStatus(), st.label(),
                e.getOverdueDays(), overdueNow, e.getGenerateType(), e.getRemark(),
                e.getBillingDays(), e.getProrationMonths(), e.getCreateTime());
    }
}
