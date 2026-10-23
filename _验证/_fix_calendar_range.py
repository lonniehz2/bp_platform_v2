# -*- coding: utf-8 -*-
"""按实体真实字段修正 setPriceRange 实现（calDate / priceOverride / calMapper）。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', 'src',
                 'main', 'java', 'com', 'yundao', 'bp', 'asset', 'service', 'impl',
                 'HouseCalendarServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

start = s.find('    public int setPriceRange(')
if start < 0:
    raise SystemExit('未找到 setPriceRange')
# 找到该方法结束（下一个 '\n    @Override' 或结尾）
end = s.find('\n    @Override', start)
if end < 0:
    end = s.rfind('}')

new_impl = '''    public int setPriceRange(Long houseId, java.time.LocalDate start, java.time.LocalDate end,
                             java.math.BigDecimal price, java.math.BigDecimal weekendPrice) {
        if (price == null || price.compareTo(java.math.BigDecimal.ZERO) < 0) {
            throw com.yundao.bp.common.exception.BizException.paramInvalid("价格不能为空且不能为负");
        }
        validateRange(start, end, true);
        ensureRange(houseId, start, end);
        java.util.List<com.yundao.bp.asset.entity.AssetHouseCalendar> cells =
                loadRows(houseId, start, end);
        int n = 0;
        for (com.yundao.bp.asset.entity.AssetHouseCalendar c : cells) {
            String st = c.getDayStatus();
            if ("BOOKED".equals(st) || "OCCUPIED".equals(st)) {
                continue;   // 已占用不改价，避免影响已成交订单
            }
            java.math.BigDecimal target = price;
            if (weekendPrice != null) {
                java.time.DayOfWeek dow = c.getCalDate().getDayOfWeek();
                if (dow == java.time.DayOfWeek.SATURDAY || dow == java.time.DayOfWeek.SUNDAY) {
                    target = weekendPrice;
                }
            }
            c.setPriceOverride(target);
            c.setUpdateTime(java.time.LocalDateTime.now());
            calMapper.updateById(c);
            n++;
        }
        log.info("日房态批量改价 houseId={} {}~{} 平日={} 周末={}，更新 {} 天",
                houseId, start, end, price, weekendPrice, n);
        return n;
    }
'''

s = s[:start] + new_impl + s[end:]
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('setPriceRange 已按真实字段重写')
