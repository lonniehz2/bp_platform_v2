# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\gov\service\impl\GovReportServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if 'report-timing' not in s:
    s = s.replace('''        List<Map<String, Object>> records = collect(reportType, dateFrom, dateTo);''',
                  '''        long tCollect0 = System.currentTimeMillis();
        List<Map<String, Object>> records = collect(reportType, dateFrom, dateTo);
        log.info("report-timing collect={}ms n={}", System.currentTimeMillis() - tCollect0,
                records.size());''', 1)
    s = s.replace('''        if (!pending.isEmpty()) {
            jdbcBatch(pending);
        }''',
                  '''        long tBatch0 = System.currentTimeMillis();
        if (!pending.isEmpty()) {
            jdbcBatch(pending);
        }
        log.info("report-timing insert={}ms n={}", System.currentTimeMillis() - tBatch0,
                pending.size());''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('timing added')
else:
    print('already')
