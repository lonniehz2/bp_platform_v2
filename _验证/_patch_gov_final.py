# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\gov\service\impl\GovReportServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
s = s.replace('final int maxRecords = 20000;', 'final int maxRecords = 500;', 1)
# 去掉临时计时日志
s = s.replace('''        long tCollect0 = System.currentTimeMillis();
        List<Map<String, Object>> records = collect(reportType, dateFrom, dateTo);
        log.info("report-timing collect={}ms n={}", System.currentTimeMillis() - tCollect0,
                records.size());''',
              '''        List<Map<String, Object>> records = collect(reportType, dateFrom, dateTo);''', 1)
s = s.replace('''        long tBatch0 = System.currentTimeMillis();
        if (!pending.isEmpty()) {
            jdbcBatch(pending);
        }
        log.info("report-timing insert={}ms n={}", System.currentTimeMillis() - tBatch0,
                pending.size());''',
              '''        if (!pending.isEmpty()) {
            jdbcBatch(pending);
        }''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('cap=500, timing removed')
