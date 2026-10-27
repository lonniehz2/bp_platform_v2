package com.yundao.bp.dev.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.iot.gateway.IotSyncService;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/** 每日同步：05:30 设备台账增量，06:10 表计读数补拉（前一天）。 */
@Component
public class IotDailySyncJob {

    private static final Logger log = LoggerFactory.getLogger(IotDailySyncJob.class);

    private final IotSyncService syncService;
    private final IamTenantMapper tenantMapper;

    public IotDailySyncJob(IotSyncService syncService, IamTenantMapper tenantMapper) {
        this.syncService = syncService;
        this.tenantMapper = tenantMapper;
    }

    @Scheduled(cron = "0 30 5 * * ?")
    public void syncDevices() {
        forEachTenant("设备同步", () -> syncService.syncDevices(
                LocalDateTime.now().minusDays(1)));
    }

    @Scheduled(cron = "0 10 6 * * ?")
    public void pullMeters() {
        forEachTenant("表计拉取", () -> syncService.pullMeters(LocalDate.now().minusDays(1)));
    }

    private void forEachTenant(String label, Runnable action) {
        try {
            for (IamTenant t : tenantMapper.selectList(new LambdaQueryWrapper<IamTenant>()
                    .eq(IamTenant::getStatus, "ENABLED"))) {
                try {
                    TenantContext.set(TenantInfo.of(t.getTenantCode(), null));
                    action.run();
                } catch (Exception e) {
                    log.warn("{}失败 tenant={}: {}", label, t.getTenantCode(), e.getMessage());
                } finally {
                    TenantContext.clear();
                }
            }
        } catch (Exception e) {
            log.warn("{}调度失败: {}", label, e.getMessage());
        }
    }
}
