package com.yundao.bp.iot.gateway;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.Map;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** IoT 同步操作：设备台账同步、表计补拉（供页面按钮与联调触发）。 */
@RestController
@RequestMapping("/api/v1/iot")
public class IotSyncController {

    private final IotSyncService syncService;

    public IotSyncController(IotSyncService syncService) {
        this.syncService = syncService;
    }

    @RequirePerm("asset:device:update")
    @PostMapping("/devices/sync")
    public R<Map<String, Object>> syncDevices(
            @RequestParam(required = false) Integer days) {
        int d = days == null || days <= 0 ? 1 : days;
        return R.ok(syncService.syncDevices(LocalDateTime.now().minusDays(d)));
    }

    @RequirePerm("fin:bill:create")
    @PostMapping("/meter/pull")
    public R<Map<String, Object>> pullMeters(
            @RequestParam(required = false) String date) {
        LocalDate day = date == null || date.isBlank() ? null : LocalDate.parse(date);
        return R.ok(syncService.pullMeters(day));
    }
}
