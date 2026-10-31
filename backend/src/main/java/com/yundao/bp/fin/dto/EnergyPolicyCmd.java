package com.yundao.bp.fin.dto;

import java.math.BigDecimal;

public record EnergyPolicyCmd(
        Long orgId,
        String vacancyBearer,
        BigDecimal warnRate,
        BigDecimal alarmRate
) {
}
