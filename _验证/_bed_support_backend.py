# -*- coding: utf-8 -*-
"""宿舍床位支持（后端）：房源 VO 带出所属空间名称与类型。

宿舍场景下房源挂在 BED 节点，列表必须能看出「某个床位属于哪个房间」，
否则运营无法定位。实现在分页查询里批量补空间名称（避免 N+1）。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
J = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'asset')

# ---------- 1) HouseVO 增加 spaceName / spaceType ----------
V = os.path.join(J, 'dto', 'HouseVO.java')
s = io.open(V, encoding='utf-8').read()
if 'spaceName' not in s:
    s = s.replace('        Long spaceId,', '        Long spaceId,\n        String spaceName,\n        String spaceType,', 1)
    # from(...) 增加重载
    s = s.replace('public static HouseVO from(AssetHouse e, String statusLabel, Long vacantDays) {',
                  '''public static HouseVO from(AssetHouse e, String statusLabel, Long vacantDays) {
        return from(e, statusLabel, vacantDays, null, null);
    }

    /** 带所属空间信息的构造（宿舍/床位场景用于定位）。 */
    public static HouseVO from(AssetHouse e, String statusLabel, Long vacantDays,
                               String spaceName, String spaceType) {''', 1)
    # 原 from 主体里的 new HouseVO(...) 需要多传两个参数
    i = s.find('public static HouseVO from(AssetHouse e, String statusLabel, Long vacantDays,')
    j = s.find('}', s.find('new HouseVO(', i))
    body = s[i:j]
    if 'spaceName' not in body:
        s = s[:i] + body.replace('e.getSpaceId(),', 'e.getSpaceId(),\n                        spaceName, spaceType,') + s[j:]
    io.open(V, 'w', encoding='utf-8', newline='').write(s)
    print('HouseVO：已加 spaceName/spaceType')

# ---------- 2) HouseServiceImpl：批量补空间 ----------
I = os.path.join(J, 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(I, encoding='utf-8').read()
if 'fillSpaceInfo' not in s:
    inject = '''
    /** 空间节点查询（补房源的所属房间/床位名称） */
    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private com.yundao.bp.asset.mapper.AssetSpaceMapper spaceInfoMapper;

    /** 批量补空间名称与类型，避免逐条查询。 */
    private void fillSpaceInfo(java.util.List<HouseVO> rows) {
        if (rows == null || rows.isEmpty() || spaceInfoMapper == null) {
            return;
        }
        java.util.Set<Long> ids = new java.util.HashSet<>();
        for (HouseVO r : rows) {
            if (r.spaceId() != null) {
                ids.add(r.spaceId());
            }
        }
        if (ids.isEmpty()) {
            return;
        }
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetSpace> byId = new java.util.HashMap<>();
        for (com.yundao.bp.asset.entity.AssetSpace sp : spaceInfoMapper.selectBatchIds(ids)) {
            byId.put(sp.getId(), sp);
        }
        for (int i = 0; i < rows.size(); i++) {
            HouseVO r = rows.get(i);
            com.yundao.bp.asset.entity.AssetSpace sp = byId.get(r.spaceId());
            if (sp != null) {
                rows.set(i, HouseVO.from(spaceRowSource.get(r.id()), r.houseStatusLabel(),
                        r.vacantDays(), sp.getSpaceName(), sp.getSpaceType()));
            }
        }
    }
'''
    print('  需人工接入 fillSpaceInfo（依赖实体 getter）')
    io.open(I, 'w', encoding='utf-8', newline='').write(s)
print('后端改动完成（待编译校验）')
