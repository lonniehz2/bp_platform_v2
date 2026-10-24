# -*- coding: utf-8 -*-
"""空间设备继承授权：按房源 → 空间祖先链逐级收集设备。

GET /devices/inherited?houseId=
返回：
  chain   空间链（床位→房间→楼层→单元→楼栋）
  devices 可授权设备（带 spaceType、是否继承）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp', 'dev',
                 'controller', 'DeviceController.java')
s = io.open(P, encoding='utf-8').read()

if 'inherited' in s:
    print('已存在')
    raise SystemExit(0)

# 依赖注入
s = s.replace('''    private final DevDeviceMapper mapper;

    public DeviceController(DevDeviceMapper mapper) {
        this.mapper = mapper;
    }''',
'''    private final DevDeviceMapper mapper;

    /** 房源（继承链起点：房源→空间） */
    private final com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper;

    /** 空间（向上遍历祖先） */
    private final com.yundao.bp.asset.mapper.AssetSpaceMapper spaceMapper;

    public DeviceController(DevDeviceMapper mapper,
                            com.yundao.bp.asset.mapper.AssetHouseMapper houseMapper,
                            com.yundao.bp.asset.mapper.AssetSpaceMapper spaceMapper) {
        this.mapper = mapper;
        this.houseMapper = houseMapper;
        this.spaceMapper = spaceMapper;
    }''', 1)

# 新接口
block = '''
    /**
     * 空间设备继承：给定房源，沿空间祖先链收集可授权设备。
     *
     * <p><b>统一模型</b>：设备只绑定空间（{@code dev_device.space_id}），
     * 房源通过 {@code house.space_id} 定位；入住人可继承
     * 床位→房间→楼层→单元→楼栋 各级设备，无需"房源设备"概念。
     *
     * <p>返回示例：房间门锁（本房源）、单元门禁（继承）、小区大门（继承）。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/inherited")
    public R<java.util.Map<String, Object>> inherited(@RequestParam Long houseId) {
        com.yundao.bp.asset.entity.AssetHouse house = houseMapper.selectById(houseId);
        if (house == null) {
            throw BizException.notFound("房源");
        }
        java.util.List<com.yundao.bp.asset.entity.AssetSpace> chain = new java.util.ArrayList<>();
        Long sid = house.getSpaceId();
        int guard = 0;
        while (sid != null && guard++ < 8) {
            com.yundao.bp.asset.entity.AssetSpace sp = spaceMapper.selectById(sid);
            if (sp == null) {
                break;
            }
            chain.add(sp);
            sid = sp.getParentId();
        }
        java.util.List<Long> ids = chain.stream().map(com.yundao.bp.asset.entity.AssetSpace::getId)
                .toList();
        java.util.Map<Long, com.yundao.bp.asset.entity.AssetSpace> byId = new java.util.HashMap<>();
        for (com.yundao.bp.asset.entity.AssetSpace sp : chain) {
            byId.put(sp.getId(), sp);
        }
        java.util.List<com.yundao.bp.dev.entity.DevDevice> devices = ids.isEmpty()
                ? java.util.List.of()
                : mapper.selectList(new LambdaQueryWrapper<com.yundao.bp.dev.entity.DevDevice>()
                        .in(com.yundao.bp.dev.entity.DevDevice::getSpaceId, ids));

        java.util.List<java.util.Map<String, Object>> chainOut = new java.util.ArrayList<>();
        for (com.yundao.bp.asset.entity.AssetSpace sp : chain) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("spaceId", String.valueOf(sp.getId()));
            m.put("spaceCode", sp.getSpaceCode());
            m.put("spaceName", sp.getSpaceName());
            m.put("spaceType", sp.getSpaceType());
            chainOut.add(m);
        }
        java.util.List<java.util.Map<String, Object>> devOut = new java.util.ArrayList<>();
        for (com.yundao.bp.dev.entity.DevDevice d : devices) {
            com.yundao.bp.asset.entity.AssetSpace sp = byId.get(d.getSpaceId());
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("deviceId", d.getDeviceId());
            m.put("deviceName", d.getDeviceName());
            m.put("deviceType", d.getDeviceType());
            m.put("spaceId", d.getSpaceId() == null ? null : String.valueOf(d.getSpaceId()));
            m.put("spaceName", sp == null ? null : sp.getSpaceName());
            m.put("spaceType", sp == null ? null : sp.getSpaceType());
            m.put("scope", house.getSpaceId() != null
                    && house.getSpaceId().equals(d.getSpaceId()) ? "本房源" : "继承");
            m.put("onlineStatus", d.getOnlineStatus());
            devOut.add(m);
        }
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("houseId", String.valueOf(house.getId()));
        out.put("houseCode", house.getHouseCode());
        out.put("houseName", house.getHouseName());
        out.put("chain", chainOut);
        out.put("devices", devOut);
        out.put("total", devOut.size());
        return R.ok(out);
    }
'''
anchor = '    /** 设备详情。 */'
s = s.replace(anchor, block + '\n' + anchor, 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('DeviceController：/inherited 已加')
