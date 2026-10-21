package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.ExchangeStatus;
import com.yundao.bp.biz.constant.ExchangeType;
import com.yundao.bp.biz.entity.BizExchange;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 换房单视图。
 */
public record ExchangeVO(
        Long id,
        String exchangeNo,
        Long personId,
        Long oldContractId,
        Long oldHouseId,
        Long newHouseId,
        Long newContractId,
        String exchangeType,
        String exchangeTypeLabel,
        String exchangeReason,
        String exchangeStatus,
        String exchangeStatusLabel,
        Boolean grantMigrated,
        Integer exchangeTimes,
        Boolean forced,
        /**
         * 是否已无换房次数（成都限 1 次）。
         *
         * <p>语义：<b>该租期已完成换房次数 ≥ 上限</b>，即"不能再换"，
         * 而非"本次是第几次"。首次申请（未完成过换房）应为 false。
         */
        Boolean exchangeLimitReached,
        Boolean noExchangeFlag,
        BigDecimal rentMultiplier,
        Integer familySizeBefore,
        Integer familySizeAfter,
        String exchangeReasonCode,
        LocalDateTime createTime
) {
    public static ExchangeVO from(BizExchange e) {
        if (e == null) {
            return null;
        }
        ExchangeType tp;
        try {
            tp = ExchangeType.valueOf(e.getExchangeType());
        } catch (IllegalArgumentException ex) {
            tp = ExchangeType.VOLUNTARY;
        }
        ExchangeStatus st;
        try {
            st = ExchangeStatus.valueOf(e.getExchangeStatus());
        } catch (IllegalArgumentException ex) {
            st = ExchangeStatus.APPLYING;
        }
        int times = e.getExchangeTimes() == null ? 0 : e.getExchangeTimes();
        // 仅"已完成"的换房才消耗次数；已无次数 = 已完成次数 >= 1（成都限 1 次）
        boolean noQuota = ExchangeStatus.COMPLETED.name().equals(e.getExchangeStatus());
        return new ExchangeVO(e.getId(), e.getExchangeNo(), e.getPersonId(),
                e.getOldContractId(), e.getOldHouseId(), e.getNewHouseId(),
                e.getNewContractId(), e.getExchangeType(), tp.label(), e.getExchangeReason(),
                e.getExchangeStatus(), st.label(),
                e.getGrantMigrated() != null && e.getGrantMigrated() == 1,
                times, e.getIsForced() != null && e.getIsForced() == 1,
                noQuota,
                e.getNoExchangeFlag() != null && e.getNoExchangeFlag() == 1,
                e.getRentMultiplier(), e.getFamilySizeBefore(), e.getFamilySizeAfter(),
                e.getExchangeReasonCode(), e.getCreateTime());
    }
}
