package com.yundao.bp.grant.config;

import com.yundao.bp.grant.iot.IotAuthorizationClient;
import com.yundao.bp.grant.iot.IotGrantClient;
import com.yundao.bp.grant.iot.MockIotAuthorizationClient;
import com.yundao.bp.grant.iot.MockIotGrantClient;
import com.yundao.bp.grant.iot.YmdGrantClient;
import com.yundao.bp.iot.legacy.YmdClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * IoT 授权客户端装配。
 *
 * <p>{@code bp.grant.iot-mode}：
 * <ul>
 *   <li>{@code mock}（默认）—— 不真正下发，用于编排验证与演示</li>
 *   <li>{@code real} —— 走真实 IoT 平台（需配置 ymd.iot.* 凭证，且参数需联调确认）</li>
 * </ul>
 */
@Configuration
public class GrantIotConfig {

    private static final Logger log = LoggerFactory.getLogger(GrantIotConfig.class);

    @Bean
    public IotAuthorizationClient iotAuthorizationClient() {
        return new MockIotAuthorizationClient();
    }

    @Bean
    public IotGrantClient iotGrantClient(
            @Value("${bp.grant.iot-mode:mock}") String mode,
            org.springframework.beans.factory.ObjectProvider<YmdClient> ymdClientProvider) {

        if ("real".equalsIgnoreCase(mode)) {
            YmdClient ymd = ymdClientProvider.getIfAvailable();
            if (ymd == null) {
                log.error("bp.grant.iot-mode=real 但未配置 ymd.iot 凭证，降级为 mock");
                return new MockIotGrantClient();
            }
            log.info("IoT 授权客户端 = YmdGrantClient（真实平台）");
            return new YmdGrantClient(ymd);
        }
        log.info("IoT 授权客户端 = MockIotGrantClient（不真正下发）");
        return new MockIotGrantClient();
    }
}
