package com.yundao.bp.iot.gateway;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.iot.config.IotSettings;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.core.env.Environment;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * IoT 对接能力与就绪度：给联调/上线切换一个“现在接的是什么、还缺什么”的视图。
 */
@RestController
@RequestMapping("/api/v1/iot")
public class IotCapabilitiesController {

    private final Environment env;
    private final IotSettings settings;

    public IotCapabilitiesController(Environment env, IotSettings settings) {
        this.env = env;
        this.settings = settings;
    }

    @RequirePerm("asset:device:view")
    @GetMapping("/capabilities")
    public R<Map<String, Object>> capabilities() {
        Map<String, Object> out = new LinkedHashMap<>();

        // 1) 客户端模式
        Map<String, Object> modes = new LinkedHashMap<>();
        modes.put("command", mode("bp.dev.command-mode"));
        modes.put("device", mode("bp.dev.device-mode"));
        modes.put("meter", mode("bp.dev.meter-mode"));
        modes.put("credential", mode("bp.credential.mode"));
        modes.put("token", mode("bp.iot.token-mode"));
        modes.put("status", mode("bp.iot.status-mode"));
        out.put("modes", modes);

        // 2) 平台凭证
        String appId = env.getProperty("ymd.iot.credential.app-id", "");
        String secret = env.getProperty("ymd.iot.credential.app-secret", "");
        Map<String, Object> cred = new LinkedHashMap<>();
        cred.put("baseUrl", env.getProperty("ymd.iot.base-url", ""));
        cred.put("appIdConfigured", appId != null && !appId.isBlank());
        cred.put("appSecretConfigured", secret != null && !secret.isBlank());
        out.put("iotCredential", cred);

        // 3) 回调配置
        Map<String, Object> cb = new LinkedHashMap<>();
        cb.put("verify", settings.getString("iot.callback.verify"));
        cb.put("appId", settings.getString("iot.callback.appId"));
        cb.put("timestampToleranceSeconds", settings.timestampToleranceSeconds());
        cb.put("nonceCacheMinutes", settings.nonceCacheMinutes());
        cb.put("defaultTenant", settings.getString("iot.callback.defaultTenant"));
        out.put("callback", cb);

        Map<String, Object> meter = new LinkedHashMap<>();
        meter.put("reportPeriod", settings.meterReportPeriod());
        meter.put("elecHourly", settings.meterPeriodHourly("ELEC"));
        meter.put("waterHourly", settings.meterPeriodHourly("WATER"));
        out.put("meter", meter);

        // 4) 平台已支持的能力
        out.put("commandTypes", List.of("LOCK_OPEN", "DEVICE_REBOOT", "DEVICE_SYNC_TIME",
                "METER_SWITCH", "LOCK_ALWAYS_OPEN", "LOCK_ALWAYS_CLOSE", "LOCK_MODE_NORMAL"));
        out.put("callbackActions", List.of("event", "access", "command/ack", "grant/ack",
                "heartbeat", "meter", "device-status", "alarm-ack"));

        // 5) 仍需 IoT 提供的能力（未完成项）
        List<Map<String, Object>> pending = new ArrayList<>();
        pending.add(item("IOT-TOKEN", "取 Token / 续期接口",
                "TC-M1-01/02；平台客户端已实现（bp.iot.token-mode=mock 可跑），待 IoT 提供端点"));
        pending.add(item("IOT-DEVICE-STATUS-BATCH", "批量设备状态查询",
                "TC-M1-05；平台客户端与同步接口已实现（/iot/devices/status-sync），待 IoT 端点"));
        pending.add(item("IOT-LOCK-MODE", "/ymd/restful/lock/mode（mode=OPEN/CLOSE/NORMAL）",
                "TC-M4-07；平台指令已支持，缺设备侧实现"));
        pending.add(item("IOT-METER-SPEC", "表计倍率/单位/上报周期字段口径",
                "TC-M6-04/07；影响用量与出账口径"));
        pending.add(item("IOT-LOAD-ENV", "压测与断网演练环境",
                "TC-M8-02/03；需要 IoT 侧配合造环境"));
        out.put("pendingFromIot", pending);

        out.put("readyForReal", isRealConfigured(appId, secret));
        return R.ok(out);
    }

    private String mode(String key) {
        String v = env.getProperty(key);
        return v == null || v.isBlank() ? "mock（默认）" : v;
    }

    private static boolean isRealConfigured(String appId, String secret) {
        return appId != null && !appId.isBlank() && secret != null && !secret.isBlank();
    }

    private static Map<String, Object> item(String code, String name, String note) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("code", code);
        m.put("name", name);
        m.put("note", note);
        return m;
    }
}
