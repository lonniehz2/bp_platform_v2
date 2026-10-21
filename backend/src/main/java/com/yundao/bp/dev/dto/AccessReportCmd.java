package com.yundao.bp.dev.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

/**
 * 上报一条开门记录。
 *
 * <p>{@code eventId} 是幂等键，必须由 IoT 侧提供且唯一。
 */
public record AccessReportCmd(

        @NotBlank(message = "事件ID不能为空（幂等去重）")
        String eventId,

        String lockId,
        String deviceId,
        String deviceMac,

        Long spaceId,
        Long houseId,
        Long orgId,

        @NotBlank(message = "开门方式不能为空")
        String openType,

        Long personId,
        String targetUserMobile,

        @NotNull(message = "开门时间不能为空")
        LocalDateTime openTime,

        /** CALLBACK / PULL */
        String source,

        Boolean abnormal,
        String abnormalType
) {
}
