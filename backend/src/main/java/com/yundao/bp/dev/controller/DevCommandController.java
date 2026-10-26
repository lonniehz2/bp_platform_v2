package com.yundao.bp.dev.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.dev.entity.DevCommand;
import com.yundao.bp.dev.service.DevCommandService;
import com.yundao.bp.iam.security.RequirePerm;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 设备指令：远程开锁 / 重启 / 校时 / 拉合闸（经 IoT 平台下发）。 */
@RestController
@RequestMapping("/api/v1/dev-commands")
public class DevCommandController {

    private final DevCommandService service;

    public DevCommandController(DevCommandService service) {
        this.service = service;
    }

    @RequirePerm("dev:command:create")
    @PostMapping
    public R<DevCommand> create(@RequestBody CommandCmd cmd) {
        return R.ok(service.create(cmd.commandType(), cmd.deviceId(), cmd.lockId(),
                cmd.meterNo(), cmd.reason(), cmd.paramsJson(), cmd.source()));
    }

    @RequirePerm("dev:command:view")
    @GetMapping
    public R<PageResult<DevCommand>> page(@RequestParam(defaultValue = "1") long pageNum,
                                          @RequestParam(defaultValue = "20") long pageSize,
                                          @RequestParam(required = false) String status,
                                          @RequestParam(required = false) String commandType,
                                          @RequestParam(required = false) String deviceId) {
        return R.ok(service.page(pageNum, pageSize, status, commandType, deviceId));
    }

    @RequirePerm("dev:command:view")
    @GetMapping("/{id}")
    public R<DevCommand> get(@PathVariable Long id) {
        return R.ok(service.get(id));
    }

    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/retry")
    public R<DevCommand> retry(@PathVariable Long id) {
        return R.ok(service.retry(id));
    }

    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/approve")
    public R<DevCommand> approve(@PathVariable Long id,
                                 @RequestParam(defaultValue = "true") boolean approve) {
        return R.ok(service.approve(id, approve));
    }

    @RequirePerm("dev:command:retry")
    @PostMapping("/{id}/cancel")
    public R<DevCommand> cancel(@PathVariable Long id) {
        return R.ok(service.cancel(id));
    }

    public record CommandCmd(String commandType, String deviceId, String lockId,
                             String meterNo, String reason, String paramsJson, String source) {
    }
}
