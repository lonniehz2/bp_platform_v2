# -*- coding: utf-8 -*-
"""性能优化第二批：
1) 门禁今日统计合并为一次查询（原来查两次全表）
2) 指标接口加 30 秒内存缓存（大屏/驾驶舱轮询频繁）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

# ---------- 1) Mapper 加合并统计 ----------
M = os.path.join(J, 'dev', 'mapper', 'DevAccessRecordMapper.java')
s = io.open(M, encoding='utf-8').read()
if 'countTodayPair' not in s:
    method = '''
    /**
     * 今日通行统计（一次查询返回总数与异常数，避免两次全表扫描）。
     *
     * @return 第 0 位为总数，第 1 位为异常数
     */
    @org.apache.ibatis.annotations.Select("""
            <script>
            select count(*) as total,
                   sum(case when is_abnormal = 1 then 1 else 0 end) as abnormal
            from bp_dev_access_record
            where tenant_id = #{tenantId}
              and open_time &gt;= #{startOfDay}
              <if test="orgId != null"> and org_id = #{orgId} </if>
            </script>
            """)
    java.util.Map<String, Object> countTodayPair(
            @org.apache.ibatis.annotations.Param("tenantId") String tenantId,
            @org.apache.ibatis.annotations.Param("orgId") Long orgId,
            @org.apache.ibatis.annotations.Param("startOfDay") java.time.LocalDateTime startOfDay);
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + method + s[i:]
    io.open(M, 'w', encoding='utf-8', newline='').write(s)
    print('DevAccessRecordMapper：已加 countTodayPair')

# ---------- 2) MetricServiceImpl：合并查询 + 缓存 ----------
P = os.path.join(J, 'rpt', 'service', 'impl', 'MetricServiceImpl.java')
s = io.open(P, encoding='utf-8').read()

# 替换两个 access 分支为合并查询
old_acc = '''            case "ACCESS_TODAY_COUNT" -> count(accessMapper.selectCount(
                    new LambdaQueryWrapper<DevAccessRecord>()
                            .eq(orgId != null, DevAccessRecord::getOrgId, orgId)
                            .ge(DevAccessRecord::getOpenTime, LocalDate.now().atStartOfDay())));
            case "ACCESS_ABNORMAL_COUNT" -> count(accessMapper.selectCount(
                    new LambdaQueryWrapper<DevAccessRecord>()
                            .eq(orgId != null, DevAccessRecord::getOrgId, orgId)
                            .eq(DevAccessRecord::getIsAbnormal, 1)
                            .ge(DevAccessRecord::getOpenTime, LocalDate.now().atStartOfDay())));'''
new_acc = '''            case "ACCESS_TODAY_COUNT" -> accessTodayPair(orgId)[0];
            case "ACCESS_ABNORMAL_COUNT" -> accessTodayPair(orgId)[1];'''
if old_acc in s:
    s = s.replace(old_acc, new_acc, 1)
    print('   门禁统计已合并')

# 追加 helper + 缓存字段
if 'accessTodayPair' in s and 'private double[] accessTodayPair' not in s:
    helper = '''
    /** 今日门禁统计缓存（60 秒），避免大屏轮询反复全表统计 */
    private static final long ACCESS_CACHE_MS = 60_000L;
    private volatile double[] accessCache = new double[] {0, 0};
    private volatile long accessCacheAt = 0L;
    private volatile Long accessCacheOrg;

    /** 今日通行（总数, 异常数），带 60 秒缓存与单次查询。 */
    private double[] accessTodayPair(Long orgId) {
        long now = System.currentTimeMillis();
        if (accessCacheOrg != null && java.util.Objects.equals(accessCacheOrg, orgId)
                && now - accessCacheAt < ACCESS_CACHE_MS) {
            return accessCache;
        }
        java.util.Map<String, Object> row = accessMapper.countTodayPair(
                TenantContext.tenantId(), orgId, LocalDate.now().atStartOfDay());
        double total = 0;
        double abnormal = 0;
        if (row != null) {
            Object t = row.get("total");
            Object a = row.get("abnormal");
            total = t == null ? 0 : ((Number) t).doubleValue();
            abnormal = a == null ? 0 : ((Number) a).doubleValue();
        }
        accessCache = new double[] {total, abnormal};
        accessCacheAt = now;
        accessCacheOrg = orgId;
        return accessCache;
    }
'''
    i = s.rstrip().rfind('}')
    s = s[:i] + helper + s[i:]

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('MetricServiceImpl：已加合并查询与缓存')
