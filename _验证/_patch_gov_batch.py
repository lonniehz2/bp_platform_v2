# -*- coding: utf-8 -*-
import io

p = r'..\backend\src\main\java\com\yundao\bp\gov\service\impl\GovReportServiceImpl.java'
s = io.open(p, encoding='utf-8').read()
if 'jdbcBatch' in s:
    print('already')
    raise SystemExit

s = s.replace('''    private final GovReportDetailMapper detailMapper;''',
              '''    private final GovReportDetailMapper detailMapper;

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private org.springframework.jdbc.core.JdbcTemplate jdbc;''', 1)

s = s.replace('''        if (!pending.isEmpty()) {
            // 批量写入：逐条 insert 在数千条时会超时
            com.baomidou.mybatisplus.extension.toolkit.Db.saveBatch(pending, 500);
        }''',
              '''        if (!pending.isEmpty()) {
            jdbcBatch(pending);
        }''', 1)

helper = '''    /** 明细批量写入（JDBC batch，数千条也能在秒级完成）。 */
    private void jdbcBatch(List<GovReportDetail> list) {
        if (jdbc == null) {
            com.baomidou.mybatisplus.extension.toolkit.Db.saveBatch(list, 500);
            return;
        }
        String sql = "insert into bp_gov_report_detail (id, tenant_id, task_id, biz_type, "
                + "biz_id, external_id, sync_status, error_code, error_msg, request_data, "
                + "response_data, create_time) values (?,?,?,?,?,?,?,?,?,?,?,?)";
        jdbc.batchUpdate(sql, new org.springframework.jdbc.core.BatchPreparedStatementSetter() {
            @Override
            public void setValues(java.sql.PreparedStatement ps, int i)
                    throws java.sql.SQLException {
                GovReportDetail d = list.get(i);
                ps.setLong(1, d.getId());
                ps.setString(2, d.getTenantId());
                ps.setLong(3, d.getTaskId());
                ps.setString(4, d.getBizType());
                ps.setLong(5, d.getBizId() == null ? 0L : d.getBizId());
                ps.setString(6, d.getExternalId());
                ps.setString(7, d.getSyncStatus());
                ps.setString(8, d.getErrorCode());
                ps.setString(9, d.getErrorMsg());
                ps.setString(10, d.getRequestData());
                ps.setObject(11, null);
                ps.setObject(12, java.sql.Timestamp.valueOf(
                        d.getCreateTime() == null
                                ? java.time.LocalDateTime.now() : d.getCreateTime()));
            }

            @Override
            public int getBatchSize() {
                return list.size();
            }
        });
    }

    private void writeAdapterLog('''

s = s.replace('    private void writeAdapterLog(', helper, 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('JDBC batch inserted')
