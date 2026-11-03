package com.yundao.bp.fin.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.fin.dto.DevicePrepayConsumeCmd;
import com.yundao.bp.fin.dto.DevicePrepayInCmd;
import com.yundao.bp.fin.dto.DevicePrepayRefundCmd;
import com.yundao.bp.fin.service.DevicePrepayService;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 设备/表计水电预存。 */
@RestController
@RequestMapping("/api/v1/fin/device-prepay")
public class DevicePrepayController {

    private final DevicePrepayService service;

    public DevicePrepayController(DevicePrepayService service) {
        this.service = service;
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:view")
    @GetMapping("/{meterPointId}")
    public R<Map<String, Object>> account(@PathVariable Long meterPointId) {
        return R.ok(service.account(meterPointId));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:create")
    @PostMapping("/in")
    public R<Map<String, Object>> payIn(@RequestBody DevicePrepayInCmd cmd) {
        return R.ok(service.payIn(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:bill:create")
    @PostMapping("/consume")
    public R<Map<String, Object>> consume(@RequestBody DevicePrepayConsumeCmd cmd) {
        return R.ok(service.consume(cmd));
    }

    @com.yundao.bp.iam.security.RequirePerm("fin:payment:refund")
    @PostMapping("/refund")
    public R<Map<String, Object>> refund(@RequestBody DevicePrepayRefundCmd cmd) {
        return R.ok(service.refund(cmd));
    }
}
