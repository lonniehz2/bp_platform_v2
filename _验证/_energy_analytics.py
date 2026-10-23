# -*- coding: utf-8 -*-
"""园区能耗分析：按月份统计用量/金额，并给出楼栋与房源排名。

接口：GET /fin/meter-readings/analytics?orgId=&months=6
口径：同一房源按抄表日期排序，用量 = 本次读数 − 上次读数（跨月自然衔接）；
      金额 = 用量 × 收费项单价。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin')

# ---------- Service 接口 ----------
S = os.path.join(J, 'service', 'MeterReadingService.java')
s = io.open(S, encoding='utf-8').read()
if 'analytics' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /** 能耗分析：月度用量/金额 + 楼栋与房源排名。 */
    java.util.Map<String, Object> analytics(Long orgId, int months);
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('MeterReadingService：analytics 已加')

# ---------- 实现 ----------
I = os.path.join(J, 'service', 'impl', 'MeterReadingServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'analytics' not in s:
    inject = '''
    /** 房源（能耗分析取楼栋归属） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetHouseMapper anaHouseMapper;

    /** 空间（楼栋名） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetSpaceMapper anaSpaceMapper;

    /** 收费项（单价） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.fin.mapper.FinFeeItemMapper anaFeeItemMapper;
'''
    if 'anaHouseMapper' not in s:
        j = s.find('    public MeterReadingServiceImpl(')
        s = s[:j] + inject + '\n' + s[j:]

    impl = '''
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
        if (anaFeeItemMapper != null) {
            for (com.yundao.bp.fin.entity.FinFeeItem it : anaFeeItemMapper.selectList(
                    new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<>())) {
                priceOf.put(it.getId(), it.getUnitPrice());
            }
        }

        java.util.Map<Long, com.yundao.bp.fin.entity.FinMeterReading> prev = new java.util.HashMap<>();
        java.util.Map<String, java.math.BigDecimal> monthUsage = new java.util.TreeMap<>();
        java.util.Map<String, java.math.BigDecimal> monthAmount = new java.util.TreeMap<>();
        java.util.Map<String, Integer> monthReadings = new java.util.HashMap<>();
        java.util.Map<Long, java.math.BigDecimal> houseUsage = new java.util.HashMap<>();

        for (com.yundao.bp.fin.entity.FinMeterReading r : list) {
            String month = r.getReadDate() == null ? "" : r.getReadDate().toString().substring(0, 7);
            monthReadings.merge(month, 1, Integer::sum);
            com.yundao.bp.fin.entity.FinMeterReading last = prev.get(r.getHouseId());
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
                }
            }
            prev.put(r.getHouseId(), r);
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
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('MeterReadingServiceImpl：analytics 已实现')

# ---------- Controller ----------
C = os.path.join(J, 'controller', 'MeterReadingController.java')
s = io.open(C, encoding='utf-8').read()
if 'analytics' not in s:
    block = '''
    /** 能耗分析：月度用量/金额 + 楼栋与房源排名。 */
    @GetMapping("/analytics")
    public R<java.util.Map<String, Object>> analytics(
            @RequestParam(required = false) Long orgId,
            @RequestParam(defaultValue = "6") int months) {
        return R.ok(meterReadingService.analytics(orgId, months));
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + block + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('MeterReadingController：/analytics 已加')

print('完成')
