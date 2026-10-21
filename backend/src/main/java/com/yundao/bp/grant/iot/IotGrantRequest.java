package com.yundao.bp.grant.iot;

import java.time.LocalDateTime;
import java.util.List;

/**
 * IoT 授权请求（与具体平台无关的中间模型）。
 *
 * @param personId   本地人员 ID
 * @param iotOwnerId IoT 侧人员主键（若已映射）
 * @param account    IoT 侧账号（通常手机号）
 * @param lockIds    目标门锁 ID 列表
 * @param validStart 生效时间
 * @param validEnd   失效时间（null=永久）
 * @param channelType 介质类型（null=仅 App 权限）
 */
public record IotGrantRequest(
        Long personId,
        String iotOwnerId,
        String account,
        List<String> lockIds,
        LocalDateTime validStart,
        LocalDateTime validEnd,
        String channelType,
        String channelModuleType
) {
}
