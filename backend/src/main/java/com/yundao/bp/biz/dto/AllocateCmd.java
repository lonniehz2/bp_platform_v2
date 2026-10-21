package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

/**
 * 生成配租单（用房源锁定给中签人）。
 *
 * @param lockHours 房源锁定小时数；超时未签约自动释放，默认 72 小时
 */
public record AllocateCmd(

        @NotNull(message = "批次不能为空")
        Long batchId,

        @NotNull(message = "房源不能为空")
        Long houseId,

        @NotNull(message = "承租人不能为空")
        Long personId,

        /** 摇号结果 ID（可空；为空则按批次+人员反查） */
        Long lotteryResultId,

        LocalDate planRentStart,
        LocalDate planRentEnd,

        Integer lockHours
) {
}
