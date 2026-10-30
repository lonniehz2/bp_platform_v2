package com.yundao.bp.iam.dto;

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
