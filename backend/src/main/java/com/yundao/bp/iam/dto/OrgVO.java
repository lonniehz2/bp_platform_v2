package com.yundao.bp.iam.dto;

import com.yundao.bp.iam.entity.IamOrg;
import java.time.LocalDateTime;

/**
 * 组织视图对象。
 *
 * <p>注意：{@code id} 为 {@code Long}，由 {@code JacksonConfig} 统一序列化为字符串，
 * 避免 JS 精度丢失。
 */
public record OrgVO(
        Long id,
        String orgCode,
        String orgName,
        Long parentId,
        String orgPath,
        Integer orgLevel,
        String orgType,
        String province, String city, String district,
        String street, String community,
        String address,
        Integer sortNo,
        String status,
        String remark,
        LocalDateTime createTime
) {
    public static OrgVO from(IamOrg e) {
        if (e == null) {
            return null;
        }
        return new OrgVO(e.getId(), e.getOrgCode(), e.getOrgName(), e.getParentId(),
                e.getOrgPath(), e.getOrgLevel(), e.getOrgType(),
                e.getProvince(), e.getCity(), e.getDistrict(), e.getStreet(),
                e.getCommunity(), e.getAddress(),
                e.getSortNo(), e.getStatus(), e.getRemark(), e.getCreateTime());
    }
}
