# -*- coding: utf-8 -*-
"""能耗分析性能优化：把逐个 selectById 的房源/空间查询改为批量预取。

原本：对每个有能耗的房源（约 740 个）各查一次房源 + 每层空间一次，
      单次接口耗时 4.3s，驾驶舱首屏图表因此迟迟不出现。
优化：一次性批量取房源与其所有上级空间，再在内存里组装。
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'fin',
                 'service', 'impl', 'MeterReadingServiceImpl.java')
s = io.open(P, encoding='utf-8', errors='replace').read()

OLD = '''        java.util.Map<Long, com.yundao.bp.asset.entity.AssetHouse> houseCache =
                new java.util.HashMap<>();
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetSpace> spaceCache =
                new java.util.HashMap<>();
        int rank = 0;'''

NEW = '''        // 批量预取：房源 + 其上级空间（避免数百次 selectById）
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetHouse> houseCache =
                new java.util.HashMap<>();
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetSpace> spaceCache =
                new java.util.HashMap<>();
        if (!ranked.isEmpty()) {
            java.util.List<Long> houseIds = new java.util.ArrayList<>();
            for (java.util.Map.Entry<Long, java.math.BigDecimal> e : ranked) {
                houseIds.add(e.getKey());
            }
            for (com.yundao.bp.asset.entity.AssetHouse h
                    : anaHouseMapper.selectBatchIds(houseIds)) {
                houseCache.put(h.getId(), h);
            }
            // 逐级收集空间 id（最多 6 层）
            java.util.Set<Long> spaceIds = new java.util.HashSet<>();
            for (com.yundao.bp.asset.entity.AssetHouse h : houseCache.values()) {
                if (h.getSpaceId() != null) {
                    spaceIds.add(h.getSpaceId());
                }
            }
            for (int depth = 0; depth < 5 && !spaceIds.isEmpty(); depth++) {
                java.util.List<Long> batch = new java.util.ArrayList<>();
                for (Long sid : spaceIds) {
                    if (!spaceCache.containsKey(sid)) {
                        batch.add(sid);
                    }
                }
                if (batch.isEmpty()) {
                    break;
                }
                java.util.Set<Long> next = new java.util.HashSet<>();
                for (com.yundao.bp.asset.entity.AssetSpace sp
                        : anaSpaceMapper.selectBatchIds(batch)) {
                    spaceCache.put(sp.getId(), sp);
                    if (sp.getParentId() != null) {
                        next.add(sp.getParentId());
                    }
                }
                spaceIds = next;
            }
        }
        int rank = 0;'''

if 'selectBatchIds(houseIds)' in s:
    print('已存在批量预取')
    raise SystemExit(0)

if OLD not in s:
    print('锚点不匹配，未修改')
    raise SystemExit(1)

s = s.replace(OLD, NEW, 1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已改为批量预取房源与空间')
