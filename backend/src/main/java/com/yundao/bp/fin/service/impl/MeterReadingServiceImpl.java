package com.yundao.bp.fin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.fin.dto.BillCreateCmd;
import com.yundao.bp.fin.dto.BillVO;
import com.yundao.bp.fin.dto.MeterReadingCmd;
import com.yundao.bp.fin.entity.FinFeeItem;
import com.yundao.bp.fin.entity.FinMeterReading;
import com.yundao.bp.fin.mapper.FinFeeItemMapper;
import com.yundao.bp.fin.mapper.FinMeterReadingMapper;
import com.yundao.bp.fin.service.BillingService;
import com.yundao.bp.fin.service.MeterReadingService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 能耗抄表：录入读数、算用量、一键出账。 */
@Service
public class MeterReadingServiceImpl implements MeterReadingService {

    private final FinMeterReadingMapper mapper;

    /** 房源（取组织） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper;

    /** 合同（取在租承租人） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.biz.mapper.BizContractMapper contractMapper;
    private final FinFeeItemMapper feeItemMapper;
    private final BillingService billingService;
    private final SnowflakeIdGenerator idGen;


    /** 房源（能耗分析取楼栋归属） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper anaHouseMapper;

    /** 空间（楼栋名） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetSpaceMapper anaSpaceMapper;

    /** 收费项（单价） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.mapper.FinFeeItemMapper anaFeeItemMapper;

    public MeterReadingServiceImpl(FinMeterReadingMapper mapper, FinFeeItemMapper feeItemMapper,
                                   BillingService billingService, SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.feeItemMapper = feeItemMapper;
        this.billingService = billingService;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public FinMeterReading record(MeterReadingCmd cmd) {
        FinFeeItem item = feeItemMapper.selectById(cmd.feeItemId());
        if (item == null) {
            throw BizException.notFound("收费项目");
        }
        if (!"METER".equals(item.getCalcMode())) {
            throw BizException.paramInvalid("该收费项目不是「按抄表」计费，请用批量出账");
        }
        LocalDate readDate = cmd.readDate() == null ? LocalDate.now() : cmd.readDate();

        // 上次读数：同房源同项目、读数日期早于本次的最近一条
        FinMeterReading prev = mapper.selectOne(new LambdaQueryWrapper<FinMeterReading>()
                .eq(FinMeterReading::getHouseId, cmd.houseId())
                .eq(FinMeterReading::getFeeItemId, cmd.feeItemId())
                .lt(FinMeterReading::getReadDate, readDate)
                .orderByDesc(FinMeterReading::getReadDate)
                .last("LIMIT 1"));
        BigDecimal prevReading = prev == null ? BigDecimal.ZERO : prev.getReading();
        if (cmd.reading().compareTo(prevReading) < 0) {
            throw BizException.paramInvalid("本次读数不能小于上次读数（上次 " + prevReading + "）");
        }
        BigDecimal usage = cmd.reading().subtract(prevReading);
        BigDecimal price = item.getUnitPrice() == null ? BigDecimal.ZERO : item.getUnitPrice();
        BigDecimal amount = usage.multiply(price).setScale(2, RoundingMode.HALF_UP);

        FinMeterReading e = new FinMeterReading();
        e.setId(idGen.nextId());
        e.setTenantId(TenantContext.tenantId());
        e.setOrgId(null);
        e.setHouseId(cmd.houseId());
        e.setFeeItemId(cmd.feeItemId());
        e.setReadDate(readDate);
        e.setReading(cmd.reading());
        e.setDeviceId(cmd.deviceId());
        e.setPrevReading(prevReading);
        e.setUsageAmount(usage);
        e.setUnitPrice(price);
        e.setAmount(amount);
        e.setBillStatus("UNBILLED");
        e.setRemark(cmd.remark());
        e.setIsDeleted(0);
        e.setCreateTime(LocalDateTime.now());
        mapper.insert(e);
        return e;
    }

    @Override
    public PageResult<FinMeterReading> page(long pageNum, long pageSize, Long houseId,
                                            Long feeItemId) {
        LambdaQueryWrapper<FinMeterReading> qw = new LambdaQueryWrapper<FinMeterReading>()
                .eq(houseId != null, FinMeterReading::getHouseId, houseId)
                .eq(feeItemId != null, FinMeterReading::getFeeItemId, feeItemId)
                .orderByDesc(FinMeterReading::getReadDate);
        var page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BillVO bill(Long readingId) {
        FinMeterReading e = mapper.selectById(readingId);
        if (e == null) {
            throw BizException.notFound("抄表记录");
        }
        if ("BILLED".equals(e.getBillStatus())) {
            throw BizException.paramInvalid("该抄表记录已出账");
        }
        String period = e.getReadDate().toString().substring(0, 7).replace("-", "");
        // 费用区间：上次抄表日（无则本次往前推一个月）→ 本次抄表日；截止日必须晚于起始日
        java.time.LocalDate start = e.getReadDate().minusMonths(1);
        com.yundao.bp.asset.entity.AssetHouse house = houseMapper == null
                ? null : houseMapper.selectById(e.getHouseId());
        java.time.LocalDate prevRead = null;
        FinMeterReading prev = mapper.selectOne(new LambdaQueryWrapper<FinMeterReading>()
                .eq(FinMeterReading::getHouseId, e.getHouseId())
                .eq(FinMeterReading::getFeeItemId, e.getFeeItemId())
                .lt(FinMeterReading::getReadDate, e.getReadDate())
                .orderByDesc(FinMeterReading::getReadDate)
                .last("LIMIT 1"));
        if (prev != null) {
            start = prev.getReadDate();
        }
        if (!e.getReadDate().isAfter(start)) {
            start = e.getReadDate().minusDays(1);
        }
        Long orgId = e.getOrgId() != null ? e.getOrgId()
                : (house == null ? null : house.getOrgId());
        // 在租合同（用于挂缴费人）
        com.yundao.bp.biz.entity.BizContract contract = contractMapper == null ? null
                : contractMapper.selectOne(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                <com.yundao.bp.biz.entity.BizContract>()
                                .eq(com.yundao.bp.biz.entity.BizContract::getHouseId, e.getHouseId())
                                .eq(com.yundao.bp.biz.entity.BizContract::getContractStatus,
                                        "EFFECTIVE")
                                .last("LIMIT 1"));
        BillCreateCmd cmd = new BillCreateCmd(
                e.getFeeItemId(), orgId,
                contract == null ? null : contract.getId(), e.getHouseId(),
                house == null ? null : house.getSpaceId(),
                contract == null ? null : contract.getLesseePersonId(),
                contract == null ? null : contract.getLesseeName(),
                contract == null ? null : contract.getLesseePhone(),
                period, start, e.getReadDate(),
                e.getAmount(), null, null, null, "METER", "抄表出账：" + e.getUsageAmount()
                + " × " + e.getUnitPrice());
        if (orgId != null && e.getOrgId() == null) {
            e.setOrgId(orgId);
        }
        BillVO bill = billingService.createBill(cmd);
        e.setBillStatus("BILLED");
        e.setBillId(bill.id());
        mapper.updateById(e);
        return bill;
    }

    @Override
    public java.util.Map<String, Object> analytics(Long orgId, int months) {
        int window = Math.max(1, Math.min(months, 24));
        if (anaHouseMapper == null || anaSpaceMapper == null) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("分析服务未就绪");
        }
        java.time.LocalDate from = java.time.LocalDate.now()
                .withDayOfMonth(1).minusMonths(window - 1);
        java.util.List<com.yundao.bp.fin.entity.FinMeterReading> list = mapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                        <com.yundao.bp.fin.entity.FinMeterReading>()
                        .ge(com.yundao.bp.fin.entity.FinMeterReading::getReadDate, from)
                        .orderByAsc(com.yundao.bp.fin.entity.FinMeterReading::getHouseId)
                        .orderByAsc(com.yundao.bp.fin.entity.FinMeterReading::getReadDate));

        // 单价（按收费项）
        java.util.Map<Long, java.math.BigDecimal> priceOf = new java.util.HashMap<>();
        java.util.Map<Long, String> itemName = new java.util.HashMap<>();
        if (anaFeeItemMapper != null) {
            for (com.yundao.bp.fin.entity.FinFeeItem it : anaFeeItemMapper.selectList(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>())) {
                priceOf.put(it.getId(), it.getUnitPrice());
                itemName.put(it.getId(), it.getItemName());
            }
        }

        // 关键：同一房源有多个计量项目（水/电/燃气），必须按「房源+项目」分别计算上期读数
        java.util.Map<String, com.yundao.bp.fin.entity.FinMeterReading> prev =
                new java.util.HashMap<>();
        java.util.Map<String, java.math.BigDecimal> monthUsage = new java.util.TreeMap<>();
        java.util.Map<String, java.math.BigDecimal> monthAmount = new java.util.TreeMap<>();
        java.util.Map<String, Integer> monthReadings = new java.util.HashMap<>();
        java.util.Map<Long, java.math.BigDecimal> houseUsage = new java.util.HashMap<>();
        java.util.Map<Long, java.math.BigDecimal> itemUsage = new java.util.HashMap<>();
        java.util.Map<Long, java.math.BigDecimal> itemAmount = new java.util.HashMap<>();
        java.util.Map<Long, Integer> itemReadings = new java.util.HashMap<>();

        for (com.yundao.bp.fin.entity.FinMeterReading r : list) {
            String month = r.getReadDate() == null ? "" : r.getReadDate().toString().substring(0, 7);
            monthReadings.merge(month, 1, Integer::sum);
            String key = r.getHouseId() + "#" + r.getFeeItemId();
            com.yundao.bp.fin.entity.FinMeterReading last = prev.get(key);
            if (last != null && last.getReading() != null && r.getReading() != null) {
                java.math.BigDecimal used = r.getReading().subtract(last.getReading());
                if (used.signum() > 0) {
                    monthUsage.merge(month, used, java.math.BigDecimal::add);
                    java.math.BigDecimal price = priceOf.get(r.getFeeItemId());
                    if (price != null) {
                        monthAmount.merge(month, used.multiply(price),
                                java.math.BigDecimal::add);
                    }
                    houseUsage.merge(r.getHouseId(), used, java.math.BigDecimal::add);
                    itemUsage.merge(r.getFeeItemId(), used, java.math.BigDecimal::add);
                    if (price != null) {
                        itemAmount.merge(r.getFeeItemId(), used.multiply(price),
                                java.math.BigDecimal::add);
                    }
                    itemReadings.merge(r.getFeeItemId(), 1, Integer::sum);
                }
            }
            prev.put(key, r);
        }

        java.util.List<java.util.Map<String, Object>> monthRows = new java.util.ArrayList<>();
        for (String m : monthReadings.keySet()) {
            java.util.Map<String, Object> row = new java.util.LinkedHashMap<>();
            row.put("month", m);
            row.put("readings", monthReadings.get(m));
            row.put("usage", monthUsage.getOrDefault(m, java.math.BigDecimal.ZERO)
                    .setScale(2, java.math.RoundingMode.HALF_UP));
            row.put("amount", monthAmount.getOrDefault(m, java.math.BigDecimal.ZERO)
                    .setScale(2, java.math.RoundingMode.HALF_UP));
            monthRows.add(row);
        }

        // 房源排名（前 10）与楼栋汇总
        java.util.List<java.util.Map.Entry<Long, java.math.BigDecimal>> ranked =
                new java.util.ArrayList<>(houseUsage.entrySet());
        ranked.sort((a, b) -> b.getValue().compareTo(a.getValue()));
        java.util.List<java.util.Map<String, Object>> topHouses = new java.util.ArrayList<>();
        java.util.Map<String, java.math.BigDecimal> byBuilding = new java.util.HashMap<>();
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetHouse> houseCache =
                new java.util.HashMap<>();
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetSpace> spaceCache =
                new java.util.HashMap<>();
        int rank = 0;
        for (java.util.Map.Entry<Long, java.math.BigDecimal> e : ranked) {
            com.yundao.bp.asset.entity.AssetHouse h = houseCache.get(e.getKey());
            if (h == null) {
                h = anaHouseMapper.selectById(e.getKey());
                if (h != null) {
                    houseCache.put(h.getId(), h);
                }
            }
            String building = buildingOf(h, spaceCache);
            byBuilding.merge(building, e.getValue(), java.math.BigDecimal::add);
            if (rank++ < 10) {
                java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
                m.put("houseId", String.valueOf(e.getKey()));
                m.put("houseCode", h == null ? null : h.getHouseCode());
                m.put("houseName", h == null ? null : h.getHouseName());
                m.put("building", building);
                m.put("usage", e.getValue().setScale(2, java.math.RoundingMode.HALF_UP));
                topHouses.add(m);
            }
        }
        java.util.List<java.util.Map<String, Object>> buildingRows = new java.util.ArrayList<>();
        java.util.List<java.util.Map.Entry<String, java.math.BigDecimal>> bl =
                new java.util.ArrayList<>(byBuilding.entrySet());
        bl.sort((a, b) -> b.getValue().compareTo(a.getValue()));
        for (java.util.Map.Entry<String, java.math.BigDecimal> e : bl) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("building", e.getKey());
            m.put("usage", e.getValue().setScale(2, java.math.RoundingMode.HALF_UP));
            buildingRows.add(m);
        }

        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("months", monthRows);
        out.put("topHouses", topHouses);
        out.put("byBuilding", buildingRows);
        java.util.List<java.util.Map<String, Object>> itemRows = new java.util.ArrayList<>();
        for (java.util.Map.Entry<Long, java.math.BigDecimal> e : itemUsage.entrySet()) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("feeItemId", String.valueOf(e.getKey()));
            m.put("feeItemName", itemName.get(e.getKey()));
            m.put("usage", e.getValue().setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("amount", itemAmount.getOrDefault(e.getKey(),
                    java.math.BigDecimal.ZERO).setScale(2, java.math.RoundingMode.HALF_UP));
            m.put("readings", itemReadings.getOrDefault(e.getKey(), 0));
            itemRows.add(m);
        }
        itemRows.sort((a, b) -> ((java.math.BigDecimal) b.get("usage"))
                .compareTo((java.math.BigDecimal) a.get("usage")));
        out.put("byFeeItem", itemRows);
        out.put("windowMonths", window);
        return out;
    }

    /** 从房源向上找到所属楼栋名称。 */
    private String buildingOf(com.yundao.bp.asset.entity.AssetHouse h,
                              java.util.Map<Long, com.yundao.bp.asset.entity.AssetSpace> cache) {
        if (h == null || h.getSpaceId() == null) {
            return "未知";
        }
        Long sid = h.getSpaceId();
        for (int depth = 0; depth < 6 && sid != null; depth++) {
            com.yundao.bp.asset.entity.AssetSpace sp = cache.get(sid);
            if (sp == null) {
                sp = anaSpaceMapper.selectById(sid);
                if (sp == null) {
                    break;
                }
                cache.put(sp.getId(), sp);
            }
            if ("BUILDING".equals(sp.getSpaceType())) {
                return sp.getSpaceName();
            }
            sid = sp.getParentId();
        }
        return "未知";
    }
}
