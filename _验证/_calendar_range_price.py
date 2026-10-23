# -*- coding: utf-8 -*-
"""日房态批量维护：按日期区间设置价格（可选周末价）与批量停用/恢复。

后端：POST /house-calendar/{houseId}/price-range
前端：日房态页新增「批量设置」入口
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'asset')

# ---------- Service 接口 ----------
S = os.path.join(J, 'service', 'HouseCalendarService.java')
s = io.open(S, encoding='utf-8').read()
if 'setPriceRange' not in s:
    i = s.rstrip().rfind('}')
    s = s[:i] + '''
    /**
     * 区间改价：把 [start, end] 的价格改为 price；weekendPrice 非空时，
     * 周六/周日用 weekendPrice 覆盖（酒店平日/周末差价）。
     *
     * <p>已占用（BOOKED/OCCUPIED）的日期不改价，避免影响已成交订单。
     *
     * @return 实际更新的天数
     */
    int setPriceRange(Long houseId, java.time.LocalDate start, java.time.LocalDate end,
                      java.math.BigDecimal price, java.math.BigDecimal weekendPrice);
''' + s[i:]
    io.open(S, 'w', encoding='utf-8', newline='').write(s)
    print('HouseCalendarService：setPriceRange 已加')

# ---------- 实现 ----------
I = os.path.join(J, 'service', 'impl', 'HouseCalendarServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'setPriceRange' not in s:
    impl = '''
    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
    public int setPriceRange(Long houseId, java.time.LocalDate start, java.time.LocalDate end,
                             java.math.BigDecimal price, java.math.BigDecimal weekendPrice) {
        if (price == null || price.signum() < 0) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("价格不能为空且不能为负");
        }
        validateRange(start, end, true);
        ensureRange(houseId, start, end);
        java.util.List<com.yundao.bp.asset.entity.AssetHouseCalendar> cells =
                calendarMapper.selectList(
                        new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper
                                <com.yundao.bp.asset.entity.AssetHouseCalendar>()
                                .eq(com.yundao.bp.asset.entity.AssetHouseCalendar::getHouseId, houseId)
                                .between(com.yundao.bp.asset.entity.AssetHouseCalendar::getCalendarDate,
                                        start, end));
        int n = 0;
        for (com.yundao.bp.asset.entity.AssetHouseCalendar c : cells) {
            String st = c.getDayStatus();
            boolean occupied = "BOOKED".equals(st) || "OCCUPIED".equals(st);
            if (occupied) {
                continue;
            }
            java.math.BigDecimal target = price;
            if (weekendPrice != null) {
                java.time.DayOfWeek dow = c.getCalendarDate().getDayOfWeek();
                if (dow == java.time.DayOfWeek.SATURDAY || dow == java.time.DayOfWeek.SUNDAY) {
                    target = weekendPrice;
                }
            }
            c.setPrice(target);
            c.setUpdateTime(java.time.LocalDateTime.now());
            calendarMapper.updateById(c);
            n++;
        }
        log.info("日房态批量改价 houseId={} {}~{} 平日={} 周末={}，更新 {} 天",
                houseId, start, end, price, weekendPrice, n);
        return n;
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + impl + s[i:]
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
    print('HouseCalendarServiceImpl：setPriceRange 已实现')

# ---------- Controller ----------
C = os.path.join(J, 'controller', 'HouseCalendarController.java')
s = io.open(C, encoding='utf-8').read()
if 'price-range' not in s:
    block = '''
    /** 区间改价（支持周末价），跳过已占用日期。 */
    @PostMapping("/{houseId}/price-range")
    public R<Integer> setPriceRange(@PathVariable Long houseId,
                                    @RequestBody PriceRangeCmd cmd) {
        return R.ok(calendarService.setPriceRange(houseId, cmd.start(), cmd.end(),
                cmd.price(), cmd.weekendPrice()));
    }
'''
    anchor = '    @PostMapping("/{houseId}/price")'
    if anchor in s:
        s = s.replace(anchor, block + '\n' + anchor, 1)
    i = s.rstrip().rfind('}')
    # 追加 record（放在最后一个 record 之后）
    s = s[:i] + '''
    public record PriceRangeCmd(
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            BigDecimal price, BigDecimal weekendPrice) {
    }
''' + s[i:]
    io.open(C, 'w', encoding='utf-8', newline='').write(s)
    print('HouseCalendarController：/price-range 已加')

print('完成')
