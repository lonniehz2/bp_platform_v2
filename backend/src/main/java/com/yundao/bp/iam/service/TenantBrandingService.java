package com.yundao.bp.iam.service;

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
