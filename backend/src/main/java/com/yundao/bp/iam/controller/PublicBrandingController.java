package com.yundao.bp.iam.controller;

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
