package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 发起合同变更。
 *
 * <p>按 {@code changeType} 填对应字段：
 * <ul>
 *   <li>{@code RENT_ADJUST} → {@code newMonthlyRent}</li>
 *   <li>{@code PERIOD} → {@code newLeaseEnd}</li>
 *   <li>{@code OTHER} → {@code remark}</li>
 * </ul>
 */
public record ChangeCreateCmd(

        @NotBlank(message = "变更类型不能为空")
        @Pattern(regexp = "RENEW|RENT_ADJUST|PERIOD|LESSEE|OTHER", message = "变更类型不合法")
        String changeType,

        String changeReason,

        /** 新月租金（RENT_ADJUST / RENEW） */
        BigDecimal newMonthlyRent,

        /** 新止租日（PERIOD / RENEW） */
        LocalDate newLeaseEnd,

        /** 新承租人人员ID（LESSEE） */
        Long newLesseePersonId,
        String newLesseeName,

        /** 生效日期；为空则批准时取当天 */
        LocalDate effectiveDate,

        /** 其他变更说明 */
        String remark
) {
}
