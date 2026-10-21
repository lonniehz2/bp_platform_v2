package com.yundao.bp.fin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.LocalDate;

/**
 * 发起对账。
 *
 * <p>{@code systemAmount} 不传时由系统按当日该渠道收款单自动汇总；
 * {@code channelAmount} 为渠道/银行回单金额（人工录入或导入）。
 */
public record ReconcileCreateCmd(

        @NotNull(message = "对账日期不能为空")
        LocalDate reconcileDate,

        @NotBlank(message = "对账类型不能为空")
        @Pattern(regexp = "CHANNEL|DAILY|MANUAL", message = "对账类型不合法")
        String reconcileType,

        /** CHANNEL 类必填；不传则汇总全部渠道 */
        String payChannel,

        /** 系统金额；不传自动汇总 */
        BigDecimal systemAmount,

        @NotNull(message = "渠道金额不能为空")
        BigDecimal channelAmount,

        /** 差异笔数；不传默认 0 */
        Integer diffCount,

        String diffDetailUrl
) {
}
