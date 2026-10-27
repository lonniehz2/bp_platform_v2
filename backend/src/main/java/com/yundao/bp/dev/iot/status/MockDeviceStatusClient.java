package com.yundao.bp.dev.iot.status;

import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 模拟批量状态：在线与否按 lockId 哈希稳定分布，电量在 20~100 之间。 */
@Component
@ConditionalOnProperty(name = "bp.iot.status-mode", havingValue = "mock", matchIfMissing = true)
public class MockDeviceStatusClient implements DeviceStatusClient {

    @Override
    public List<DeviceStatus> batch(List<String> lockIds) {
        List<DeviceStatus> out = new ArrayList<>();
        for (String id : lockIds) {
            int h = Math.abs(id.hashCode());
            boolean online = h % 7 != 0;
            out.add(new DeviceStatus(id, online, 20 + h % 81, -(40 + h % 40),
                    null, "mock-1.0.0"));
        }
        return out;
    }
}
