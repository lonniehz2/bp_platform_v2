package com.yundao.bp.dev.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.dev.service.impl.DevCommandServiceImpl;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** 每 30 秒扫描超时指令：重试或置 TIMEOUT。 */
@Component
public class DevCommandTimeoutJob {

    private static final Logger log = LoggerFactory.getLogger(DevCommandTimeoutJob.class);

    private final DevCommandServiceImpl service;
    private final IamTenantMapper tenantMapper;

    public DevCommandTimeoutJob(DevCommandServiceImpl service, IamTenantMapper tenantMapper) {
        this.service = service;
        this.tenantMapper = tenantMapper;
    }

    @Scheduled(initialDelay = 45_000, fixedDelay = 30_000)
    public void sweep() {
        for (String tenantId : tenantCodes()) {
            try {
                TenantContext.set(TenantInfo.of(tenantId, null));
                int n = service.sweepTimeout();
                if (n > 0) {
                    log.info("指令超时扫描 tenant={} {} 条", tenantId, n);
                }
            } catch (Exception e) {
                log.warn("指令超时扫描失败 tenant={}: {}", tenantId, e.getMessage());
            } finally {
                TenantContext.clear();
            }
        }
    }

    private java.util.List<String> tenantCodes() {
        try {
            java.util.List<com.yundao.bp.iam.entity.IamTenant> list = tenantMapper.selectList(
                    new LambdaQueryWrapper<com.yundao.bp.iam.entity.IamTenant>()
                            .eq(com.yundao.bp.iam.entity.IamTenant::getStatus, "ENABLED"));
            java.util.List<String> out = new java.util.ArrayList<>();
            for (com.yundao.bp.iam.entity.IamTenant t : list) {
                out.add(t.getTenantCode());
            }
            return out;
        } catch (Exception e) {
            log.warn("租户列表读取失败，回落到默认租户: {}", e.getMessage());
            return java.util.List.of("350600");
        }
    }
}
