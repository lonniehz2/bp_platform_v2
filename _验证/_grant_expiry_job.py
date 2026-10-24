# -*- coding: utf-8 -*-
"""接口与定时任务：权益到期自动归还。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'grant')

# 1) 接口方法
S = os.path.join(J, 'service', 'GrantService.java')
s = io.open(S, encoding='utf-8').read()
if 'expireOverdue' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 管理权到期自动归还：把 valid_end 已过的生效权益置为 EXPIRED，返回条数。 */
    int expireOverdue();
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('GrantService：expireOverdue 已加')

# 2) 定时任务
T = os.path.join(J, 'GrantExpiryJob.java')
if not os.path.exists(T):
    io.open(T, 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.grant;

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
''')
    print('GrantExpiryJob：已创建')
