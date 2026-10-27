package com.yundao.bp.dev.iot;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 表计读数拉取（平台 → IoT）。配置 {@code bp.dev.meter-mode=mock|real}。
 *
 * <p>与设备主动上报（回调 meter）互为补充：本接口用于补数/对账。
 */
public interface MeterPullClient {

    List<Reading> pull(List<String> meterNos, LocalDate from, LocalDate to);

    record Reading(String meterNo, String deviceId, String meterType,
                   BigDecimal reading, BigDecimal multiplier, LocalDateTime readTime) {
    }
}
