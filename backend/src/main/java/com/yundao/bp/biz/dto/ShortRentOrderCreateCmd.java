package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 创建短租订单。
 *
 * <p><b>时刻级</b>：入住/退房精确到时分，适配酒店 14:00 入住、次日 12:00 退房。
 *
 * <p><b>房晚口径</b>：按日期差计算（左闭右开）——
 * 11-01 14:00 → 11-02 12:00 为 <b>1 晚</b>；
 * 同日入住退房视为钟点房，按 <b>1 晚</b> 计。
 */
public record ShortRentOrderCreateCmd(

        @NotNull(message = "房源不能为空")
        Long houseId,

        Long spaceId,

        @NotBlank(message = "来源渠道不能为空")
        @Pattern(regexp = "DIRECT|OTA|WECHAT|PHONE|WALKIN|OTHER", message = "来源渠道不合法")
        String sourceChannel,

        /** 网约房必须实名 */
        @NotBlank(message = "住客姓名不能为空（网约房需实名登记）")
        String guestName,

        String guestPhone,
        String guestIdCard,

        @Min(value = 1, message = "入住人数至少 1 人")
        Integer guestCount,

        @NotNull(message = "入住时刻不能为空")
        LocalDateTime checkInTime,

        @NotNull(message = "退房时刻不能为空")
        LocalDateTime checkOutTime,

        /** 房晚单价；不传则按房源默认价（本模块不自动取价，由前端/渠道传入） */
        @NotNull(message = "房晚单价不能为空")
        BigDecimal nightlyPrice,

        BigDecimal extraAmount,
        BigDecimal discountAmount,
        BigDecimal paidAmount,
        String remark
) {
}
