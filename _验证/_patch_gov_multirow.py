# -*- coding: utf-8 -*-
"""报送明细改多行 INSERT，去掉 500 条限制（保留 2 万安全上限）。"""
import io
import re

p = r'..\backend\src\main\java\com\yundao\bp\gov\service\impl\GovReportServiceImpl.java'
s = io.open(p, encoding='utf-8').read()

# 1) 上限 500 -> 20000
s = s.replace('final int maxRecords = 500;', 'final int maxRecords = 20000;', 1)

# 2) jdbcBatch 改为分块多行 INSERT
start = s.find('    private void jdbcBatch(List<GovReportDetail> list) {')
if start < 0:
    print('jdbcBatch not found')
    raise SystemExit
end = s.find('    private void writeAdapterLog(', start)
new_method = '''    private void jdbcBatch(List<GovReportDetail> list) {
        if (jdbc == null) {
            com.baomidou.mybatisplus.extension.toolkit.Db.saveBatch(list, 500);
            return;
        }
        final int chunk = 200;
        for (int from = 0; from < list.size(); from += chunk) {
            int to = Math.min(from + chunk, list.size());
            StringBuilder sql = new StringBuilder(
                    "insert into bp_gov_report_detail (id, tenant_id, task_id, biz_type, "
                            + "biz_id, external_id, sync_status, error_code, error_msg, "
                            + "request_data, response_data, create_time) values ");
            java.util.List<Object> args = new java.util.ArrayList<>();
            for (int i = from; i < to; i++) {
                GovReportDetail d = list.get(i);
                if (i > from) {
                    sql.append(",");
                }
                sql.append("(?,?,?,?,?,?,?,?,?,?,?,?)");
                args.add(d.getId());
                args.add(d.getTenantId());
                args.add(d.getTaskId());
                args.add(d.getBizType());
                args.add(d.getBizId() == null ? 0L : d.getBizId());
                args.add(d.getExternalId());
                args.add(d.getSyncStatus());
                args.add(d.getErrorCode());
                args.add(d.getErrorMsg());
                args.add(d.getRequestData());
                args.add(null);
                args.add(java.sql.Timestamp.valueOf(d.getCreateTime() == null
                        ? java.time.LocalDateTime.now() : d.getCreateTime()));
            }
            jdbc.update(sql.toString(), args.toArray());
        }
    }

'''
s = s[:start] + new_method + s[end:]
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('multi-row insert ready')
