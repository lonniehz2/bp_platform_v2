package com.yundao.bp.grant.iot;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicLong;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 模拟 IoT 授权客户端（<b>默认</b>，仅用于编排验证与演示）。
 *
 * <p>⚠️ 它不会真正下发到门锁。启用条件：{@code bp.grant.iot-mode=mock}（默认）。
 * 启动时会打印 WARN 提醒。
 *
 * <p>行为：对每个 lockId 返回成功，模拟 5ms 耗时，用于验证
 * 任务状态机、明细写入、统计与重试。
 */
public class MockIotGrantClient implements IotGrantClient {

    private static final Logger log = LoggerFactory.getLogger(MockIotGrantClient.class);
    private final AtomicLong seq = new AtomicLong(System.currentTimeMillis() % 100000);

    public MockIotGrantClient() {
        log.warn("========================================================");
        log.warn(" IoT 授权使用 MOCK 实现：不会真正下发到门锁！");
        log.warn(" 要对接真实平台，请设置 bp.grant.iot-mode=real");
        log.warn("========================================================");
    }

    @Override
    public IotGrantResult grant(IotGrantRequest req) {
        List<IotGrantResult.DeviceResult> devs = new ArrayList<>();
        for (String lockId : req.lockIds()) {
            devs.add(new IotGrantResult.DeviceResult(lockId, true, null, null, 5));
        }
        String taskId = "MOCK-" + seq.incrementAndGet();
        return IotGrantResult.ok(taskId, "MOCK 授权已受理", devs);
    }

    @Override
    public IotGrantResult revoke(IotGrantRequest req) {
        List<IotGrantResult.DeviceResult> devs = new ArrayList<>();
        for (String lockId : req.lockIds()) {
            devs.add(new IotGrantResult.DeviceResult(lockId, true, null, null, 5));
        }
        return IotGrantResult.ok("MOCK-R-" + seq.incrementAndGet(), "MOCK 撤销已受理", devs);
    }

    @Override
    public IotGrantResult queryTaskResult(String iotTaskId) {
        // 模拟：立刻返回成功，明细由编排层按原请求补齐
        return IotGrantResult.ok(iotTaskId, "MOCK 任务已完成", List.of());
    }
}
