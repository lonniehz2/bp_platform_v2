# -*- coding: utf-8 -*-
import io
import os

BASE = r'..\backend\src\main\java\com\yundao\bp\iam\dto'
os.makedirs(BASE, exist_ok=True)

files = {}

files['OperatorLoginCmd.java'] = '''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;

public record OperatorLoginCmd(
        @NotBlank(message = "账号不能为空") String username,
        @NotBlank(message = "密码不能为空") String password
) {
}
'''

files['OperatorLoginVO.java'] = '''package com.yundao.bp.iam.dto;

public record OperatorLoginVO(
        String token,
        Long operatorId,
        String username,
        String realName,
        Boolean mustChangePassword
) {
}
'''

files['OperatorChangePwdCmd.java'] = '''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record OperatorChangePwdCmd(
        @NotBlank(message = "原密码不能为空") String oldPassword,
        @NotBlank(message = "新密码不能为空")
        @Size(min = 10, max = 64, message = "新密码至少 10 位") String newPassword
) {
}
'''

files['PlatformVO.java'] = '''package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

public record PlatformVO(
        Long id,
        String tenantCode,
        String tenantName,
        String tenantType,
        String regionCode,
        String status,
        String contactName,
        String contactPhone,
        String businessTypeCode,
        Long adminCount,
        LocalDateTime createTime,
        LocalDateTime archiveTime
) {
}
'''

files['PlatformCreateCmd.java'] = '''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record PlatformCreateCmd(
        @NotBlank(message = "平台名称不能为空")
        @Size(max = 100, message = "平台名称不能超过 100 字") String tenantName,

        @NotBlank(message = "行政区划不能为空")
        @Size(max = 20, message = "行政区划编码过长") String regionCode,

        @Pattern(regexp = "GOV|ORG|ENTERPRISE", message = "平台类型不合法") String tenantType,

        String contactName,
        String contactPhone,

        @NotBlank(message = "管理员账号不能为空")
        @Size(max = 64) String adminUsername,

        @Size(max = 64) String adminRealName
) {
}
'''

files['PlatformCreateResult.java'] = '''package com.yundao.bp.iam.dto;

/** 创建平台结果：初始密码仅本次返回。 */
public record PlatformCreateResult(
        PlatformVO platform,
        String adminUsername,
        String initialPassword
) {
}
'''

files['PlatformUpdateCmd.java'] = '''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record PlatformUpdateCmd(
        @NotBlank(message = "平台名称不能为空")
        @Size(max = 100) String tenantName,

        @Pattern(regexp = "GOV|ORG|ENTERPRISE", message = "平台类型不合法") String tenantType,

        @Size(max = 20) String regionCode,

        String contactName,
        String contactPhone
) {
}
'''

files['PlatformAdminVO.java'] = '''package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

public record PlatformAdminVO(
        Long userId,
        String username,
        String realName,
        String phone,
        String status,
        Boolean mustChangePassword,
        LocalDateTime lastLoginTime,
        LocalDateTime lockedUntil
) {
}
'''

files['PlatformAdminCreateCmd.java'] = '''package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record PlatformAdminCreateCmd(
        @NotBlank(message = "管理员账号不能为空")
        @Size(max = 64) String username,

        @Size(max = 64) String realName,
        @Size(max = 32) String phone,
        @Size(max = 128) String email
) {
}
'''

files['PlatformAdminResetVO.java'] = '''package com.yundao.bp.iam.dto;

/** 重置/新建管理员结果：初始密码仅本次返回。 */
public record PlatformAdminResetVO(
        Long userId,
        String username,
        String initialPassword,
        Boolean mustChangePassword
) {
}
'''

files['PlatformAuditVO.java'] = '''package com.yundao.bp.iam.dto;

import java.time.LocalDateTime;

public record PlatformAuditVO(
        Long id,
        String operatorName,
        String platformCode,
        String action,
        String detail,
        String ip,
        LocalDateTime createTime
) {
}
'''

files['BrandingVO.java'] = '''package com.yundao.bp.iam.dto;

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
'''

for name, code in files.items():
    io.open(os.path.join(BASE, name), 'w', encoding='utf-8', newline='').write(code)
print('dtos', len(files))
