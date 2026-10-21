package com.yundao.bp.person.service;

import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.person.entity.PersonGuaranteeProfile;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 保障对象档案服务。
 *
 * <p>承载保障专有属性：家庭人口、收入档位、房产车辆、优先条件、人才层次、
 * 资格有效期。这些字段是<b>资格审核与年度复核的直接依据</b>，
 * 不适合塞进通用人员表。
 */
public interface GuaranteeProfileService {

    /** 建档或更新（同一人员唯一档案）。 */
    PersonGuaranteeProfile save(ProfileCmd cmd);

    PersonGuaranteeProfile getByPerson(Long personId);

    /** ⭐ 重算收入档位（阈值来自系统参数，支持分地区）。 */
    Map<String, Object> recalcIncome(Long personId, BigDecimal lowLine,
                                     BigDecimal lowIncomeLine, BigDecimal middleLowLine);

    /** 资格审核通过：置 QUALIFIED 并写资格有效期。 */
    PersonGuaranteeProfile qualify(Long personId, Integer qualifyYears);

    /** 退出保障：置 EXITED 并记录原因。 */
    PersonGuaranteeProfile exit(Long personId, LocalDate exitDate, String reason);

    /** ⭐ 资格到期预警（年审依据）：返回即将到期/已过期档案。 */
    List<Map<String, Object>> expiring(int withinDays);

    PageResult<PersonGuaranteeProfile> page(long pageNum, long pageSize,
                                            String securityType, String incomeLevel,
                                            String profileStatus, String keyword, Long personId);

    /** 建档入参。 */
    record ProfileCmd(Long personId, String securityType, Integer familySize,
                      String familyType, BigDecimal monthlyIncome,
                      BigDecimal assetDeclare, Integer hasHouse, Integer houseCount,
                      Integer hasVehicle, String socialSecurity, String priorityFlags,
                      String talentLevel, String talentCertNo) {
    }
}
