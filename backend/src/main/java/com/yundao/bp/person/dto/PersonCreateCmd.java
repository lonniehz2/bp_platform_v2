package com.yundao.bp.person.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 创建人员。
 *
 * <p>敏感字段传<b>明文</b>，由服务层加密 + 哈希 + 脱敏后落库。
 *
 * @param personName   姓名
 * @param idCard       身份证号（明文，18 位或 15 位）
 * @param phone        手机号（明文）
 * @param orgId        归属组织
 * @param householdType URBAN / RURAL / OTHER
 * @param maritalStatus SINGLE / MARRIED / DIVORCED / WIDOWED
 */
public record PersonCreateCmd(
        @NotBlank(message = "姓名不能为空")
        @Size(max = 64, message = "姓名不能超过 64 字符")
        String personName,

        @Size(max = 20, message = "身份证号格式不正确")
        String idCard,

        @Size(max = 20, message = "手机号格式不正确")
        String phone,

        Long orgId,

        @Pattern(regexp = "^$|URBAN|RURAL|OTHER", message = "户籍类型不合法")
        String householdType,

        @Pattern(regexp = "^$|SINGLE|MARRIED|DIVORCED|WIDOWED", message = "婚姻状况不合法")
        String maritalStatus,

        @Size(max = 30, message = "学历不能超过 30 字符")
        String education,

        @Size(max = 128, message = "工作单位不能超过 128 字符")
        String employer,

        @Size(max = 500, message = "备注不能超过 500 字符")
        String remark
) {
}
