package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.constant.LotteryResultType;
import com.yundao.bp.biz.entity.BizLotteryResult;
import java.time.LocalDateTime;

/**
 * 摇号结果视图。
 */
public record LotteryResultVO(
        Long id,
        Long batchId,
        Long personId,
        Long applicationId,
        Long waitingId,
        String resultType,
        String resultTypeLabel,
        String lotterySeq,
        Integer selectSeq,
        Long houseId,
        Long spaceId,
        LocalDateTime selectTime,
        String resultStatus,
        String giveUpReason
) {
    public static LotteryResultVO from(BizLotteryResult e) {
        if (e == null) {
            return null;
        }
        LotteryResultType t;
        try {
            t = LotteryResultType.valueOf(e.getResultType());
        } catch (IllegalArgumentException ex) {
            t = LotteryResultType.LOST;
        }
        return new LotteryResultVO(e.getId(), e.getBatchId(), e.getPersonId(),
                e.getApplicationId(), e.getWaitingId(), e.getResultType(), t.label(),
                e.getLotterySeq(), e.getSelectSeq(), e.getHouseId(), e.getSpaceId(),
                e.getSelectTime(), e.getResultStatus(), e.getGiveUpReason());
    }
}
