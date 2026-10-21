package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 生成账单。
 *
 * <p>应付金额由服务端计算：{@code payable = 应收 - 减免 + 滞纳金 - 已收 - 已免}。
 */
public record BillCreateCmd(

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        @NotNull(message = "组织不能为空")
        Long orgId,

        Long contractId,
        Long houseId,
        Long spaceId,
        Long personId,
        String payerName,
        String payerPhone,

        String billPeriod,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,
        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        @NotNull(message = "应收金额不能为空")
        @DecimalMin(value = "0", message = "应收金额不能为负")
        BigDecimal billAmount,

        @DecimalMin(value = "0", message = "减免金额不能为负")
        BigDecimal discountAmount,

        @DecimalMin(value = "0", message = "滞纳金不能为负")
        BigDecimal lateFee,

        LocalDate dueDate,

        @Pattern(regexp = "^$|AUTO|MANUAL|IMPORT", message = "生成方式不合法")
        String generateType,

        String remark
) {
}
