package com.yundao.bp.grant.iot;

import java.util.concurrent.atomic.AtomicLong;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 授权冻结/恢复本地模拟实现。
 *
 * <p>真实 IoT 平台接入时替换此 Bean 即可；业务系统只负责发起与接收回调。
 * 模拟实现不会真正操作门锁，只返回受理单号。
 */
public class MockIotAuthorizationClient implements IotAuthorizationClient {

    private static final Logger log = LoggerFactory.getLogger(MockIotAuthorizationClient.class);
    private final AtomicLong seq = new AtomicLong(System.currentTimeMillis() % 100000);

    public MockIotAuthorizationClient() {
        log.warn("IoT 授权冻结使用 MOCK 实现：不会真正下发到门锁");
    }

    @Override
    public IotAuthorizationResult freeze(IotAuthorizationRequest req) {
        return IotAuthorizationResult.ok("MOCK-FREEZE-" + seq.incrementAndGet());
    }

    @Override
    public IotAuthorizationResult unfreeze(IotAuthorizationRequest req) {
        return IotAuthorizationResult.ok("MOCK-UNFREEZE-" + seq.incrementAndGet());
    }
}
