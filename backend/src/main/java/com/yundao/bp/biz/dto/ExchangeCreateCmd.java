package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

/**
 * 申请换房。
 *
 * @param forceExchange 是否属于"应当换房"（如期满时合住人数减少不符户型标准）
 */
public record ExchangeCreateCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "原合同不能为空")
        Long oldContractId,

        @NotNull(message = "原房源不能为空")
        Long oldHouseId,

        @NotNull(message = "新房源不能为空")
        Long newHouseId,

        @NotBlank(message = "换房类型不能为空")
        @Pattern(regexp = "VOLUNTARY|ADJUST|EXPEL_RELOCATE", message = "换房类型不合法")
        String exchangeType,

        String exchangeReason,

        /** 换房原因码：MARRIAGE / BIRTH / COHABIT / EMPLOYMENT / SCHOOL / OTHER */
        String exchangeReasonCode,

        Integer familySizeBefore,
        Integer familySizeAfter,

        Boolean forceExchange
) {
}
