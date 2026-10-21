package com.yundao.bp.dev.dto;

import java.time.LocalDateTime;

/**
 * 空置判定结果。
 */
public record IdleStatVO(
        Long houseId,
        Long spaceId,
        Long orgId,
        /** 最近一次开门时间（无记录则为 null） */
        LocalDateTime lastOpenTime,
        /** 连续无开门天数 */
        long idleDays,
        /** 是否疑似空置 */
        boolean suspectIdle,
        String remark
) {
}
