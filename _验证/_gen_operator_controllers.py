# -*- coding: utf-8 -*-
import io
import os

BASE = r'..\backend\src\main\java\com\yundao\bp\iam'

ctrl = '''package com.yundao.bp.iam.controller;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.dto.*;
import com.yundao.bp.iam.entity.PlatformOperator;
import com.yundao.bp.iam.service.PlatformManageService;
import com.yundao.bp.iam.service.PlatformOperatorService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.*;

/** 平台运营台（独立入口，使用 X-Operator-Token 鉴权）。 */
@RestController
@RequestMapping("/api/v1/platform-admin")
public class PlatformAdminController {

    private final PlatformOperatorService operatorService;
    private final PlatformManageService manageService;

    public PlatformAdminController(PlatformOperatorService operatorService,
                                   PlatformManageService manageService) {
        this.operatorService = operatorService;
        this.manageService = manageService;
    }

    @PostMapping("/auth/login")
    public R<OperatorLoginVO> login(@Valid @RequestBody OperatorLoginCmd cmd,
                                    HttpServletRequest req) {
        return R.ok(operatorService.login(cmd, ip(req)));
    }

    @PostMapping("/auth/change-password")
    public R<Void> changePassword(@Valid @RequestBody OperatorChangePwdCmd cmd,
                                  HttpServletRequest req) {
        operatorService.changePassword(token(req), cmd.oldPassword(), cmd.newPassword());
        return R.ok(null);
    }

    @PostMapping("/auth/logout")
    public R<Void> logout(HttpServletRequest req) {
        operatorService.logout(token(req));
        return R.ok(null);
    }

    @GetMapping("/platforms")
    public R<List<PlatformVO>> platforms(@RequestParam(required = false) String keyword,
                                         @RequestParam(required = false) String status,
                                         HttpServletRequest req) {
        require(req);
        return R.ok(manageService.list(keyword, status));
    }

    @PostMapping("/platforms")
    public R<PlatformCreateResult> createPlatform(@Valid @RequestBody PlatformCreateCmd cmd,
                                                  HttpServletRequest req) {
        return R.ok(manageService.create(cmd, require(req), ip(req)));
    }

    @GetMapping("/platforms/{id}")
    public R<PlatformVO> platform(@PathVariable Long id, HttpServletRequest req) {
        require(req);
        return R.ok(manageService.detail(id));
    }

    @PutMapping("/platforms/{id}")
    public R<PlatformVO> updatePlatform(@PathVariable Long id,
                                        @Valid @RequestBody PlatformUpdateCmd cmd,
                                        HttpServletRequest req) {
        return R.ok(manageService.update(id, cmd, require(req), ip(req)));
    }

    @PostMapping("/platforms/{id}/enable")
    public R<Void> enable(@PathVariable Long id, HttpServletRequest req) {
        manageService.setStatus(id, "ENABLED", require(req), ip(req));
        return R.ok(null);
    }

    @PostMapping("/platforms/{id}/disable")
    public R<Void> disable(@PathVariable Long id, HttpServletRequest req) {
        manageService.setStatus(id, "DISABLED", require(req), ip(req));
        return R.ok(null);
    }

    @PostMapping("/platforms/{id}/archive")
    public R<Void> archive(@PathVariable Long id, HttpServletRequest req) {
        manageService.archive(id, require(req), ip(req));
        return R.ok(null);
    }

    @PostMapping("/platforms/{id}/restore")
    public R<Void> restore(@PathVariable Long id, HttpServletRequest req) {
        manageService.restore(id, require(req), ip(req));
        return R.ok(null);
    }

    @GetMapping("/platforms/{id}/admins")
    public R<List<PlatformAdminVO>> admins(@PathVariable Long id, HttpServletRequest req) {
        require(req);
        return R.ok(manageService.admins(id));
    }

    @PostMapping("/platforms/{id}/admins")
    public R<PlatformAdminResetVO> createAdmin(@PathVariable Long id,
                                               @Valid @RequestBody PlatformAdminCreateCmd cmd,
                                               HttpServletRequest req) {
        return R.ok(manageService.createAdmin(id, cmd, require(req), ip(req)));
    }

    @PostMapping("/platforms/{id}/admins/{userId}/reset-password")
    public R<PlatformAdminResetVO> resetPassword(@PathVariable Long id,
                                                 @PathVariable Long userId,
                                                 HttpServletRequest req) {
        return R.ok(manageService.resetPassword(id, userId, require(req), ip(req)));
    }

    @PostMapping("/platforms/{id}/admins/{userId}/enable")
    public R<Void> enableAdmin(@PathVariable Long id, @PathVariable Long userId,
                               HttpServletRequest req) {
        manageService.setAdminStatus(id, userId, "ENABLED", require(req), ip(req));
        return R.ok(null);
    }

    @PostMapping("/platforms/{id}/admins/{userId}/disable")
    public R<Void> disableAdmin(@PathVariable Long id, @PathVariable Long userId,
                                HttpServletRequest req) {
        manageService.setAdminStatus(id, userId, "DISABLED", require(req), ip(req));
        return R.ok(null);
    }

    @PostMapping("/platforms/{id}/admins/{userId}/unlock")
    public R<Void> unlockAdmin(@PathVariable Long id, @PathVariable Long userId,
                               HttpServletRequest req) {
        manageService.unlockAdmin(id, userId, require(req), ip(req));
        return R.ok(null);
    }

    @GetMapping("/audits")
    public R<PageResult<PlatformAuditVO>> audits(
            @RequestParam(defaultValue = "1") long pageNum,
            @RequestParam(defaultValue = "20") long pageSize,
            HttpServletRequest req) {
        require(req);
        return R.ok(manageService.audits(pageNum, pageSize));
    }

    private PlatformOperator require(HttpServletRequest req) {
        return operatorService.require(token(req));
    }

    private static String token(HttpServletRequest req) {
        return req.getHeader("X-Operator-Token");
    }

    private static String ip(HttpServletRequest req) {
        String xf = req.getHeader("X-Forwarded-For");
        if (xf != null && !xf.isBlank()) {
            return xf.split(",")[0].trim();
        }
        return req.getRemoteAddr();
    }
}
'''

io.open(os.path.join(BASE, 'controller/PlatformAdminController.java'), 'w',
        encoding='utf-8', newline='').write(ctrl)

pub = '''package com.yundao.bp.iam.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.R;
import com.yundao.bp.iam.dto.BrandingVO;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.entity.TenantBranding;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.iam.mapper.TenantBrandingMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** 登录前品牌信息（无需登录，仅返回展示字段）。 */
@RestController
@RequestMapping("/api/v1/public")
public class PublicBrandingController {

    private final IamTenantMapper tenantMapper;
    private final TenantBrandingMapper brandingMapper;

    public PublicBrandingController(IamTenantMapper tenantMapper,
                                    TenantBrandingMapper brandingMapper) {
        this.tenantMapper = tenantMapper;
        this.brandingMapper = brandingMapper;
    }

    @GetMapping("/platform-branding")
    public R<BrandingVO> branding(@RequestParam String code) {
        IamTenant t = tenantMapper.selectOne(new LambdaQueryWrapper<IamTenant>()
                .eq(IamTenant::getTenantCode, code)
                .eq(IamTenant::getDeleted, 0)
                .last("LIMIT 1"));
        TenantBranding b = brandingMapper.selectById(code);
        String name = t == null ? null : t.getTenantName();
        return R.ok(new BrandingVO(code, name,
                b == null ? null : b.getLogoUrl(),
                b == null ? null : b.getPrimaryColor(),
                b == null ? null : b.getAccentColor(),
                b == null ? null : b.getLoginTitle(),
                b == null ? null : b.getLoginSubtitle(),
                b == null ? "rail" : b.getMenuStyle(),
                b == null ? "light" : b.getColorMode(),
                b == null || b.getAllowUserSwitch() == null || b.getAllowUserSwitch() == 1));
    }
}
'''
io.open(os.path.join(BASE, 'controller/PublicBrandingController.java'), 'w',
        encoding='utf-8', newline='').write(pub)
print('controllers written')
