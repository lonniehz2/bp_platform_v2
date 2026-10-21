package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

/**
 * 创建收费项目。
 *
 * <p>⭐ {@code calcMode} 决定该费用"按什么算"，是<b>多业态适配的核心开关</b>：
 * <ul>
 *   <li>保障房租金 → {@code BY_AREA} / {@code BY_HOUSE}</li>
 *   <li>宿舍床位费 → {@code BY_BED}</li>
 *   <li>酒店/民宿/网约房 → {@code BY_NIGHT}</li>
 *   <li>园区水电能耗费 → {@code METER}</li>
 * </ul>
 */
public record FeeItemCreateCmd(

        @NotBlank(message = "项目编码不能为空")
        @Size(max = 64, message = "编码不能超过 64 字符")
        String itemCode,

        @NotBlank(message = "项目名称不能为空")
        @Size(max = 128, message = "名称不能超过 128 字符")
        String itemName,

        @NotBlank(message = "项目类型不能为空")
        @Pattern(regexp = "RENT|PROPERTY|PARKING|ENERGY|DEPOSIT|LATE_FEE|OTHER",
                message = "项目类型不合法")
        String itemType,

        String securityType,

        @NotBlank(message = "计费方式不能为空")
        @Pattern(regexp = "FIXED|BY_AREA|BY_HOUSE|BY_PERSON|BY_BED|BY_NIGHT|METER",
                message = "计费方式不合法")
        String calcMode,

        @DecimalMin(value = "0", message = "单价不能为负")
        BigDecimal unitPrice,

        String unit
) {
}
