package com.yundao.bp.dev.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.iot.config.IotSettings;
import com.yundao.bp.iot.gateway.IotSyncService;
import java.time.LocalDate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 小时级表计拉取：仅当配置为 HOURLY 的表类型存在时执行。
 *
 * <p>配置 {@code iot.meter.reportPeriod=ELEC:HOURLY,WATER:DAILY}；默认都是 DAILY，
 * 由 {@link IotDailySyncJob} 每日拉取。
 */
@Component
public class IotMeterHourlyPullJob {

    private static final Logger log = LoggerFactory.getLogger(IotMeterHourlyPullJob.class);

    private final IotSyncService syncService;
    private final IamTenantMapper tenantMapper;
    private final IotSettings settings;

    public IotMeterHourlyPullJob(IotSyncService syncService, IamTenantMapper tenantMapper,
                                 IotSettings settings) {
        this.syncService = syncService;
        this.tenantMapper = tenantMapper;
        this.settings = settings;
    }

    @Scheduled(cron = "0 5 * * * ?")
    public void pullHourly() {
        try {
            if (!settings.meterPeriodHourly("ELEC") && !settings.meterPeriodHourly("WATER")) {
                return;
            }
            for (IamTenant t : tenantMapper.selectList(new LambdaQueryWrapper<IamTenant>()
                    .eq(IamTenant::getStatus, "ENABLED"))) {
                TenantContext.set(com.yundao.bp.common.tenant.TenantInfo.of(t.getTenantCode(), null));
                try {
                    syncService.pullMeters(LocalDate.now());
                } catch (Exception e) {
                    log.warn("租户 {} 小时级表计拉取失败：{}", t.getTenantCode(), e.getMessage());
                } finally {
                    TenantContext.clear();
                }
            }
        } catch (Exception e) {
            log.warn("小时级表计拉取作业异常：{}", e.getMessage());
        }
    }
}
