package com.yundao.bp.iot.credential;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟凭据同步。 */
@Component
@ConditionalOnProperty(name = "bp.credential.mode", havingValue = "mock", matchIfMissing = true)
public class MockCredentialSyncClient implements CredentialSyncClient {

    private static final Logger log = LoggerFactory.getLogger(MockCredentialSyncClient.class);

    @Override
    public Result sync(SyncRequest req) {
        log.info("[mock] 凭据同步 {} person={} type={} action={}", req.requestId(),
                req.personId(), req.keyType(), req.action());
        return new Result(true, "0", "mock ok");
    }
}
