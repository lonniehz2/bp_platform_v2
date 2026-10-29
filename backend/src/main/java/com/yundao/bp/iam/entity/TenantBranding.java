package com.yundao.bp.iam.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import java.time.LocalDateTime;
import lombok.Data;

/** 平台品牌与主题。 */
@Data
@TableName("bp_iam_tenant_branding")
public class TenantBranding {
    @TableId(type = IdType.INPUT)
    private String tenantId;
    private String logoUrl;
    private String primaryColor;
    private String accentColor;
    private String loginTitle;
    private String loginSubtitle;
    private String menuStyle;
    private String colorMode;
    private Integer allowUserSwitch;
    private LocalDateTime updateTime;
}
