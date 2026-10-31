package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;

public record MeterPointCmd(
        @NotNull(message = "空间不能为空") Long spaceId,
        @NotNull(message = "收费项目不能为空") Long feeItemId,
        String meterScope,
        String allocationBasis,
        Integer bedCapacity,
        String meterName,
        String status
) {
}
