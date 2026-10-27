# -*- coding: utf-8 -*-
"""表计倍率/单位：实体、入库、回调、拉取、页面。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# 1) 实体
p = os.path.join(BE, 'fin', 'entity', 'FinMeterReading.java')
s = io.open(p, encoding='utf-8').read()
if 'multiplier' not in s:
    s = s.replace('''    private BigDecimal prevReading;''', '''    private BigDecimal prevReading;
    /** 倍率：用量 =（本次−上次）× 倍率 */
    private BigDecimal multiplier;
    /** 单位：kWh / m3 */
    private String unit;''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('实体已加字段')

# 2) 入库服务：新签名 + 倍率换算
p = os.path.join(BE, 'dev', 'iot', 'MeterIngestService.java')
s = io.open(p, encoding='utf-8').read()
if 'multiplier' not in s:
    s = s.replace('''    public boolean ingest(String meterNo, String deviceId, String meterType, BigDecimal reading,
                          LocalDateTime readTime, String source) {''',
                  '''    public boolean ingest(String meterNo, String deviceId, String meterType, BigDecimal reading,
                          LocalDateTime readTime, String source) {
        return ingest(meterNo, deviceId, meterType, reading, null, null, readTime, source);
    }

    /** 带倍率/单位的入库；用量 =（本次 − 上次）× 倍率。 */
    public boolean ingest(String meterNo, String deviceId, String meterType, BigDecimal reading,
                          BigDecimal multiplier, String unit,
                          LocalDateTime readTime, String source) {''', 1)
    s = s.replace('''        BigDecimal usage = reading.subtract(prevReading);
        if (usage.compareTo(BigDecimal.ZERO) < 0) {
            usage = BigDecimal.ZERO;
        }''', '''        BigDecimal m = multiplier == null || multiplier.compareTo(BigDecimal.ZERO) <= 0
                ? BigDecimal.ONE : multiplier;
        BigDecimal usage = reading.subtract(prevReading).multiply(m);
        if (usage.compareTo(BigDecimal.ZERO) < 0) {
            usage = BigDecimal.ZERO;
        }
        usage = usage.setScale(2, RoundingMode.HALF_UP);''', 1)
    s = s.replace('''        e.setUsageAmount(usage);''', '''        e.setMultiplier(m);
        e.setUnit(unit == null || unit.isBlank() ? "kWh" : unit);
        e.setUsageAmount(usage);''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('入库服务已支持倍率')

# 3) 回调：读取 multiplier / unit
p = os.path.join(BE, 'iot', 'gateway', 'IotCallbackService.java')
s = io.open(p, encoding='utf-8').read()
s = s.replace('''            meterIngest.ingest(text(x, "meterNo"), text(x, "deviceId"),
                    text(x, "meterType"), x.path("reading").decimalValue(),
                    parseTime(text(x, "readTime")),
                    text(x, "source") == null ? "PUSH" : text(x, "source"));''',
              '''            meterIngest.ingest(text(x, "meterNo"), text(x, "deviceId"),
                    text(x, "meterType"), x.path("reading").decimalValue(),
                    x.has("multiplier") ? x.path("multiplier").decimalValue() : null,
                    text(x, "unit"),
                    parseTime(text(x, "readTime")),
                    text(x, "source") == null ? "PUSH" : text(x, "source"));''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('回调已传倍率/单位')

# 4) 拉取同步：使用 Reading.multiplier
p = os.path.join(BE, 'iot', 'gateway', 'IotSyncService.java')
s = io.open(p, encoding='utf-8').read()
if 'r.multiplier()' not in s:
    s = s.replace('''            if (meterIngest.ingest(r.meterNo(), r.deviceId(), r.meterType(), r.reading(),
                    r.readTime(), "PULL")) {''',
                  '''            if (meterIngest.ingest(r.meterNo(), r.deviceId(), r.meterType(), r.reading(),
                    r.multiplier(), null, r.readTime(), "PULL")) {''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('拉取同步已用倍率')
