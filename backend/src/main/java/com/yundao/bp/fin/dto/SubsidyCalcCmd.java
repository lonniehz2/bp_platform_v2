package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 补贴试算（不落库）。
 */
public record SubsidyCalcCmd(

        @NotNull(message = "合同不能为空")
        Long contractId,

        Long standardId,

        /** 面积（BY_AREA 用；不传取合同/房源面积） */
        BigDecimal area,

        /** 家庭人口（BY_PERSON 用） */
        Integer personCount,

        /** 月租金（RATIO 用；不传取合同月租金） */
        BigDecimal monthlyRent
) {
}
