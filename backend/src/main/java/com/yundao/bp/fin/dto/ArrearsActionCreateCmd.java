package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;

/**
 * 创建欠费处置单。
 *
 * @param freezeScope         冻结范围；<b>默认 EXCLUDE_MAIN_DOOR（安全底线，不停大门）</b>。
 *                            {@code ALL} 会停用大门，需 {@code confirmSafetyRisk=true} 才允许。
 * @param confirmSafetyRisk   是否已确认"停用大门"的安全风险（默认 false）
 */
public record ArrearsActionCreateCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        @NotNull(message = "人员不能为空")
        Long personId,

        @NotNull(message = "欠费金额不能为空")
        @DecimalMin(value = "0.01", message = "欠费金额必须大于 0")
        BigDecimal arrearsAmount,

        Integer overdueDays,

        /** 组织（为空时按合同补） */
        Long orgId,

        @NotBlank(message = "处置动作不能为空")
        @Pattern(regexp = "NOTIFY|FREEZE|UNFREEZE|RESTRICT|EXPIRE|LEGAL",
                message = "处置动作不合法")
        String actionType,

        @Pattern(regexp = "^$|ALL|ROOM_LOCK|EXCLUDE_MAIN_DOOR", message = "冻结范围不合法")
        String freezeScope,

        /** 是否已确认停用大门的安全风险 */
        Boolean confirmSafetyRisk,

        @Pattern(regexp = "^$|AUTO|MANUAL", message = "触发方式不合法")
        String triggerType
) {
}
