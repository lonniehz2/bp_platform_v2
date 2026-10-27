# -*- coding: utf-8 -*-
"""表计上报周期：按类型解析 + 小时级拉取作业。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# 1) IotSettings：解析周期
p = os.path.join(BE, 'iot', 'config', 'IotSettings.java')
s = io.open(p, encoding='utf-8').read()
if 'meterPeriodHourly' not in s:
    s = s.replace('''    public String meterReportPeriod() {''', '''    /**
     * 某类表计是否按小时上报。配置格式 {@code ELEC:DAILY,WATER:HOURLY}，
     * 未配置的类型默认 DAILY。
     */
    public boolean meterPeriodHourly(String type) {
        if (type == null) {
            return false;
        }
        String raw = meterReportPeriod();
        if (raw == null) {
            return false;
        }
        String key = type.trim().toUpperCase();
        for (String part : raw.split("[,;]")) {
            String[] kv = part.split(":");
            if (kv.length == 2 && kv[0].trim().toUpperCase().equals(key)) {
                return "HOURLY".equalsIgnoreCase(kv[1].trim());
            }
        }
        return "HOURLY".equalsIgnoreCase(raw.trim());
    }

    public String meterReportPeriod() {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('IotSettings 已加周期解析')

# 2) 小时级拉取作业
p = os.path.join(BE, 'dev', 'job', 'IotMeterHourlyPullJob.java')
if not os.path.exists(p):
    code = '''package com.yundao.bp.dev.job;

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
                TenantContext.set(t.getTenantCode());
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
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(code)
    print('小时级拉取作业已创建')

# 3) capabilities 暴露周期
p = os.path.join(BE, 'iot', 'gateway', 'IotCapabilitiesController.java')
s = io.open(p, encoding='utf-8').read()
if 'meterPeriod' not in s:
    s = s.replace('''        out.put("callback", cb);''', '''        out.put("callback", cb);

        Map<String, Object> meter = new LinkedHashMap<>();
        meter.put("reportPeriod", settings.meterReportPeriod());
        meter.put("elecHourly", settings.meterPeriodHourly("ELEC"));
        meter.put("waterHourly", settings.meterPeriodHourly("WATER"));
        out.put("meter", meter);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('capabilities 已加表计周期')
