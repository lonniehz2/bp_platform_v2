package com.yundao.bp.iam.controller;

import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.dto.BrandingCmd;
import com.yundao.bp.iam.dto.BrandingVO;
import com.yundao.bp.iam.security.RequirePerm;
import com.yundao.bp.iam.service.TenantBrandingService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/** 平台品牌与主题配置。 */
@RestController
@RequestMapping("/api/v1/platform/branding")
public class PlatformBrandingController {

    private final TenantBrandingService service;

    public PlatformBrandingController(TenantBrandingService service) {
        this.service = service;
    }

    @GetMapping
    @RequirePerm("platform:branding:view")
    public R<BrandingVO> get() {
        return R.ok(service.get());
    }

    @PutMapping
    @RequirePerm("platform:branding:manage")
    public R<BrandingVO> save(@Valid @RequestBody BrandingCmd cmd) {
        return R.ok(service.save(cmd));
    }
}
