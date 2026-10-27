# -*- coding: utf-8 -*-
"""设备同步服务、表计拉取服务、告警转工单、接口与 Job。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
BK = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')


def write(rel, body):
    path = os.path.join(BK, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        print('跳过(已存在)', rel)
        return
    io.open(path, 'w', encoding='utf-8', newline='').write(body)
    print('创建', rel)


write('iot/gateway/IotSyncService.java', '''package com.yundao.bp.iot.gateway;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.iot.DeviceInventoryClient;
import com.yundao.bp.dev.iot.MeterIngestService;
import com.yundao.bp.dev.iot.MeterPullClient;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 与 IoT 的定期同步：设备台账增量、表计读数补拉。 */
@Service
public class IotSyncService {

    private static final Logger log = LoggerFactory.getLogger(IotSyncService.class);

    private final DeviceInventoryClient deviceClient;
    private final MeterPullClient meterClient;
    private final DevDeviceMapper deviceMapper;
    private final MeterIngestService meterIngest;
    private final SnowflakeIdGenerator idGen;

    public IotSyncService(DeviceInventoryClient deviceClient, MeterPullClient meterClient,
                          DevDeviceMapper deviceMapper, MeterIngestService meterIngest,
                          SnowflakeIdGenerator idGen) {
        this.deviceClient = deviceClient;
        this.meterClient = meterClient;
        this.deviceMapper = deviceMapper;
        this.meterIngest = meterIngest;
        this.idGen = idGen;
    }

    /** 设备台账同步：按 deviceId upsert，返回统计。 */
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> syncDevices(LocalDateTime since) {
        List<DeviceInventoryClient.DeviceInfo> list =
                deviceClient.fetch(since == null ? LocalDateTime.now().minusDays(1) : since);
        int created = 0;
        int updated = 0;
        for (DeviceInventoryClient.DeviceInfo info : list) {
            if (info.deviceId() == null || info.deviceId().isBlank()) {
                continue;
            }
            DevDevice exist = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceId, info.deviceId()).last("LIMIT 1"));
            if (exist == null) {
                DevDevice d = new DevDevice();
                d.setId(idGen.nextId());
                d.setTenantId(TenantContext.tenantId());
                d.setDeviceId(info.deviceId());
                d.setDeviceMac(info.deviceMac());
                d.setDeviceName(info.deviceName());
                d.setDeviceType(info.deviceType());
                d.setDeviceModel(info.deviceModel());
                d.setOnlineStatus(info.onlineStatus() == null ? 0 : info.onlineStatus());
                d.setBattery(info.battery());
                d.setRssi(info.rssi());
                d.setLastReportTime(info.lastReportTime());
                d.setInstallAddress(info.installAddress());
                d.setIsPublic(0);
                d.setCreateTime(LocalDateTime.now());
                d.setUpdateTime(LocalDateTime.now());
                d.setIsDeleted(0);
                deviceMapper.insert(d);
                created++;
            } else {
                if (info.onlineStatus() != null) {
                    exist.setOnlineStatus(info.onlineStatus());
                }
                if (info.battery() != null) {
                    exist.setBattery(info.battery());
                }
                if (info.rssi() != null) {
                    exist.setRssi(info.rssi());
                }
                if (info.lastReportTime() != null) {
                    exist.setLastReportTime(info.lastReportTime());
                }
                exist.setUpdateTime(LocalDateTime.now());
                deviceMapper.updateById(exist);
                updated++;
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("fetched", list.size());
        out.put("created", created);
        out.put("updated", updated);
        out.put("syncedAt", LocalDateTime.now().toString());
        log.info("设备同步：拉取 {}，新增 {}，更新 {}", list.size(), created, updated);
        return out;
    }

    /** 表计读数补拉：按指定日期拉取所有表计设备的读数并入库。 */
    public Map<String, Object> pullMeters(LocalDate date) {
        LocalDate day = date == null ? LocalDate.now().minusDays(1) : date;
        List<DevDevice> meters = deviceMapper.selectList(new LambdaQueryWrapper<DevDevice>()
                .in(DevDevice::getDeviceType, List.of("ELEC_METER", "WATER_METER", "GAS_METER",
                        "HEAT_METER", "METER"))
                .orderByAsc(DevDevice::getId).last("LIMIT 200"));
        List<String> meterNos = new ArrayList<>();
        for (DevDevice d : meters) {
            meterNos.add(d.getDeviceId());
        }
        List<MeterPullClient.Reading> readings = meterClient.pull(meterNos, day, day);
        int ok = 0;
        for (MeterPullClient.Reading r : readings) {
            if (meterIngest.ingest(r.meterNo(), r.deviceId(), r.meterType(), r.reading(),
                    r.readTime(), "PULL")) {
                ok++;
            }
        }
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("date", day.toString());
        out.put("meters", meterNos.size());
        out.put("fetched", readings.size());
        out.put("ingested", ok);
        log.info("表计拉取 {}：表 {} 台，读数 {} 条，入库 {}", day, meterNos.size(),
                readings.size(), ok);
        return out;
    }
}
''')

# 定时任务
write('dev/job/IotDailySyncJob.java', '''package com.yundao.bp.dev.job;

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
''')

# 告警转工单
write('ops/service/DeviceAlertActionService.java', '''package com.yundao.bp.ops.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.dev.entity.DevEvent;
import com.yundao.bp.ops.dto.WorkOrderCreateCmd;
import com.yundao.bp.ops.entity.OpsWorkorder;
import com.yundao.bp.ops.mapper.OpsWorkorderMapper;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * 设备告警联动：严重级别事件自动生成工单（同设备同标题 24 小时内只生成一次）。
 */
@Service
public class DeviceAlertActionService {

    private static final Logger log = LoggerFactory.getLogger(DeviceAlertActionService.class);
    private static final List<String> AUTO_TYPES =
            List.of("DURESS", "TAMPER", "POWER_OVER", "OFFLINE", "LOW_BATTERY");

    private final WorkOrderService workOrderService;
    private final OpsWorkorderMapper workOrderMapper;

    public DeviceAlertActionService(WorkOrderService workOrderService,
                                    OpsWorkorderMapper workOrderMapper) {
        this.workOrderService = workOrderService;
        this.workOrderMapper = workOrderMapper;
    }

    /** 判断是否需要联动，并创建工单。返回工单号或 null。 */
    public String onDeviceEvent(DevEvent e) {
        if (e == null || e.getIdentifier() == null) {
            return null;
        }
        boolean serious = "CRITICAL".equals(e.getEventLevel())
                || AUTO_TYPES.contains(e.getIdentifier());
        if (!serious) {
            return null;
        }
        String title = "设备告警：" + label(e.getIdentifier()) + "（" + e.getDeviceId() + "）";
        Long dup = workOrderMapper.selectCount(new LambdaQueryWrapper<OpsWorkorder>()
                .eq(OpsWorkorder::getDeviceId, e.getDeviceId())
                .eq(OpsWorkorder::getOrderType, "ALERT")
                .ge(OpsWorkorder::getCreateTime, LocalDateTime.now().minusHours(24))
                .ne(OpsWorkorder::getOrderStatus, "CLOSED"));
        if (dup != null && dup > 0) {
            return null;
        }
        try {
            var vo = workOrderService.create(new WorkOrderCreateCmd(
                    "ALERT", "ALERT", title,
                    e.getBody() == null ? "设备事件自动转单" : e.getBody(),
                    e.getOrgId(), e.getSpaceId(), null, e.getDeviceId(), null,
                    null, null, null, null, null, null, null, null));
            return vo == null ? null : vo.workorderNo();
        } catch (Exception ex) {
            log.warn("告警转工单失败 device={}: {}", e.getDeviceId(), ex.getMessage());
            return null;
        }
    }

    private static String label(String id) {
        return switch (id) {
            case "DURESS" -> "胁迫告警";
            case "TAMPER" -> "防拆告警";
            case "POWER_OVER" -> "超功率告警";
            case "OFFLINE" -> "设备离线";
            case "LOW_BATTERY" -> "低电量";
            default -> id;
        };
    }
}
''')

# 接口
write('iot/gateway/IotSyncController.java', '''package com.yundao.bp.iot.gateway;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** IoT 同步操作：设备台账同步、表计补拉（供页面按钮与联调触发）。 */
@RestController
@RequestMapping("/api/v1/iot")
public class IotSyncController {

    private final IotSyncService syncService;

    public IotSyncController(IotSyncService syncService) {
        this.syncService = syncService;
    }

    @RequirePerm("asset:device:update")
    @PostMapping("/devices/sync")
    public R<Map<String, Object>> syncDevices(
            @RequestParam(required = false) Integer days) {
        int d = days == null || days <= 0 ? 1 : days;
        return R.ok(syncService.syncDevices(LocalDateTime.now().minusDays(d)));
    }

    @RequirePerm("fin:bill:create")
    @PostMapping("/meter/pull")
    public R<Map<String, Object>> pullMeters(
            @RequestParam(required = false) String date) {
        LocalDate day = date == null || date.isBlank() ? null : LocalDate.parse(date);
        return R.ok(syncService.pullMeters(day));
    }
}
''')

print('同步服务/任务/联动完成')
