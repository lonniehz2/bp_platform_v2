package com.yundao.bp.biz.dto;

import com.yundao.bp.biz.entity.BizContractCohabitant;
import java.time.LocalDateTime;

/**
 * 同住人视图。
 */
public record CohabitantVO(
        Long id,
        Long contractId,
        Long personId,
        String memberName,
        String idCardMask,
        String relation,
        String relationLabel,
        Boolean granted,
        LocalDateTime createTime
) {
    public static CohabitantVO from(BizContractCohabitant e) {
        if (e == null) {
            return null;
        }
        return new CohabitantVO(e.getId(), e.getContractId(), e.getPersonId(),
                e.getMemberName(), e.getIdCardMask(), e.getRelation(),
                relationLabel(e.getRelation()),
                e.getIsGranted() != null && e.getIsGranted() == 1, e.getCreateTime());
    }

    /** 关系中文标签。 */
    public static String relationLabel(String relation) {
        if (relation == null) {
            return "其他";
        }
        return switch (relation) {
            case "SPOUSE" -> "配偶";
            case "CHILD" -> "子女";
            case "PARENT" -> "父母";
            case "SIBLING" -> "兄弟姐妹";
            default -> "其他";
        };
    }
}
