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
        String giveUpReason,
        String personName,
        String phoneMask,
        /** 优先附加分 */
        java.math.BigDecimal priorityScore,
        /** 轮候天数 */
        Integer waitDays,
        /** 总分 = 附加分 + 轮候天数 × 0.1 */
        java.math.BigDecimal totalScore
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
                e.getSelectTime(), e.getResultStatus(), e.getGiveUpReason(), null, null,
                null, null, null);
    }

    /** 补充人员姓名与脱敏手机号 */
    public LotteryResultVO withPerson(String name, String phone) {
        return new LotteryResultVO(id, batchId, personId, applicationId, waitingId, resultType,
                resultTypeLabel, lotterySeq, selectSeq, houseId, spaceId, selectTime,
                resultStatus, giveUpReason, name, phone, priorityScore, waitDays, totalScore);
    }
}
