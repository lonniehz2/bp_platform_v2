package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 申请通过后加入轮候库。
 */
public record WaitingEnterCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "申请单不能为空")
        Long applicationId,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        Long orgId,

        /** 优先条件分（如低保、残疾、优抚等，由业务按政策核定） */
        @DecimalMin(value = "0", message = "优先分不能为负")
        BigDecimal priorityScore,

        /** 轮候资格有效期；为空则不设限 */
        LocalDate validUntil
) {
}
