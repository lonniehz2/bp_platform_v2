package com.yundao.bp.person.dto;

import com.yundao.bp.person.entity.Person;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 人员视图（<b>只返回脱敏数据</b>）。
 *
 * <p>⚠️ 安全约束：本 VO <b>绝不包含</b> {@code id_card} / {@code phone} 明文或密文，
 * 只返回 {@code idCardMask} / {@code phoneMask} 用于展示。
 */
public record PersonVO(
        Long id,
        String personCode,
        String personName,
        String realName,
        /** 脱敏手机号，如 138****8000 */
        String phoneMask,
        /** 脱敏身份证，如 330106********1219 */
        String idCardMask,
        String gender,
        LocalDate birthday,
        String householdType,
        String maritalStatus,
        String education,
        String employer,
        Long orgId,
        String verifyStatus,
        String personStatus,
        LocalDateTime createTime
) {
    public static PersonVO from(Person p) {
        if (p == null) {
            return null;
        }
        String phoneMask = null;
        if (p.getPhone() != null && p.getPhone().length() >= 8) {
            String s = p.getPhone();
            phoneMask = s.substring(0, 3) + "****" + s.substring(s.length() - 4);
        }
        return new PersonVO(p.getId(), p.getPersonCode(), p.getPersonName(), p.getRealName(),
                phoneMask, p.getIdCardMask(), p.getGender(), p.getBirthday(),
                p.getHouseholdType(), p.getMaritalStatus(), p.getEducation(), p.getEmployer(),
                p.getOrgId(), p.getVerifyStatus(), p.getPersonStatus(), p.getCreateTime());
    }
}
