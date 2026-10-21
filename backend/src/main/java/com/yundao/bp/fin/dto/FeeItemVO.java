package com.yundao.bp.fin.dto;

import com.yundao.bp.fin.constant.CalcMode;
import com.yundao.bp.fin.entity.FinFeeItem;
import java.math.BigDecimal;

/**
 * 收费项目视图。
 */
public record FeeItemVO(
        Long id,
        String itemCode,
        String itemName,
        String itemType,
        String securityType,
        String calcMode,
        String calcModeLabel,
        BigDecimal unitPrice,
        String unit,
        String status
) {
    public static FeeItemVO from(FinFeeItem e) {
        if (e == null) {
            return null;
        }
        CalcMode m;
        try {
            m = CalcMode.valueOf(e.getCalcMode());
        } catch (IllegalArgumentException ex) {
            m = CalcMode.FIXED;
        }
        return new FeeItemVO(e.getId(), e.getItemCode(), e.getItemName(), e.getItemType(),
                e.getSecurityType(), e.getCalcMode(), m.label(), e.getUnitPrice(), e.getUnit(),
                e.getStatus());
    }
}
