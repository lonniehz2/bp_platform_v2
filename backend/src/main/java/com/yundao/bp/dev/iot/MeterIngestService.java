package com.yundao.bp.dev.iot;

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
        return ingest(meterNo, deviceId, meterType, reading, null, null, readTime, source);
    }

    /** 带倍率/单位的入库；用量 =（本次 − 上次）× 倍率。 */
    public boolean ingest(String meterNo, String deviceId, String meterType, BigDecimal reading,
                          BigDecimal multiplier, String unit,
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
        BigDecimal m = multiplier == null || multiplier.compareTo(BigDecimal.ZERO) <= 0
                ? BigDecimal.ONE : multiplier;
        BigDecimal usage = reading.subtract(prevReading).multiply(m);
        if (usage.compareTo(BigDecimal.ZERO) < 0) {
            usage = BigDecimal.ZERO;
        }
        usage = usage.setScale(2, RoundingMode.HALF_UP);
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
        e.setMultiplier(m);
        e.setUnit(unit == null || unit.isBlank() ? "kWh" : unit);
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
