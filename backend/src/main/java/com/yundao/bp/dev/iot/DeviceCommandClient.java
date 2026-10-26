package com.yundao.bp.dev.iot;

import java.time.LocalDateTime;

/**
 * 设备指令下发客户端抽象。平台不直连设备，实现走 IoT 平台。
 *
 * <p>配置 {@code bp.dev.command-mode=mock|real}。real 实现待 IoT 接口确认后接入。
 */
public interface DeviceCommandClient {

    CommandResult send(CommandRequest req);

    record CommandRequest(String requestId, String commandType, String lockId,
                          String meterNo, String paramsJson) {
    }

    record CommandResult(boolean success, String code, String message,
                         LocalDateTime deviceTime, Integer costMs) {
        public static CommandResult ok(String code, String message, Integer costMs) {
            return new CommandResult(true, code, message, LocalDateTime.now(), costMs);
        }

        public static CommandResult fail(String code, String message) {
            return new CommandResult(false, code, message, null, null);
        }
    }
}
