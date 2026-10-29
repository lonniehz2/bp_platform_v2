package com.yundao.bp.iam.dto;

/** 登录前可读取的品牌信息（无敏感字段）。 */
public record BrandingVO(
        String tenantCode,
        String tenantName,
        String logoUrl,
        String primaryColor,
        String accentColor,
        String loginTitle,
        String loginSubtitle,
        String menuStyle,
        String colorMode,
        Boolean allowUserSwitch
) {
}
