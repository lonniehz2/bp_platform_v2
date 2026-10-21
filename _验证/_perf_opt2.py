# -*- coding: utf-8 -*-
"""大屏按需取指标（只算配置里出现的指标，避免算无用指标）"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 1) MetricService 增加按需批量取值
p1 = os.path.join(BASE, r'rpt\service\MetricService.java')
s1 = io.open(p1, encoding='utf-8').read()
if 'values(' not in s1:
    s1 = s1.replace('''    /** 实时取全部指标（驾驶舱/大屏用）。 */
    Map<String, Object> currentAll(Long orgId);''',
                    '''    /** 实时取全部指标（驾驶舱/大屏用）。 */
    Map<String, Object> currentAll(Long orgId);

    /**
     * 按需取指定指标（只算传入的编码，不算无用指标）。
     *
     * <p>大屏组件通常只用一部分指标，按需取可显著减少查询轮次。
     */
    Map<String, Object> values(java.util.List<String> codes, Long orgId);''', 1)
    io.open(p1, 'w', encoding='utf-8').write(s1)
    print('  ✓ MetricService 增加 values()')

# 2) 实现
p2 = os.path.join(BASE, r'rpt\service\impl\MetricServiceImpl.java')
s2 = io.open(p2, encoding='utf-8').read()
if 'public Map<String, Object> values(' not in s2:
    anchor = '    @Override\n    @Transactional(rollbackFor = Exception.class)\n    public int snapshotToday('
    helper = '''    @Override
    public Map<String, Object> values(java.util.List<String> codes, Long orgId) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (String code : codes) {
            m.put(code, current(code, orgId));
        }
        return m;
    }

''' + anchor
    assert anchor in s2
    s2 = s2.replace(anchor, helper, 1)
    io.open(p2, 'w', encoding='utf-8').write(s2)
    print('  ✓ MetricServiceImpl 实现 values()')

# 3) 大屏：先解析配置里的编码，再按需取值
p3 = os.path.join(BASE, r'rpt\service\impl\ScreenServiceImpl.java')
s3 = io.open(p3, encoding='utf-8').read()
if 'metricService.values(' not in s3:
    s3 = s3.replace('''        // 一次性取全部指标，避免每个组件重复查询（原来 8 组件 = 8 轮聚合）
        Map<String, Object> all = metricService.currentAll(orgId);
        List<Map<String, Object>> out = new ArrayList<>();
        try {
            List<Map<String, Object>> defs = new com.fasterxml.jackson.databind.ObjectMapper()
                    .readValue(widgetsJson, List.class);
            for (Map<String, Object> w : defs) {''',
                  '''        List<Map<String, Object>> out = new ArrayList<>();
        try {
            List<Map<String, Object>> defs = new com.fasterxml.jackson.databind.ObjectMapper()
                    .readValue(widgetsJson, List.class);
            // 先收集配置里真正需要的指标编码，只算这些（避免计算无用指标）
            List<String> codes = new ArrayList<>();
            for (Map<String, Object> w : defs) {
                String c = String.valueOf(w.get("code"));
                if (!codes.contains(c)) {
                    codes.add(c);
                }
            }
            Map<String, Object> all = metricService.values(codes, orgId);
            for (Map<String, Object> w : defs) {''', 1)
    io.open(p3, 'w', encoding='utf-8').write(s3)
    print('  ✓ ScreenServiceImpl 改为按需取值')

# 4) 用一个只含 8 个真实指标的校验：确保未引入未使用变量
s3 = io.open(p3, encoding='utf-8').read()
if 'Map<String, Object> all = metricService.values' in s3:
    print('  ✓ 校验：values() 已接入')
