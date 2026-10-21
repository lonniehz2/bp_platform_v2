# -*- coding: utf-8 -*-
"""用 JdbcTemplate 做通用业务编号解析，补齐剩余 ID 名称"""
import io
import os

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\web\DisplayEnricher.java')
s = io.open(P, encoding='utf-8').read()

# 1) 注入 JdbcTemplate
s = s.replace('import org.springframework.stereotype.Component;',
              'import org.springframework.jdbc.core.JdbcTemplate;\n'
              'import org.springframework.stereotype.Component;', 1)
s = s.replace('    private final ObjectMapper objectMapper;',
              '    private final ObjectMapper objectMapper;\n'
              '    /** 业务编号解析用：直接按 id 查业务单号，避免为 8 张表各注入一个 Mapper */\n'
              '    private final JdbcTemplate jdbcTemplate;\n'
              '    private final Map<Long, String> bizNoCache = new ConcurrentHashMap<>();', 1)

s = s.replace('''    public DisplayEnricher(PersonMapper personMapper, AssetHouseMapper houseMapper,
                           IamOrgMapper orgMapper, AssetSpaceMapper spaceMapper,
                           ObjectMapper objectMapper) {''',
              '''    public DisplayEnricher(PersonMapper personMapper, AssetHouseMapper houseMapper,
                           IamOrgMapper orgMapper, AssetSpaceMapper spaceMapper,
                           ObjectMapper objectMapper, JdbcTemplate jdbcTemplate) {''', 1)
s = s.replace('        this.objectMapper = objectMapper;\n    }',
              '        this.objectMapper = objectMapper;\n'
              '        this.jdbcTemplate = jdbcTemplate;\n    }', 1)

# 2) nameOf 扩展
s = s.replace('''            case "spaceId" -> spaceName(id);
            default -> null;''',
              '''            case "spaceId" -> spaceName(id);
            case "contractId", "oldContractId", "newContractId", "parentContractId" ->
                    bizNo("bp_biz_contract", "contract_no", "contractId", id);
            case "applicationId" -> bizNo("bp_biz_application", "application_no", "applicationId", id);
            case "batchId" -> bizNo("bp_biz_batch", "batch_no", "batchId", id);
            case "billId" -> bizNo("bp_fin_bill", "bill_no", "billId", id);
            case "terminationId" -> bizNo("bp_biz_termination", "termination_no", "terminationId", id);
            case "reviewId" -> bizNo("bp_biz_annual_review", "review_no", "reviewId", id);
            case "allocationId" -> bizNo("bp_biz_allocation", "allocation_no", "allocationId", id);
            case "userId", "decideUserId", "handleUserId", "operatorId",
                 "assignUserId" -> bizNo("bp_iam_user", "username", "userId", id);
            default -> null;''', 1)

# 3) bizNo 实现
s = s.replace('    private static String nullToEmpty(String s) {',
              '''    /**
     * 通用业务编号解析。只用于展示（补 xxxName），命中失败返回空串。
     * SQL 用固定白名单表名/列名，不接受外部输入，无注入风险。
     */
    private String bizNo(String table, String column, String key, long id) {
        String cacheKey = key + ":" + id;
        return bizNoCache.computeIfAbsent(cacheKey.hashCode() * 31L + id, k -> {
            trim();
            try {
                java.util.List<String> rows = jdbcTemplate.queryForList(
                        "SELECT " + column + " FROM " + table + " WHERE id = ? LIMIT 1",
                        String.class, id);
                return rows.isEmpty() || rows.get(0) == null ? "" : rows.get(0);
            } catch (RuntimeException ex) {
                // 表不存在或数据异常时不影响主流程
                return "";
            }
        });
    }

    private static String nullToEmpty(String s) {''', 1)

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ DisplayEnricher 接入 JdbcTemplate（合同/申请/批次/账单/退租/年审/配租/用户）')
