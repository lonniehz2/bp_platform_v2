# -*- coding: utf-8 -*-
"""生成保障档案服务 + 实名留痕服务 + 控制器"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
F = {}

F['person/service/GuaranteeProfileService.java'] = '''package com.yundao.bp.person.service;

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
                                            String profileStatus);

    /** 建档入参。 */
    record ProfileCmd(Long personId, String securityType, Integer familySize,
                      String familyType, BigDecimal monthlyIncome,
                      BigDecimal assetDeclare, Integer hasHouse, Integer houseCount,
                      Integer hasVehicle, String socialSecurity, String priorityFlags,
                      String talentLevel, String talentCertNo) {
    }
}
'''

F['person/service/impl/GuaranteeProfileServiceImpl.java'] = '''package com.yundao.bp.person.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.api.PageResult;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.person.constant.IncomeLevel;
import com.yundao.bp.person.entity.PersonGuaranteeProfile;
import com.yundao.bp.person.mapper.PersonGuaranteeProfileMapper;
import com.yundao.bp.person.service.GuaranteeProfileService;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * 保障对象档案实现。
 */
@Service
public class GuaranteeProfileServiceImpl implements GuaranteeProfileService {

    private static final Logger log =
            LoggerFactory.getLogger(GuaranteeProfileServiceImpl.class);

    private final PersonGuaranteeProfileMapper mapper;
    private final SnowflakeIdGenerator idGen;

    public GuaranteeProfileServiceImpl(PersonGuaranteeProfileMapper mapper,
                                       SnowflakeIdGenerator idGen) {
        this.mapper = mapper;
        this.idGen = idGen;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PersonGuaranteeProfile save(ProfileCmd cmd) {
        if (cmd.personId() == null) {
            throw BizException.paramInvalid("人员ID不能为空");
        }
        if (cmd.securityType() == null || cmd.securityType().isBlank()) {
            throw BizException.paramInvalid("保障类型不能为空");
        }
        // 家庭人口必须 ≥1：0 人会导致按人计费/补贴算成 0
        int familySize = cmd.familySize() == null ? 1 : cmd.familySize();
        if (familySize <= 0) {
            throw BizException.paramInvalid("家庭人口必须大于 0");
        }
        if (cmd.monthlyIncome() != null
                && cmd.monthlyIncome().compareTo(BigDecimal.ZERO) < 0) {
            throw BizException.paramInvalid("家庭月收入不能为负");
        }
        LocalDateTime now = LocalDateTime.now();
        PersonGuaranteeProfile exist = findByPerson(cmd.personId());
        if (exist == null) {
            PersonGuaranteeProfile e = new PersonGuaranteeProfile();
            e.setId(idGen.nextId());
            e.setTenantId(TenantContext.tenantId());
            e.setPersonId(cmd.personId());
            fill(e, cmd, familySize);
            e.setProfileStatus("APPLICANT");
            e.setFirstApplyDate(LocalDate.now());
            e.setIsDeleted(0);
            e.setCreateTime(now);
            e.setUpdateTime(now);
            mapper.insert(e);
            log.info("保障档案已建立：人员 {}（{}）", cmd.personId(), cmd.securityType());
            return e;
        }
        fill(exist, cmd, familySize);
        exist.setUpdateTime(now);
        mapper.updateById(exist);
        return exist;
    }

    private static void fill(PersonGuaranteeProfile e, ProfileCmd cmd, int familySize) {
        e.setSecurityType(cmd.securityType());
        e.setFamilySize(familySize);
        e.setFamilyType(cmd.familyType());
        e.setMonthlyIncome(cmd.monthlyIncome());
        e.setAssetDeclare(cmd.assetDeclare());
        e.setHasHouse(cmd.hasHouse() == null ? 0 : cmd.hasHouse());
        e.setHouseCount(cmd.houseCount() == null ? 0 : cmd.houseCount());
        e.setHasVehicle(cmd.hasVehicle() == null ? 0 : cmd.hasVehicle());
        e.setSocialSecurity(cmd.socialSecurity());
        e.setPriorityFlags(cmd.priorityFlags());
        e.setTalentLevel(cmd.talentLevel());
        e.setTalentCertNo(cmd.talentCertNo());
    }

    @Override
    public PersonGuaranteeProfile getByPerson(Long personId) {
        PersonGuaranteeProfile e = findByPerson(personId);
        if (e == null) {
            throw BizException.notFound("保障档案");
        }
        return e;
    }

    private PersonGuaranteeProfile findByPerson(Long personId) {
        return mapper.selectOne(new LambdaQueryWrapper<PersonGuaranteeProfile>()
                .eq(PersonGuaranteeProfile::getPersonId, personId)
                .last("LIMIT 1"));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> recalcIncome(Long personId, BigDecimal lowLine,
                                            BigDecimal lowIncomeLine,
                                            BigDecimal middleLowLine) {
        PersonGuaranteeProfile e = getByPerson(personId);
        IncomeLevel before = e.getIncomeLevel() == null ? null
                : IncomeLevel.valueOf(e.getIncomeLevel());
        IncomeLevel after = IncomeLevel.of(e.getMonthlyIncome(), e.getFamilySize(),
                lowLine, lowIncomeLine, middleLowLine);
        e.setIncomeLevel(after.name());
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);

        BigDecimal perCapita = null;
        if (e.getMonthlyIncome() != null) {
            int size = e.getFamilySize() == null || e.getFamilySize() <= 0
                    ? 1 : e.getFamilySize();
            perCapita = e.getMonthlyIncome().divide(BigDecimal.valueOf(size), 2,
                    RoundingMode.HALF_UP);
        }
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("personId", personId);
        m.put("monthlyIncome", e.getMonthlyIncome());
        m.put("familySize", e.getFamilySize());
        m.put("perCapitaIncome", perCapita);
        m.put("incomeLevelBefore", before == null ? null : before.name());
        m.put("incomeLevelAfter", after.name());
        m.put("incomeLevelLabel", after.label());
        m.put("changed", before != after);
        log.info("收入档位重算：人员 {} 人均 {} → {}（{}）", personId, perCapita,
                after.name(), after.label());
        return m;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PersonGuaranteeProfile qualify(Long personId, Integer qualifyYears) {
        PersonGuaranteeProfile e = getByPerson(personId);
        if ("EXITED".equals(e.getProfileStatus())) {
            throw BizException.stateConflict("该档案已退出保障，不可直接通过审核");
        }
        int years = qualifyYears == null || qualifyYears <= 0 ? 1 : qualifyYears;
        LocalDate today = LocalDate.now();
        e.setProfileStatus("QUALIFIED");
        e.setQualifyDate(today);
        e.setQualifyExpire(today.plusYears(years));
        e.setLastReviewDate(today);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("资格审核通过：人员 {}，有效期至 {}", personId, e.getQualifyExpire());
        return e;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PersonGuaranteeProfile exit(Long personId, LocalDate exitDate, String reason) {
        PersonGuaranteeProfile e = getByPerson(personId);
        if ("EXITED".equals(e.getProfileStatus())) {
            throw BizException.stateConflict("该档案已退出，不可重复退出");
        }
        e.setProfileStatus("EXITED");
        e.setExitDate(exitDate == null ? LocalDate.now() : exitDate);
        e.setExitReason(reason);
        e.setUpdateTime(LocalDateTime.now());
        mapper.updateById(e);
        log.info("保障档案已退出：人员 {}（{}）", personId, reason);
        return e;
    }

    @Override
    public List<Map<String, Object>> expiring(int withinDays) {
        int days = withinDays <= 0 ? 30 : withinDays;
        LocalDate limit = LocalDate.now().plusDays(days);
        List<PersonGuaranteeProfile> list = mapper.selectList(
                new LambdaQueryWrapper<PersonGuaranteeProfile>()
                        .in(PersonGuaranteeProfile::getProfileStatus,
                                List.of("QUALIFIED", "IN_RESIDENCE"))
                        .isNotNull(PersonGuaranteeProfile::getQualifyExpire)
                        .le(PersonGuaranteeProfile::getQualifyExpire, limit)
                        .orderByAsc(PersonGuaranteeProfile::getQualifyExpire));
        LocalDate today = LocalDate.now();
        List<Map<String, Object>> out = new ArrayList<>();
        for (PersonGuaranteeProfile e : list) {
            long left = ChronoUnit.DAYS.between(today, e.getQualifyExpire());
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("personId", e.getPersonId());
            m.put("securityType", e.getSecurityType());
            m.put("profileStatus", e.getProfileStatus());
            m.put("qualifyExpire", e.getQualifyExpire());
            m.put("daysLeft", left);
            m.put("expired", left < 0);
            m.put("advice", left < 0
                    ? "资格已过期 " + (-left) + " 天，应立即停发补贴并启动退出"
                    : "还有 " + left + " 天到期，请安排年度复核");
            out.add(m);
        }
        return out;
    }

    @Override
    public PageResult<PersonGuaranteeProfile> page(long pageNum, long pageSize,
                                                   String securityType, String incomeLevel,
                                                   String profileStatus) {
        LambdaQueryWrapper<PersonGuaranteeProfile> qw =
                new LambdaQueryWrapper<PersonGuaranteeProfile>()
                        .eq(securityType != null && !securityType.isBlank(),
                                PersonGuaranteeProfile::getSecurityType, securityType)
                        .eq(incomeLevel != null && !incomeLevel.isBlank(),
                                PersonGuaranteeProfile::getIncomeLevel, incomeLevel)
                        .eq(profileStatus != null && !profileStatus.isBlank(),
                                PersonGuaranteeProfile::getProfileStatus, profileStatus)
                        .orderByDesc(PersonGuaranteeProfile::getId);
        IPage<PersonGuaranteeProfile> page = mapper.selectPage(
                new Page<>(pageNum, pageSize), qw);
        return PageResult.of(page.getTotal(), pageNum, pageSize, page.getRecords());
    }
}
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件' % count)
