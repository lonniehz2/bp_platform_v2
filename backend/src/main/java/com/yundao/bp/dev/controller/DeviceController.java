package com.yundao.bp.dev.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 设备查询接口。
 *
 * <p><b>补齐说明</b>：此前只有「门锁绑定解析」，没有设备列表接口，
 * 导致前端「设备管理」页无处可查。本控制器只做<b>查询</b>，
 * 设备注册/绑定仍由 IoT 侧与绑定流程负责。
 */
@RestController
@RequestMapping("/api/v1/devices")
public class DeviceController {

    private final DevDeviceMapper mapper;

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
    }

    /**
     * 分页查询设备。
     *
     * <p>过滤维度按 `bp_dev_device` 实际字段：spaceId / deviceId / deviceMac /
     * onlineStatus。该表<b>没有</b> houseId / lockId 列——门锁与房源的关系
     * 由绑定记录与空间层级推导，不在设备表冗余。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping
    public R<PageResult<DevDevice>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long spaceId,
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String deviceMac,
            @RequestParam(required = false) Integer onlineStatus,
            @RequestParam(required = false) String deviceType,
            @RequestParam(required = false) String keyword) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .eq(spaceId != null, DevDevice::getSpaceId, spaceId)
                .eq(deviceType != null && !deviceType.isBlank(),
                        DevDevice::getDeviceType, deviceType)
                .eq(deviceId != null && !deviceId.isBlank(),
                        DevDevice::getDeviceId, deviceId)
                .like(deviceMac != null && !deviceMac.isBlank(),
                        DevDevice::getDeviceMac, deviceMac)
                .eq(onlineStatus != null, DevDevice::getOnlineStatus, onlineStatus)
                .and(keyword != null && !keyword.isBlank(),
                        w -> w.like(DevDevice::getDeviceId, keyword)
                                .or().like(DevDevice::getDeviceMac, keyword)
                                .or().like(DevDevice::getDeviceName, keyword))
                .orderByDesc(DevDevice::getId);
        IPage<DevDevice> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return R.ok(PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords()));
    }


    /** 设备分类清单（具体分类 + 大类 + 数量）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/types")
    public R<java.util.List<java.util.Map<String, Object>>> types() {
        java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
        for (com.yundao.bp.dev.constant.DevDeviceType t
                : com.yundao.bp.dev.constant.DevDeviceType.values()) {
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("code", t.name());
            m.put("label", t.label());
            m.put("category", t.category());
            m.put("count", mapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                    .eq(DevDevice::getDeviceType, t.name())));
            out.add(m);
        }
        return R.ok(out);
    }

    /** 未绑定任何空间的设备（供绑定弹窗选择）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/unbound")
    public R<java.util.List<DevDevice>> unbound(
            @RequestParam(required = false) String deviceType) {
        return R.ok(mapper.selectList(new LambdaQueryWrapper<DevDevice>()
                .isNull(DevDevice::getSpaceId)
                .eq(deviceType != null && !deviceType.isBlank(),
                        DevDevice::getDeviceType, deviceType)
                .orderByDesc(DevDevice::getId)));
    }

    /** 设备绑定/解绑空间：spaceId 传空表示解绑。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @org.springframework.web.bind.annotation.PostMapping("/{id:\\d+}/bind")
    public R<DevDevice> bind(@PathVariable Long id,
                             @RequestBody java.util.Map<String, Object> body) {
        DevDevice d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("设备");
        }
        Object raw = body == null ? null : body.get("spaceId");
        if (raw == null || String.valueOf(raw).isBlank()
                || "null".equals(String.valueOf(raw))) {
            d.setSpaceId(null);
        } else {
            Long spaceId = Long.valueOf(String.valueOf(raw));
            if (spaceMapper.selectById(spaceId) == null) {
                throw BizException.notFound("空间");
            }
            d.setSpaceId(spaceId);
        }
        d.setUpdateTime(java.time.LocalDateTime.now());
        mapper.updateById(d);
        return R.ok(d);
    }

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

    /** 设备详情。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/{id:\\d+}")
    public R<DevDevice> get(@PathVariable Long id) {
        DevDevice d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("设备");
        }
        return R.ok(d);
    }


    /**
     * 数据新鲜度检查：按上报间隔契约判定设备是否失联。
     *
     * <p>门锁要求 ≥1 天 1 次、水电表 ≥1 天 2 次；传入 hours 可自定义阈值。
     * 用于上线后巡检「数据静默失效」。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/freshness")
    public R<java.util.Map<String, Object>> freshness(
            @RequestParam(defaultValue = "24") int hours) {
        java.time.LocalDateTime deadline = java.time.LocalDateTime.now()
                .minusHours(Math.max(1, hours));
        java.util.List<DevDevice> all = mapper.selectList(new LambdaQueryWrapper<>());
        java.util.List<java.util.Map<String, Object>> stale = new java.util.ArrayList<>();
        int fresh = 0;
        for (DevDevice d : all) {
            java.time.LocalDateTime last = d.getLastReportTime() != null
                    ? d.getLastReportTime()
                    : (d.getUpdateTime() != null ? d.getUpdateTime() : d.getCreateTime());
            boolean ok = last != null && last.isAfter(deadline);
            if (ok) {
                fresh++;
                continue;
            }
            java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
            m.put("deviceId", d.getDeviceId());
            m.put("deviceName", d.getDeviceName());
            m.put("deviceType", d.getDeviceType());
            m.put("spaceId", d.getSpaceId() == null ? null : String.valueOf(d.getSpaceId()));
            m.put("lastReportTime", last == null ? null : last.toString());
            m.put("hoursSilent", last == null ? null
                    : java.time.Duration.between(last, java.time.LocalDateTime.now()).toHours());
            m.put("battery", d.getBattery());
            stale.add(m);
        }
        stale.sort((a, b) -> Long.compare(
                ((Number) (b.get("hoursSilent") == null ? 0 : b.get("hoursSilent"))).longValue(),
                ((Number) (a.get("hoursSilent") == null ? 0 : a.get("hoursSilent"))).longValue()));
        java.util.Map<String, Object> out = new java.util.LinkedHashMap<>();
        out.put("thresholdHours", hours);
        out.put("total", all.size());
        out.put("fresh", fresh);
        out.put("stale", stale.size());
        out.put("staleRate", all.isEmpty() ? 0.0
                : Math.round(stale.size() * 10000.0 / all.size()) / 100.0);
        out.put("staleDevices", stale.size() > 50 ? stale.subList(0, 50) : stale);
        return R.ok(out);
    }

    /** 在线/绑定状态统计（看板用）。 */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/stats")
    public R<java.util.Map<String, Object>> stats() {
        long total = orZero(mapper.selectCount(new LambdaQueryWrapper<>()));
        long online = orZero(mapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getOnlineStatus, 1)));
        java.util.Map<String, Object> m = new java.util.LinkedHashMap<>();
        m.put("total", total);
        m.put("online", online);
        m.put("offline", total - online);
        m.put("onlineRate", total == 0 ? 0.0
                : Math.round(online * 10000.0 / total) / 100.0);
        return R.ok(m);
    }

    private static long orZero(Long v) {
        return v == null ? 0 : v;
    }
}
