package com.yundao.bp.dev.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.R;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.dev.entity.DevDevice;
import com.yundao.bp.dev.mapper.DevDeviceMapper;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * 与 IoT 平台的设备安装对接：待安装设备查询、安装结果回调。
 *
 * <p>安装单由 IoT 平台维护；本系统只落 MAC、安装状态和硬件历史。
 */
@RestController
@RequestMapping("/api/v1/iot")
public class DeviceInstallController {

    private final DevDeviceMapper deviceMapper;
    private final JdbcTemplate jdbc;
    private final SnowflakeIdGenerator idGen;

    public DeviceInstallController(DevDeviceMapper deviceMapper, JdbcTemplate jdbc,
                                   SnowflakeIdGenerator idGen) {
        this.deviceMapper = deviceMapper;
        this.jdbc = jdbc;
        this.idGen = idGen;
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/devices/pending-install")
    public R<List<Map<String, Object>>> pending(@RequestParam(required = false) Long orgId) {
        LambdaQueryWrapper<DevDevice> qw = new LambdaQueryWrapper<DevDevice>()
                .in(DevDevice::getInstallStatus, List.of("PENDING_INSTALL", "VIRTUAL"))
                .eq(orgId != null, DevDevice::getOrgId, orgId)
                .orderByAsc(DevDevice::getId)
                .last("LIMIT 500");
        List<Map<String, Object>> out = new ArrayList<>();
        for (DevDevice d : deviceMapper.selectList(qw)) {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("deviceId", d.getDeviceId());
            m.put("deviceType", d.getDeviceType());
            m.put("deviceName", d.getDeviceName());
            m.put("deviceMac", d.getDeviceMac());
            m.put("spaceId", d.getSpaceId() == null ? null : String.valueOf(d.getSpaceId()));
            m.put("orgId", d.getOrgId() == null ? null : String.valueOf(d.getOrgId()));
            m.put("installStatus", d.getInstallStatus());
            out.add(m);
        }
        return R.ok(out);
    }

    @com.yundao.bp.iam.security.RequirePerm("asset:device:view")
    @GetMapping("/devices/{deviceId}")
    public R<DevDevice> get(@PathVariable String deviceId) {
        DevDevice d = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getDeviceId, deviceId).last("LIMIT 1"));
        if (d == null) {
            throw BizException.notFound("设备");
        }
        return R.ok(d);
    }

    /**
     * IoT 安装完成回调。
     *
     * <p>NEW：写入首个 MAC；REPLACE：同一个 deviceId 更新 MAC，并记录硬件历史。
     */
    @com.yundao.bp.iam.security.RequirePerm("asset:device:update")
    @PostMapping("/install-orders/callback")
    public R<Map<String, Object>> callback(@RequestBody Map<String, Object> body) {
        String deviceId = str(body.get("deviceId"));
        String newMac = str(body.get("newMac"));
        String mode = str(body.get("installMode"));
        if (deviceId.isBlank() || newMac.isBlank()) {
            throw BizException.paramInvalid("deviceId 和 newMac 不能为空");
        }
        DevDevice d = deviceMapper.selectOne(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getDeviceId, deviceId).last("LIMIT 1"));
        if (d == null) {
            throw BizException.notFound("设备");
        }
        Long dup = deviceMapper.selectCount(new LambdaQueryWrapper<DevDevice>()
                .eq(DevDevice::getDeviceMac, newMac)
                .ne(DevDevice::getDeviceId, deviceId));
        if (dup != null && dup > 0) {
            throw BizException.stateConflict("物理MAC已被其他设备使用");
        }
        String oldMac = d.getDeviceMac();
        d.setDeviceMac(newMac);
        d.setIsVirtual(0);
        d.setInstallStatus("INSTALLED");
        d.setInstallTime(LocalDateTime.now());
        d.setMacUpdatedTime(LocalDateTime.now());
        d.setIotOrderNo(str(body.get("orderNo")));
        d.setUpdateTime(LocalDateTime.now());
        deviceMapper.updateById(d);
        jdbc.update("insert into bp_dev_device_hardware"
                        + "(id, tenant_id, device_id, old_mac, new_mac, change_type, iot_order_no,"
                        + " operator_id, operator_name, install_time, remark)"
                        + " values(?,?,?,?,?,?,?,?,?,?,?)",
                idGen.nextId(), d.getTenantId(), deviceId, oldMac, newMac,
                mode.isBlank() ? "NEW" : mode, str(body.get("orderNo")),
                str(body.get("operatorId")), str(body.get("operatorName")),
                LocalDateTime.now(), str(body.get("remark")));
        return R.ok(Map.of("deviceId", deviceId, "deviceMac", newMac, "status", "INSTALLED"));
    }

    private static String str(Object v) {
        return v == null ? "" : String.valueOf(v).trim();
    }
}
