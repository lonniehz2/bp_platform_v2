package com.yundao.bp.iot.gateway;

import com.yundao.bp.common.api.R;
import com.yundao.bp.dev.iot.status.DeviceStatusSyncService;
import com.yundao.bp.iam.security.RequirePerm;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 批量设备状态同步（IoT → 平台）。 */
@RestController
@RequestMapping("/api/v1/iot")
public class IotDeviceStatusController {

    private final DeviceStatusSyncService service;

    public IotDeviceStatusController(DeviceStatusSyncService service) {
        this.service = service;
    }

    /**
     * 拉取一批设备的在线/电量状态并回写。
     *
     * @param lockIds 逗号分隔设备编号；为空则取前 limit 台
     * @param limit   未指定 lockIds 时取多少台（默认 100，最大 500）
     */
    @RequirePerm("asset:device:update")
    @PostMapping("/devices/status-sync")
    public R<Map<String, Object>> sync(@RequestParam(required = false) String lockIds,
                                       @RequestParam(defaultValue = "100") int limit) {
        List<String> ids = new ArrayList<>();
        if (lockIds != null && !lockIds.isBlank()) {
            for (String x : lockIds.split(",")) {
                if (!x.isBlank()) {
                    ids.add(x.trim());
                }
            }
        }
        return R.ok(service.sync(ids, limit));
    }
}
