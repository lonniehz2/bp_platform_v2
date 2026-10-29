package com.yundao.bp.iam.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.dto.PlatformInfoUpdateCmd;
import com.yundao.bp.iam.dto.PlatformInfoVO;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.iam.service.PlatformInfoService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 平台信息（当前平台）：编码只读，名称/类型/区域/状态可维护。 */
@RestController
@RequestMapping("/api/v1/platform")
public class PlatformController {

    private final PlatformInfoService service;

    public PlatformController(PlatformInfoService service) {
        this.service = service;
    }

    @RequirePerm("platform:info:view")
    @GetMapping("/info")
    public R<PlatformInfoVO> info() {
        return R.ok(service.get());
    }

    @RequirePerm("platform:info:manage")
    @PutMapping("/info")
    public R<PlatformInfoVO> update(@Valid @RequestBody PlatformInfoUpdateCmd cmd) {
        return R.ok(service.update(cmd));
    }
}
