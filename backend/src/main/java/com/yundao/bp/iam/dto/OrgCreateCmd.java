package com.yundao.bp.iam.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 创建组织请求。
 *
 * @param orgCode   组织编码（租户内唯一）
 * @param orgName   组织名称
 * @param parentId  父组织ID（为空表示顶级）
 * @param orgType   组织类型：DISTRICT / COMMUNITY / COMPANY / DEPARTMENT
 * @param address   地址
 * @param sortNo    排序号
 * @param remark    备注
 */
public record OrgCreateCmd(
        @NotBlank(message = "组织编码不能为空")
        @Size(max = 64, message = "组织编码不能超过 64 字符")
        String orgCode,

        @NotBlank(message = "组织名称不能为空")
        @Size(max = 128, message = "组织名称不能超过 128 字符")
        String orgName,

        Long parentId,

        @NotBlank(message = "组织类型不能为空")
        @Pattern(regexp = "DISTRICT|COMMUNITY|COMPANY|DEPARTMENT|PROPERTY_PROJECT", message = "组织类型不合法")
        String orgType,

        @Size(max = 500, message = "地址不能超过 500 字符")
        String province, String city, String district,
        String street, String community,
        String address,

        Integer sortNo,

        @Size(max = 500, message = "备注不能超过 500 字符")
        String remark
,
        String provinceCode,
        String cityCode,
        String districtCode,
        String streetCode,
        String communityCode
        ) {
}
