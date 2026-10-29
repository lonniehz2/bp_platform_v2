# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\gov\service\impl\GovReportServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if 'MAX_REPORT_RECORDS' not in s:
    s = s.replace('''        List<Map<String, Object>> records = collect(reportType, dateFrom, dateTo);
        t.setRecordCount(records.size());''',
                  '''        List<Map<String, Object>> records = collect(reportType, dateFrom, dateTo);
        // 单次报文上限：数千条同步生成会让页面等待数分钟，这里限制并明确提示
        final int maxRecords = 500;
        int totalRecords = records.size();
        boolean truncated = totalRecords > maxRecords;
        if (truncated) {
            records = new ArrayList<>(records.subList(0, maxRecords));
        }
        t.setRecordCount(records.size());''', 1)
    s = s.replace('''        t.setFailDetail(errors.isEmpty() ? null : String.join("；", errors));''',
                  '''        String note = truncated
                ? "数据总量 " + totalRecords + " 条，单次最多报送 " + maxRecords
                  + " 条（前 " + maxRecords + " 条），请按日期/范围分批"
                : null;
        t.setFailDetail(note != null ? note
                : (errors.isEmpty() ? null : String.join("；", errors)));''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('报送上限已加')
else:
    print('already')
