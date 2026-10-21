# -*- coding: utf-8 -*-
"""生成资格判定接入测试"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'

SRC = r'''package com.yundao.bp.biz;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.yundao.bp.biz.dto.ApplicationVO;
import com.yundao.bp.biz.dto.ReviewCmd;
import com.yundao.bp.biz.entity.BizApplication;
import com.yundao.bp.biz.mapper.BizApplicationMapper;
import com.yundao.bp.biz.mapper.BizReviewRecordMapper;
import com.yundao.bp.biz.service.impl.ApplicationServiceImpl;
import com.yundao.bp.common.api.ErrorCode;
import com.yundao.bp.common.exception.BizException;
import com.yundao.bp.common.id.SnowflakeIdGenerator;
import com.yundao.bp.common.tenant.TenantContext;
import com.yundao.bp.common.tenant.TenantInfo;
import com.yundao.bp.person.entity.PersonGuaranteeProfile;
import com.yundao.bp.person.service.GuaranteeProfileService;
import java.time.LocalDate;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * 资格判定接入测试。
 *
 * <p><b>为什么必须测</b>：审核员手工勾「通过」而不看档案，是最容易发生的
 * 审核流于形式。本测试证明：档案里的收入档位、家庭人口、人才认定、
 * 名下房产都会**真的阻止审核通过**。
 */
@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class ApplicationQualifyGateTest {

    @Mock
    private BizApplicationMapper appMapper;
    @Mock
    private BizReviewRecordMapper reviewMapper;
    @Mock
    private GuaranteeProfileService profileService;

    private ApplicationServiceImpl service;

    @BeforeEach
    void setUp() {
        service = new ApplicationServiceImpl(appMapper, reviewMapper,
                new SnowflakeIdGenerator(1, 1));
        TenantContext.set(TenantInfo.of("350600", 1001L));
        when(appMapper.updateById(any(BizApplication.class))).thenReturn(1);
        when(reviewMapper.insert(any())).thenReturn(1);
        when(reviewMapper.selectCount(any())).thenReturn(0L);
        ReflectionTestUtils.setField(service, "guaranteeProfileService", profileService);
    }

    @AfterEach
    void tearDown() {
        TenantContext.clear();
    }

    /** 处于审核中的申请单。 */
    private void givenInReviewApp(int familySize, String securityType) {
        BizApplication e = new BizApplication();
        e.setId(100L);
        e.setTenantId("350600");
        e.setPersonId(4001L);
        e.setOrgId(1L);
        e.setSecurityType(securityType);
        e.setFamilySize(familySize);
        e.setApplicationStatus("DEPT_REVIEW");
        e.setIsDeleted(0);
        when(appMapper.selectById(100L)).thenReturn(e);
    }

    private static PersonGuaranteeProfile profile(String level, int size, String talent,
                                                  LocalDate talentValid, Integer hasHouse,
                                                  String remark) {
        PersonGuaranteeProfile p = new PersonGuaranteeProfile();
        p.setId(1L);
        p.setPersonId(4001L);
        p.setIncomeLevel(level);
        p.setFamilySize(size);
        p.setTalentLevel(talent);
        p.setTalentValidTo(talentValid);
        p.setHasHouse(hasHouse);
        p.setHouseCount(hasHouse == null || hasHouse == 0 ? 0 : 1);
        p.setRemark(remark);
        p.setProfileStatus("APPLICANT");
        return p;
    }

    private static ReviewCmd pass() {
        return new ReviewCmd("DEPT", null, "PASS", "同意", null, null, null);
    }

    private static ReviewCmd reject() {
        return new ReviewCmd("DEPT", null, "REJECT", "不符合", null, null, "收入超标");
    }

    // ==================== ⭐⭐ 收入档位 ====================

    @Test
    @DisplayName("⭐⭐ 收入档位为 NORMAL（超标）→ 审核通过被拒")
    void rejectNormalIncome() {
        givenInReviewApp(3, "PUBLIC");
        when(profileService.getByPerson(any())).thenReturn(
                profile("NORMAL", 3, null, null, 0, null));

        BizException ex = assertThrows(BizException.class,
                () -> service.review(100L, pass(), 1001L, "审核员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("超过中低收入线"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 收入档位 LOW/LOW_INCOME/MIDDLE_LOW → 允许通过")
    void allowQualifiedIncome() {
        for (String level : new String[]{"LOW", "LOW_INCOME", "MIDDLE_LOW"}) {
            givenInReviewApp(3, "PUBLIC");
            when(profileService.getByPerson(any())).thenReturn(
                    profile(level, 3, null, null, 0, null));
            ApplicationVO vo = service.review(100L, pass(), 1001L, "审核员");
            assertEquals("QUALIFIED", vo.applicationStatus(), level + " 应通过");
        }
    }

    @Test
    @DisplayName("⭐⭐ 无保障档案 → 不能通过审核（缺判定依据）")
    void rejectNoProfile() {
        givenInReviewApp(3, "PUBLIC");
        when(profileService.getByPerson(any())).thenThrow(BizException.notFound("保障档案"));

        BizException ex = assertThrows(BizException.class,
                () -> service.review(100L, pass(), 1001L, "审核员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("尚无保障对象档案"), ex.getMessage());
    }

    // ==================== ⭐⭐ 家庭人口一致性 ====================

    @Test
    @DisplayName("⭐⭐ 申报 3 人但档案 1 人 → 涉嫌申报不实，拒绝")
    void rejectFamilySizeMismatch() {
        givenInReviewApp(3, "PUBLIC");
        when(profileService.getByPerson(any())).thenReturn(
                profile("LOW", 1, null, null, 0, null));

        BizException ex = assertThrows(BizException.class,
                () -> service.review(100L, pass(), 1001L, "审核员"));
        assertEquals(ErrorCode.STATE_CONFLICT, ex.errorCode());
        assertTrue(ex.getMessage().contains("不一致"), ex.getMessage());
        assertTrue(ex.getMessage().contains("3"), ex.getMessage());
        assertTrue(ex.getMessage().contains("1"), ex.getMessage());
    }

    @Test
    @DisplayName("人口一致 → 允许通过")
    void allowSameSize() {
        givenInReviewApp(3, "PUBLIC");
        when(profileService.getByPerson(any())).thenReturn(
                profile("LOW", 3, null, null, 0, null));
        assertEquals("QUALIFIED",
                service.review(100L, pass(), 1001L, "审核员").applicationStatus());
    }

    // ==================== ⭐ 人才公寓 ====================

    @Test
    @DisplayName("⭐⭐ 人才公寓但档案无人才层次 → 拒绝")
    void rejectTalentNoLevel() {
        givenInReviewApp(2, "TALENT");
        when(profileService.getByPerson(any())).thenReturn(
                profile("LOW", 2, null, null, 0, null));

        BizException ex = assertThrows(BizException.class,
                () -> service.review(100L, pass(), 1001L, "审核员"));
        assertTrue(ex.getMessage().contains("人才认定"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐⭐ 人才认定已过期 → 拒绝")
    void rejectTalentExpired() {
        givenInReviewApp(2, "TALENT");
        when(profileService.getByPerson(any())).thenReturn(
                profile("LOW", 2, "B", LocalDate.now().minusDays(30), 0, null));

        BizException ex = assertThrows(BizException.class,
                () -> service.review(100L, pass(), 1001L, "审核员"));
        assertTrue(ex.getMessage().contains("已过期"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 人才认定有效 → 允许通过")
    void allowTalentValid() {
        givenInReviewApp(2, "TALENT");
        when(profileService.getByPerson(any())).thenReturn(
                profile("LOW", 2, "B", LocalDate.now().plusYears(1), 0, null));
        assertEquals("QUALIFIED",
                service.review(100L, pass(), 1001L, "审核员").applicationStatus());
    }

    // ==================== 名下有房 ====================

    @Test
    @DisplayName("⭐ 名下有房且无例外说明 → 拒绝（要求备注依据）")
    void rejectHasHouseNoRemark() {
        givenInReviewApp(2, "PUBLIC");
        when(profileService.getByPerson(any())).thenReturn(
                profile("LOW", 2, null, null, 1, null));

        BizException ex = assertThrows(BizException.class,
                () -> service.review(100L, pass(), 1001L, "审核员"));
        assertTrue(ex.getMessage().contains("备注"), ex.getMessage());
    }

    @Test
    @DisplayName("⭐ 名下有房但备注了例外依据 → 允许通过")
    void allowHasHouseWithRemark() {
        givenInReviewApp(2, "PUBLIC");
        when(profileService.getByPerson(any())).thenReturn(
                profile("LOW", 2, null, null, 1, "离婚析产后归对方，现无自有住房"));
        assertEquals("QUALIFIED",
                service.review(100L, pass(), 1001L, "审核员").applicationStatus());
    }

    // ==================== 只影响 PASS ====================

    @Test
    @DisplayName("⭐⭐ 驳回/补件不受资格判定影响（否则无法退回）")
    void rejectDoesNotRunGate() {
        givenInReviewApp(3, "PUBLIC");
        // 档案缺失也不应影响驳回
        when(profileService.getByPerson(any())).thenThrow(BizException.notFound("保障档案"));
        ApplicationVO vo = service.review(100L, reject(), 1001L, "审核员");
        assertEquals("REJECTED", vo.applicationStatus());
    }

    @Test
    @DisplayName("档案服务未部署时放行（灰度环境不阻断）")
    void allowWhenServiceMissing() {
        ReflectionTestUtils.setField(service, "guaranteeProfileService", null);
        givenInReviewApp(3, "PUBLIC");
        assertEquals("QUALIFIED",
                service.review(100L, pass(), 1001L, "审核员").applicationStatus());
    }
}
'''

p = os.path.join(BASE, 'ApplicationQualifyGateTest.java')
os.makedirs(BASE, exist_ok=True)
io.open(p, 'w', encoding='utf-8').write(SRC)
print('  + biz/ApplicationQualifyGateTest.java（%d 行）' % SRC.count('\n'))
