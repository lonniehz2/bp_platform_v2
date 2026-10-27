package com.yundao.bp.dev.iot;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟台账拉取：返回空列表。 */
@Component
@ConditionalOnProperty(name = "bp.dev.device-mode", havingValue = "mock", matchIfMissing = true)
public class MockDeviceInventoryClient implements DeviceInventoryClient {

    @Override
    public List<DeviceInfo> fetch(LocalDateTime since) {
        return new ArrayList<>();
    }
}
