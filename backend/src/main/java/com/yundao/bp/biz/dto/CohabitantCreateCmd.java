package com.yundao.bp.biz.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/**
 * 添加合同同住人。
 *
 * <p>身份证只存<b>脱敏串</b>（如 110101********1234），不存明文。
 */
public record CohabitantCreateCmd(

        Long personId,

        @NotBlank(message = "同住人姓名不能为空")
        @Size(max = 64, message = "姓名不能超过 64 字符")
        String memberName,

        /** 身份证脱敏串（前端脱敏后传，或不传） */
        String idCardMask,

        /** 与承租人关系：SPOUSE 配偶 / CHILD 子女 / PARENT 父母 / SIBLING 兄弟姐妹 / OTHER 其他 */
        String relation,

        Integer isGranted
) {
}
