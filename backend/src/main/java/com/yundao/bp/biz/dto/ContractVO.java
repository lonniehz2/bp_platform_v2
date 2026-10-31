package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ContractStatus;
import com.yundao.bp.biz.entity.BizContract;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

/**
 * 合同视图（含派生指标）。
 */
public record ContractVO(
        Long id,
        String contractNo,
        String contractType,
        Long orgId,
        Long lessorOrgId,
        Long lesseePersonId,
        String lesseeName,
        String lesseePhone,
        String lesseeIdCardMask,
        Long houseId,
        String houseAddress,
        BigDecimal houseArea,
        LocalDate leaseStart,
        LocalDate leaseEnd,
        Integer leaseMonths,
        BigDecimal rentPrice,
        String rentUnit,
        BigDecimal monthlyRent,
        BigDecimal depositAmount,
        BigDecimal subsidyAmount,
        BigDecimal actualPay,
        String payCycle,
        Integer payDay,
        String signType,
        LocalDateTime signTime,
        String contractStatus,
        String contractStatusLabel,
        LocalDateTime effectiveTime,
        LocalDateTime terminateTime,
        String terminateReason,
        Integer autoGrant,
        Integer autoExpire,
        Integer arrearsStop,
        /** 派生：距到期剩余天数（履约中才有意义，其它为 null） */
        Long daysToExpire,
        /** 派生：是否即将到期（30 天内） */
        Boolean expiringSoon,
        /** 派生：是否占房（履约中/续签中） */
        Boolean occupying,
        String remark,
        LocalDateTime createTime,
        /** 父合同ID：换房/续签生成的新合同指向原合同，便于追溯链条 */
        Long parentContractId,
        Integer billingPersonCount,
        Integer billingBedCount
) {
    public static ContractVO from(BizContract e) {
        if (e == null) {
            return null;
        }
        ContractStatus st;
        try {
            st = ContractStatus.valueOf(e.getContractStatus());
        } catch (IllegalArgumentException ex) {
            st = ContractStatus.DRAFT;
        }
        Long daysToExpire = null;
        boolean expiringSoon = false;
        if (st.isOccupying() && e.getLeaseEnd() != null) {
            daysToExpire = ChronoUnit.DAYS.between(LocalDate.now(), e.getLeaseEnd());
            expiringSoon = daysToExpire >= 0 && daysToExpire <= 30;
        }
        return new ContractVO(e.getId(), e.getContractNo(), e.getContractType(), e.getOrgId(),
                e.getLessorOrgId(), e.getLesseePersonId(), e.getLesseeName(), e.getLesseePhone(),
                e.getLesseeIdCardMask(), e.getHouseId(), e.getHouseAddress(),
                e.getHouseArea(), e.getLeaseStart(), e.getLeaseEnd(), e.getLeaseMonths(),
                e.getRentPrice(), e.getRentUnit(), e.getMonthlyRent(), e.getDepositAmount(),
                e.getSubsidyAmount(), e.getActualPay(), e.getPayCycle(), e.getPayDay(),
                e.getSignType(), e.getSignTime(), e.getContractStatus(), st.label(),
                e.getEffectiveTime(), e.getTerminateTime(), e.getTerminateReason(),
                e.getAutoGrant(), e.getAutoExpire(), e.getArrearsStop(),
                daysToExpire, expiringSoon, st.isOccupying(), e.getRemark(), e.getCreateTime(),
                e.getParentContractId(),
                e.getBillingPersonCount(), e.getBillingBedCount());
    }
}
