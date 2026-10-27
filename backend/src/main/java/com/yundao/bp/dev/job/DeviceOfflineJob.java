package com.yundao.bp.dev.job;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.entity.DevEvent;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.dev.mapper.DevEventMapper;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.iot.config.IotSettings;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 离线判定：超过阈值无心跳的在线设备置离线，并生成 OFFLINE 事件。
 *
 * <p>阈值取系统参数 {@code iot.offline.thresholdSeconds}（默认 180 秒）。
 * 定时任务没有请求上下文，按租户逐个执行。
 */
@Component
public class DeviceOfflineJob {

    private static final Logger log = LoggerFactory.getLogger(DeviceOfflineJob.class);

    private final DevDeviceMapper deviceMapper;
    private final DevEventMapper eventMapper;
    private final IotSettings settings;
    private final SnowflakeIdGenerator idGen;
    private final IamTenantMapper tenantMapper;

    public DeviceOfflineJob(DevDeviceMapper deviceMapper, DevEventMapper eventMapper,
                            IotSettings settings, SnowflakeIdGenerator idGen,
                            IamTenantMapper tenantMapper) {
        this.deviceMapper = deviceMapper;
        this.eventMapper = eventMapper;
        this.settings = settings;
        this.idGen = idGen;
        this.tenantMapper = tenantMapper;
    }

    @Scheduled(initialDelay = 60_000, fixedDelay = 60_000)
    public void sweep() {
        for (String tenantId : tenantCodes()) {
            try {
                TenantContext.set(TenantInfo.of(tenantId, null));
                runForTenant(tenantId);
            } catch (Exception e) {
                log.warn("离线判定失败 tenant={}: {}", tenantId, e.getMessage());
            } finally {
                TenantContext.clear();
            }
        }
    }

    private void runForTenant(String tenantId) {
        int threshold = Math.max(30, settings.offlineThresholdSeconds());
        LocalDateTime deadline = LocalDateTime.now().minusSeconds(threshold);
        List<DevDevice> online = deviceMapper.selectList(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getOnlineStatus, 1)
                .orderByAsc(DevDevice::getId)
                .last("LIMIT 500"));
        // 预取当天已生成的自动离线事件，避免逐台 selectCount
        java.util.Set<String> existing = new java.util.HashSet<>();
        for (DevEvent e : eventMapper.selectList(new LambdaQueryWrapper<DevEvent>()
                .likeRight(DevEvent::getEventId, "AUTO-OFF-")
                .like(DevEvent::getEventId, LocalDateTime.now().toLocalDate().toString()))) {
            existing.add(e.getEventId());
        }
        int n = 0;
        for (DevDevice d : online) {
            LocalDateTime last = d.getLastReportTime() != null
                    ? d.getLastReportTime() : d.getUpdateTime();
            if (last != null && last.isAfter(deadline)) {
                continue;
            }
            d.setOnlineStatus(0);
            d.setOfflineTime(LocalDateTime.now());
            d.setUpdateTime(LocalDateTime.now());
            deviceMapper.updateById(d);

            String eventId = "AUTO-OFF-" + d.getDeviceId() + "-" + LocalDateTime.now().toLocalDate();
            if (!existing.contains(eventId)) {
                existing.add(eventId);
                DevEvent e = new DevEvent();
                e.setId(idGen.nextId());
                e.setTenantId(tenantId);
                e.setOrgId(d.getOrgId());
                e.setSpaceId(d.getSpaceId());
                e.setDeviceId(d.getDeviceId());
                e.setIdentifier("OFFLINE");
                e.setEventLevel("WARN");
                e.setEventTime(LocalDateTime.now());
                e.setBody("{\"reason\":\"心跳超时 " + threshold + " 秒\"}");
                e.setHandled(0);
                e.setIsDeleted(0);
                e.setCreateTime(LocalDateTime.now());
                e.setEventId(eventId);
                try {
                    eventMapper.insert(e);
                } catch (Exception ex) {
                    log.debug("离线事件写入跳过: {}", ex.getMessage());
                }
            }
            n++;
        }
        if (n > 0) {
            log.info("离线判定 tenant={}：{} 台设备置离线", tenantId, n);
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
