package com.yundao.bp.dev.iot.token;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟 Token：不访问 IoT，返回固定前缀的假 Token。 */
@Component
@ConditionalOnProperty(name = "bp.iot.token-mode", havingValue = "mock", matchIfMissing = true)
public class MockIotTokenClient implements IotTokenClient {

    private static final Logger log = LoggerFactory.getLogger(MockIotTokenClient.class);

    @Override
    public TokenInfo token() {
        String t = "mock-token-" + System.currentTimeMillis();
        log.debug("[mock] 取 Token: {}", t);
        return new TokenInfo(t, 7200);
    }
}
