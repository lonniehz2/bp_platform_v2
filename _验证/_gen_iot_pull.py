# -*- coding: utf-8 -*-
"""表计拉取、设备同步、告警联动工单。"""
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


# ---------- 客户端抽象 ----------
write('dev/iot/MeterPullClient.java', '''package com.yundao.bp.dev.iot;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 表计读数拉取（平台 → IoT）。配置 {@code bp.dev.meter-mode=mock|real}。
 *
 * <p>与设备主动上报（回调 meter）互为补充：本接口用于补数/对账。
 */
public interface MeterPullClient {

    List<Reading> pull(List<String> meterNos, LocalDate from, LocalDate to);

    record Reading(String meterNo, String deviceId, String meterType,
                   BigDecimal reading, BigDecimal multiplier, LocalDateTime readTime) {
    }
}
''')

write('dev/iot/MockMeterPullClient.java', '''package com.yundao.bp.dev.iot;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟拉取：返回空列表，页面/任务可跑通流程。 */
@Component
@ConditionalOnProperty(name = "bp.dev.meter-mode", havingValue = "mock", matchIfMissing = true)
public class MockMeterPullClient implements MeterPullClient {

    @Override
    public List<Reading> pull(List<String> meterNos, LocalDate from, LocalDate to) {
        return new ArrayList<>();
    }
}
''')

write('dev/iot/DeviceInventoryClient.java', '''package com.yundao.bp.dev.iot;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 设备台账拉取（平台 → IoT）。配置 {@code bp.dev.device-mode=mock|real}。
 *
 * <p>用于增量同步：按更新时间拉取设备，写入 {@code bp_dev_device}。
 */
public interface DeviceInventoryClient {

    List<DeviceInfo> fetch(LocalDateTime since);

    record DeviceInfo(String deviceId, String deviceMac, String deviceName, String deviceType,
                      String deviceModel, String firmware, Integer onlineStatus,
                      Integer battery, String rssi, LocalDateTime lastReportTime,
                      String installAddress) {
    }
}
''')

write('dev/iot/MockDeviceInventoryClient.java', '''package com.yundao.bp.dev.iot;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

/** 联调前的模拟台账拉取：返回空列表。 */
@Component
@ConditionalOnProperty(name = "bp.dev.device-mode", havingValue = "mock", matchIfMissing = true)
public class MockDeviceInventoryClient implements DeviceInventoryClient {

    @Override
    public List<DeviceInfo> fetch(LocalDateTime since) {
        return new ArrayList<>();
    }
}
''')

# ---------- 表计入库（回调与拉取共用） ----------
write('dev/iot/MeterIngestService.java', '''package com.yundao.bp.dev.iot;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.asset.entity.AssetHouse;
import com.yundao.bp.asset.mapper.AssetHouseMapper;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.entity.FinMeterReading;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.mapper.FinMeterReadingMapper;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/** 表计读数入库：设备→空间→房源、表类型→收费项目，按 deviceId+readDate 去重。 */
@Service
public class MeterIngestService {

    private static final Logger log = LoggerFactory.getLogger(MeterIngestService.class);

    private final DevDeviceMapper deviceMapper;
    private final AssetHouseMapper houseMapper;
    private final FinFeeItemMapper feeItemMapper;
    private final FinMeterReadingMapper meterMapper;
    private final SnowflakeIdGenerator idGen;

    public MeterIngestService(DevDeviceMapper deviceMapper, AssetHouseMapper houseMapper,
                              FinFeeItemMapper feeItemMapper, FinMeterReadingMapper meterMapper,
                              SnowflakeIdGenerator idGen) {
        this.deviceMapper = deviceMapper;
        this.houseMapper = houseMapper;
        this.feeItemMapper = feeItemMapper;
        this.meterMapper = meterMapper;
        this.idGen = idGen;
    }

    /**
     * 入库一条读数。
     *
     * @return true=已入库，false=缺映射或重复被跳过
     */
    public boolean ingest(String meterNo, String deviceId, String meterType, BigDecimal reading,
                          LocalDateTime readTime, String source) {
        DevDevice d = findDevice(deviceId, meterNo);
        Long houseId = d == null ? null : findHouseId(d.getSpaceId());
        Long feeItemId = findFeeItemId(meterType);
        if (houseId == null || feeItemId == null) {
            log.warn("表计读数未入库（缺房源或收费项目） meter={} type={} device={}",
                    meterNo, meterType, deviceId);
            return false;
        }
        LocalDate readDate = readTime == null ? LocalDate.now() : readTime.toLocalDate();
        String meterKey = meterNo != null ? meterNo : deviceId;
        Long dup = meterMapper.selectCount(new LambdaQueryWrapper<FinMeterReading>()
                .eq(FinMeterReading::getDeviceId, meterKey)
                .eq(FinMeterReading::getReadDate, readDate));
        if (dup != null && dup > 0) {
            return false;
        }
        FinMeterReading prev = meterMapper.selectOne(new LambdaQueryWrapper<FinMeterReading>()
                .eq(FinMeterReading::getHouseId, houseId)
                .eq(FinMeterReading::getFeeItemId, feeItemId)
                .orderByDesc(FinMeterReading::getReadDate).last("LIMIT 1"));
        BigDecimal prevReading = prev == null ? BigDecimal.ZERO : prev.getReading();
        BigDecimal usage = reading.subtract(prevReading);
        if (usage.compareTo(BigDecimal.ZERO) < 0) {
            usage = BigDecimal.ZERO;
        }
        BigDecimal price = BigDecimal.ZERO;
        FinFeeItem item = feeItemMapper.selectById(feeItemId);
        if (item != null && item.getUnitPrice() != null) {
            price = item.getUnitPrice();
        }
        FinMeterReading e = new FinMeterReading();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setOrgId(d == null ? null : d.getOrgId());
        e.setHouseId(houseId);
        e.setFeeItemId(feeItemId);
        e.setDeviceId(meterKey);
        e.setReadDate(readDate);
        e.setReading(reading);
        e.setPrevReading(prevReading);
        e.setUsageAmount(usage);
        e.setUnitPrice(price);
        e.setAmount(usage.multiply(price).setScale(2, RoundingMode.HALF_UP));
        e.setBillStatus("UNBILLED");
        e.setRemark("IoT " + (source == null ? "PUSH" : source));
        e.setIsDeleted(0);
        e.setCreateTime(LocalDateTime.now());
        meterMapper.insert(e);
        return true;
    }

    private DevDevice findDevice(String deviceId, String meterNo) {
        if (deviceId != null && !deviceId.isBlank()) {
            DevDevice d = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceId, deviceId).last("LIMIT 1"));
            if (d != null) {
                return d;
            }
        }
        if (meterNo != null && !meterNo.isBlank()) {
            return deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceId, meterNo).last("LIMIT 1"));
        }
        return null;
    }

    private Long findHouseId(Long spaceId) {
        if (spaceId == null) {
            return null;
        }
        AssetHouse h = houseMapper.selectOne(new LambdaQueryWrapper<AssetHouse>()
                .eq(AssetHouse::getSpaceId, spaceId).last("LIMIT 1"));
        return h == null ? null : h.getId();
    }

    private Long findFeeItemId(String meterType) {
        if (meterType == null) {
            return null;
        }
        List<String> codes = switch (meterType.toUpperCase()) {
            case "ELEC" -> List.of("ELEC", "ELECTRIC", "电费");
            case "WATER" -> List.of("WATER", "水费");
            case "GAS" -> List.of("GAS", "燃气费");
            case "HEAT" -> List.of("HEAT", "热力费");
            default -> List.of(meterType.toUpperCase());
        };
        for (String code : codes) {
            FinFeeItem item = feeItemMapper.selectOne(new LambdaQueryWrapper<FinFeeItem>()
                    .eq(FinFeeItem::getItemCode, code).last("LIMIT 1"));
            if (item != null) {
                return item.getId();
            }
        }
        FinFeeItem any = feeItemMapper.selectOne(new LambdaQueryWrapper<FinFeeItem>()
                .eq(FinFeeItem::getCalcMode, "METER")
                .eq(FinFeeItem::getStatus, "ENABLED").last("LIMIT 1"));
        return any == null ? null : any.getId();
    }
}
''')

print('客户端与入库服务完成')
