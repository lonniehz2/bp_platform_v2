package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/**
 * 提交保障房申请。
 */
public record ApplicationCreateCmd(

        @NotNull(message = "受理组织不能为空")
        Long orgId,

        @NotNull(message = "申请人员不能为空")
        Long personId,

        @NotBlank(message = "保障类型不能为空")
        @Pattern(regexp = "PUBLIC|AFFORDABLE|TALENT|LOW_RENT", message = "保障类型不合法")
        String securityType,

        @Pattern(regexp = "^$|HOUSE|SUBSIDY", message = "保障方式不合法")
        String securityMode,

        @Pattern(regexp = "^$|ONLINE|OFFLINE|IMPORT", message = "申请渠道不合法")
        String applyChannel,

        @NotNull(message = "家庭人口数不能为空")
        @Min(value = 1, message = "家庭人口数至少为 1")
        Integer familySize,

        String intentDistrict,
        Long intentProject,
        String intentLayout,
        BigDecimal intentAreaMin,
        BigDecimal intentAreaMax,

        BigDecimal declaredIncome,
        BigDecimal declaredIncomeYear,
        BigDecimal familyPropertyAmount,

        @Pattern(regexp = "^$|LAST_YEAR|LAST_12M", message = "收入统计期不合法")
        String incomeCheckPeriod,

        String formData,
        String attachmentUrls,

        /** 是否签署真实性承诺书（保障房必备） */
        Integer complianceCommitFlag,
        /** 是否书面同意核实申报信息 */
        Integer dataShareAgreeFlag,

        String remark
) {
}
