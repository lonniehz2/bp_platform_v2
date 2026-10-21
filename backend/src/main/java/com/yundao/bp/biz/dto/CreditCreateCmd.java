package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 记入信用惩戒。
 *
 * @param banYears 限制申请年限；{@code sanctionType=BAN_APPLY} 时必填（政策常见 5 年）
 */
public record CreditCreateCmd(

        @NotNull(message = "人员不能为空")
        Long personId,

        @Pattern(regexp = "^$|EXIT|CONTRACT|APPLICATION", message = "业务类型不合法")
        String bizType,
        Long bizId,

        @NotBlank(message = "违规类型不能为空")
        @Pattern(regexp = "FALSE_INFO|SUBLEASE|STRUCTURE|CHANGE_USE|VACANT|ILLEGAL|ARREARS|OTHER",
                message = "违规类型不合法")
        String violationType,

        @Size(max = 2000, message = "违规描述不能超过 2000 字")
        String violationDesc,

        String evidenceUrl,

        @NotBlank(message = "惩戒措施不能为空")
        @Pattern(regexp = "TERMINATE|BAN_APPLY|CREDIT_PLATFORM|FINE|OTHER",
                message = "惩戒措施不合法")
        String sanctionType,

        Integer banYears,

        Long decideOrgId,
        Long decideUserId,
        String legalDocNo,

        /** 是否推送信用平台（推送状态初始为 PENDING） */
        Boolean pushToPlatform,
        String pushPlatform,

        String remark
) {
}
