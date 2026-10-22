package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 公摊费用分摊出账。
 *
 * @param allocateBy 分摊方式：AREA（按建筑面积）| HOUSE（按户数）
 */
public record SharedBillCmd(

        @NotNull(message = "组织不能为空")
        Long orgId,

        /** 限定楼栋/单元（可空，空表示整个组织） */
        Long spaceId,

        @NotNull(message = "收费项目不能为空")
        Long feeItemId,

        @NotNull(message = "总分摊金额不能为空")
        @DecimalMin(value = "0.01", message = "分摊金额必须大于 0")
        BigDecimal totalAmount,

        @NotNull(message = "费用起始日不能为空")
        LocalDate periodStart,

        @NotNull(message = "费用截止日不能为空")
        LocalDate periodEnd,

        @NotBlank(message = "账期不能为空")
        String billPeriod,

        LocalDate dueDate,

        /** AREA | HOUSE */
        String allocateBy
) {
}
