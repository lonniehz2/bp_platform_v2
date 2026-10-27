package com.yundao.bp.iot.gateway;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.security.RequirePerm;
import java.time.LocalDate;
import java.util.Map;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** IoT 日对账（指令 / 回调 / 表计）。 */
@RestController
@RequestMapping("/api/v1/iot")
public class IotReconcileController {

    private final IotReconcileService service;

    public IotReconcileController(IotReconcileService service) {
        this.service = service;
    }

    @RequirePerm("asset:device:view")
    @GetMapping("/reconcile")
    public R<Map<String, Object>> daily(
            @RequestParam(required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {
        return R.ok(service.daily(date));
    }
}
