package com.yundao.bp.dev.job;

import com.yundao.bp.dev.service.impl.DevCommandServiceImpl;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** 每 30 秒扫描超时指令：重试或置 TIMEOUT。 */
@Component
public class DevCommandTimeoutJob {

    private static final Logger log = LoggerFactory.getLogger(DevCommandTimeoutJob.class);

    private final DevCommandServiceImpl service;

    public DevCommandTimeoutJob(DevCommandServiceImpl service) {
        this.service = service;
    }

    @Scheduled(initialDelay = 45_000, fixedDelay = 30_000)
    public void sweep() {
        try {
            int n = service.sweepTimeout();
            if (n > 0) {
                log.info("指令超时扫描处理 {} 条", n);
            }
        } catch (Exception e) {
            log.warn("指令超时扫描失败: {}", e.getMessage());
        }
    }
}
