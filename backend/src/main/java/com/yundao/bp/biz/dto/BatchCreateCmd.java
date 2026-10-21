package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 创建配租批次。
 *
 * @param houseIds 批次可配房源（创建时一并入池）
 */
public record BatchCreateCmd(

        @NotBlank(message = "批次名称不能为空")
        String batchName,

        @NotNull(message = "项目组织不能为空")
        Long orgId,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        @NotBlank(message = "批次类型不能为空")
        @Pattern(regexp = "LOTTERY|SELECT|DIRECT|SUPPLEMENT", message = "批次类型不合法")
        String batchType,

        /** 可配房源 ID 列表 */
        List<Long> houseIds,

        LocalDateTime signupStart,
        LocalDateTime signupEnd,
        LocalDateTime lotteryTime,
        LocalDateTime selectStart,
        LocalDateTime selectEnd,

        String notaryInfo,
        String remark
) {
}
