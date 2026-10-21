package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 起草合同。
 *
 * <p>金额口径：{@code actualPay = monthlyRent - subsidyAmount}（服务端计算，不接受前端传入）。
 */
public record ContractCreateCmd(

        @NotBlank(message = "合同类型不能为空")
        @Pattern(regexp = "PUBLIC_RENTAL|AFFORDABLE|TALENT|LEASE|SERVICE|DORMITORY",
                message = "合同类型不合法")
        String contractType,

        @NotNull(message = "签约组织不能为空")
        Long orgId,

        @NotNull(message = "出租方不能为空")
        Long lessorOrgId,

        @NotNull(message = "承租人不能为空")
        Long lesseePersonId,
        String lesseeName,
        String lesseePhone,
        String lesseeIdCardMask,

        @NotNull(message = "房源不能为空")
        Long houseId,
        @NotNull(message = "空间不能为空")
        Long spaceId,
        String houseAddress,
        BigDecimal houseArea,

        @NotNull(message = "起租日不能为空")
        LocalDate leaseStart,
        @NotNull(message = "止租日不能为空")
        LocalDate leaseEnd,

        @NotNull(message = "租金单价不能为空")
        @DecimalMin(value = "0", message = "租金单价不能为负")
        BigDecimal rentPrice,

        @Pattern(regexp = "^$|AREA_MONTH|HOUSE_MONTH|BED_MONTH|HOUSE_NIGHT|BED_NIGHT",
                message = "租金单位不合法")
        String rentUnit,

        @NotNull(message = "月租金不能为空")
        @DecimalMin(value = "0", message = "月租金不能为负")
        BigDecimal monthlyRent,

        @DecimalMin(value = "0", message = "押金不能为负")
        BigDecimal depositAmount,

        @DecimalMin(value = "0", message = "补贴不能为负")
        BigDecimal subsidyAmount,

        @Pattern(regexp = "^$|MONTH|QUARTER|HALF_YEAR|YEAR", message = "缴费周期不合法")
        String payCycle,

        @Min(value = 1, message = "缴费日必须在 1-31")
        Integer payDay,

        @Pattern(regexp = "^$|ELECTRONIC|PAPER|FACE", message = "签署方式不合法")
        String signType,

        Long templateId,
        Long allocationId,
        Long parentContractId,

        BigDecimal lateFeeRate,
        String remark
) {
}
