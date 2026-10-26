package com.yundao.bp.dev.iot;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟下发：直接返回成功，便于验证指令状态机与页面。 */
@Component
@ConditionalOnProperty(name = "bp.dev.command-mode", havingValue = "mock", matchIfMissing = true)
public class MockDeviceCommandClient implements DeviceCommandClient {

    private static final Logger log = LoggerFactory.getLogger(MockDeviceCommandClient.class);

    @Override
    public CommandResult send(CommandRequest req) {
        log.info("[mock] 下发指令 {} type={} lock={} meter={}", req.requestId(),
                req.commandType(), req.lockId(), req.meterNo());
        return CommandResult.ok("0", "mock ok", 12);
    }
}
