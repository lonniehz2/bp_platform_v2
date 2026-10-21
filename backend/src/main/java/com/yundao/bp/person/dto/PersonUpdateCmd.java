package com.yundao.bp.person.dto;

import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 人员信息修改入参。
 *
 * <p>不含身份证号：证件号是人员唯一标识的关键字段，修改需走专门流程，
 * 避免误改导致历史业务数据对不上。</p>
 */
public record PersonUpdateCmd(
        @Size(max = 64, message = "姓名不能超过 64 字符")
        String personName,
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
        String remark) {
}
