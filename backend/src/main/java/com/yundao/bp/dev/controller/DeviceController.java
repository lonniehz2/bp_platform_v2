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

    public DeviceController(DevDeviceMapper mapper) {
        this.mapper = mapper;
    }

    /**
     * 分页查询设备。
     *
     * <p>过滤维度按 `bp_dev_device` 实际字段：spaceId / deviceId / deviceMac /
     * onlineStatus。该表<b>没有</b> houseId / lockId 列——门锁与房源的关系
     * 由绑定记录与空间层级推导，不在设备表冗余。
     */
    @GetMapping
    public R<PageResult<DevDevice>> page(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            @RequestParam(required = false) Long spaceId,
            @RequestParam(required = false) String deviceId,
            @RequestParam(required = false) String deviceMac,
            @RequestParam(required = false) Integer onlineStatus) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .eq(spaceId != null, DevDevice::getSpaceId, spaceId)
                .eq(deviceId != null && !deviceId.isBlank(),
                        DevDevice::getDeviceId, deviceId)
                .like(deviceMac != null && !deviceMac.isBlank(),
                        DevDevice::getDeviceMac, deviceMac)
                .eq(onlineStatus != null, DevDevice::getOnlineStatus, onlineStatus)
                .orderByDesc(DevDevice::getId);
        IPage<DevDevice> page = mapper.selectPage(new Page<>(pageNum, pageSize), qw);
        return R.ok(PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords()));
    }

    /** 设备详情。 */
    @GetMapping("/{id}")
    public R<DevDevice> get(@PathVariable Long id) {
        DevDevice d = mapper.selectById(id);
        if (d == null) {
            throw BizException.notFound("设备");
        }
        return R.ok(d);
    }

    /** 在线/绑定状态统计（看板用）。 */
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
