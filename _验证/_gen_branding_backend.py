# -*- coding: utf-8 -*-
import io
import os

BASE = r'..\backend\src\main\java\com\yundao\bp\iam'

io.open(os.path.join(BASE, 'dto/BrandingCmd.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record BrandingCmd(
        @Size(max = 512) String logoUrl,
        @Pattern(regexp = "^$|^#[0-9a-fA-F]{6}$", message = "主题色应为 #RRGGBB") String primaryColor,
        @Pattern(regexp = "^$|^#[0-9a-fA-F]{6}$", message = "辅助色应为 #RRGGBB") String accentColor,
        @Size(max = 120) String loginTitle,
        @Size(max = 200) String loginSubtitle,
        @Pattern(regexp = "rail|classic", message = "菜单风格不合法") String menuStyle,
        @Pattern(regexp = "light|dark", message = "配色不合法") String colorMode,
        Boolean allowUserSwitch
) {
}
''')

io.open(os.path.join(BASE, 'service/TenantBrandingService.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.iam.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.iam.dto.BrandingCmd;
import com.yundao.bp.iam.dto.BrandingVO;
import com.yundao.bp.iam.entity.IamTenant;
import com.yundao.bp.iam.entity.TenantBranding;
import com.yundao.bp.iam.mapper.IamTenantMapper;
import com.yundao.bp.iam.mapper.TenantBrandingMapper;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/** 平台品牌与主题（平台侧维护）。 */
@Service
public class TenantBrandingService {

    private final TenantBrandingMapper brandingMapper;
    private final IamTenantMapper tenantMapper;

    public TenantBrandingService(TenantBrandingMapper brandingMapper,
                                 IamTenantMapper tenantMapper) {
        this.brandingMapper = brandingMapper;
        this.tenantMapper = tenantMapper;
    }

    public BrandingVO get() {
        String code = TenantContext.get().tenantId();
        IamTenant t = tenantMapper.selectOne(new LambdaQueryWrapper<IamTenant>()
                .eq(IamTenant::getTenantCode, code).last("LIMIT 1"));
        TenantBranding b = brandingMapper.selectById(code);
        return new BrandingVO(code, t == null ? null : t.getTenantName(),
                b == null ? null : b.getLogoUrl(),
                b == null ? null : b.getPrimaryColor(),
                b == null ? null : b.getAccentColor(),
                b == null ? null : b.getLoginTitle(),
                b == null ? null : b.getLoginSubtitle(),
                b == null || b.getMenuStyle() == null ? "rail" : b.getMenuStyle(),
                b == null || b.getColorMode() == null ? "light" : b.getColorMode(),
                b == null || b.getAllowUserSwitch() == null || b.getAllowUserSwitch() == 1);
    }

    @Transactional(rollbackFor = Exception.class)
    public BrandingVO save(BrandingCmd cmd) {
        String code = TenantContext.get().tenantId();
        TenantBranding b = brandingMapper.selectById(code);
        boolean create = b == null;
        if (create) {
            b = new TenantBranding();
            b.setTenantId(code);
        }
        b.setLogoUrl(blankToNull(cmd.logoUrl()));
        b.setPrimaryColor(blankToNull(cmd.primaryColor()));
        b.setAccentColor(blankToNull(cmd.accentColor()));
        b.setLoginTitle(blankToNull(cmd.loginTitle()));
        b.setLoginSubtitle(blankToNull(cmd.loginSubtitle()));
        b.setMenuStyle(cmd.menuStyle() == null ? "rail" : cmd.menuStyle());
        b.setColorMode(cmd.colorMode() == null ? "light" : cmd.colorMode());
        b.setAllowUserSwitch(cmd.allowUserSwitch() == null || cmd.allowUserSwitch() ? 1 : 0);
        b.setUpdateTime(LocalDateTime.now());
        if (create) {
            brandingMapper.insert(b);
        } else {
            brandingMapper.updateById(b);
        }
        return get();
    }

    private static String blankToNull(String s) {
        return s == null || s.isBlank() ? null : s.trim();
    }
}
''')

io.open(os.path.join(BASE, 'controller/PlatformBrandingController.java'), 'w', encoding='utf-8', newline='').write('''package com.yundao.bp.iam.controller;

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
''')
print('branding backend written')
