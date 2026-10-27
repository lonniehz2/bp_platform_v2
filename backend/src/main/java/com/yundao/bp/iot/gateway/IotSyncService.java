package com.yundao.bp.iot.gateway;

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
