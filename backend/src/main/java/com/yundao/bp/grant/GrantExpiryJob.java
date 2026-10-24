package com.yundao.bp.grant;

import com.yundao.bp.grant.service.GrantService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

/**
 * 权益到期自动归还任务。
 *
 * <p>业务口径：管理权可带到期时间，到期后自动归还所有权者；
 * 所有权者也可随时强制收回（{@code /grant/{id}/revoke}）。
 */
@Configuration
@EnableScheduling
public class GrantExpiryJob {

    private static final Logger log = LoggerFactory.getLogger(GrantExpiryJob.class);

    private final GrantService grantService;

    public GrantExpiryJob(GrantService grantService) {
        this.grantService = grantService;
    }

    /** 每小时检查一次（启动后 5 分钟开始）。 */
    @Scheduled(initialDelay = 300000, fixedDelay = 3600000)
    public void sweep() {
        try {
            int n = grantService.expireOverdue();
            if (n > 0) {
                log.info("权益到期自动归还：{} 条", n);
            }
        } catch (Exception ex) {
            log.warn("权益到期检查失败：{}", ex.getMessage());
        }
    }
}
